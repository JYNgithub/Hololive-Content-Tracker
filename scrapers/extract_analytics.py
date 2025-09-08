import os
import re
import html
import iso8601
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build

############################################
# Configuration
############################################

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

load_dotenv()
API_KEY = os.getenv("YT_API_KEY")
DB_URL = os.getenv("DB_URL")
ENGINE = create_engine(DB_URL)
df = pd.read_csv("./data/intermediate.csv")
CHANNEL_HANDLES = df['Handle'].dropna().unique().tolist()
EXTRACT_PERIOD = datetime.now(timezone.utc) - timedelta(days=7)  
DATA_PATH = './data/talent_analytics.csv'

############################################
# Utility Functions
############################################

def initialize_client():
    """
    Build YouTube API client
    Requires Youtube Data API Key
    """
    
    logging.info("Initializing YouTube API client...")
    client = build('youtube', 'v3', developerKey=API_KEY)
    return client

def extract_channel_id(client, handle):
    """
    Get channel ID from handle
    
    Args:
        client: Youtube client from initialize_client()
        handle: Youtube channel handle to extract data
    """
    try: 
        channel_res = client.channels().list(
            part="id,contentDetails",
            forHandle=handle
        ).execute()
        if not channel_res['items']:
            raise ValueError(f"Channel not found: {handle}")
        channel_id = channel_res['items'][0]['id']
    except Exception as e:
        logging.error(e)

    return channel_id

# not used, remove when dual API implemented
def extract_analytics_minquota(client, channel_id, handle):
    data = []
    stale_pages = 0
    MAX_STALE_PAGES = 1

    try:
        uploads_playlist_id = client.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        next_page = None
        page_count = 0
        logging.info(f"[{handle}] Starting to scan playlist for recent live broadcasts...")

        while True:
            page_count += 1
            if page_count == 1:
                logging.info(f"[{handle}] Checking first page of uploads...")
            else:
                logging.info(f"[{handle}] Checking page {page_count}...")

            playlist_items = client.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page
            ).execute()

            video_ids = [item['contentDetails']['videoId'] for item in playlist_items['items']]
            videos_res = client.videos().list(
                part="snippet,liveStreamingDetails,statistics",
                id=",".join(video_ids)
            ).execute()

            recent_found = False
            for video_data in videos_res.get('items', []):
                live_info = video_data.get('liveStreamingDetails')
                live_flag = video_data['snippet'].get('liveBroadcastContent', 'none')

                # Skip if not live-related
                if live_flag not in ['live', 'upcoming', 'completed']:
                    continue

                # Skip if no liveStreamingDetails or no actualStartTime
                actual_start_str = live_info.get('actualStartTime') if live_info else None
                if not actual_start_str:
                    continue

                actual_start = iso8601.parse_date(actual_start_str)
                if actual_start < EXTRACT_PERIOD:
                    continue

                recent_found = True
                start = actual_start
                end = iso8601.parse_date(live_info.get('actualEndTime', datetime.now(timezone.utc).isoformat()))
                duration_hours = round((end - start).total_seconds() / 3600, 2)

                data.append({
                    'handle': handle,
                    'video_id': video_data['id'],
                    'title': video_data['snippet']['title'],
                    'published_at': video_data['snippet']['publishedAt'],
                    'live_broadcast_content': live_flag,
                    'actual_start_time': live_info.get('actualStartTime'),
                    'actual_end_time': live_info.get('actualEndTime'),
                    'scheduled_start_time': live_info.get('scheduledStartTime'),
                    'duration_hours': duration_hours,
                    'view_count': video_data.get('statistics', {}).get('viewCount', 0),
                    'like_count': video_data.get('statistics', {}).get('likeCount', 0),
                    'comment_count': video_data.get('statistics', {}).get('commentCount', 0)
                })

            if not recent_found:
                stale_pages += 1
                logging.info(f"[{handle}] No recent live broadcasts on page {page_count}. Stale count: {stale_pages}")
                if stale_pages >= MAX_STALE_PAGES:
                    logging.info(f"[{handle}] Reached {MAX_STALE_PAGES} stale pages. Stopping early.")
                    break
            else:
                stale_pages = 0

            next_page = playlist_items.get('nextPageToken')
            if not next_page:
                break

        logging.info(f"[{handle}] Finished. Found {len(data)} recent live broadcasts.")

    except Exception as e:
        logging.warning(f"[{handle}] Extraction failed: {e}")

    return data

def extract_analytics(client, channel_id, handle):
    """
    Extract analytics one channel at a time
    
    Args:
        client: Youtube client from initialize_client()
        channel_id: Youtube Channel ID to extract from extract_channel_id()
    """
    
    data = []
    next_page = None
    
    # Search for completed/archived live broadcasts
    try:
        while True:
            search_res = client.search().list(
                part="snippet",
                channelId=channel_id,
                eventType="completed",  
                type="video",
                order="date",
                publishedAfter=EXTRACT_PERIOD.isoformat(),
                maxResults=50,
                pageToken=next_page
            ).execute()
            
            if not search_res.get('items'):
                break
            
            video_ids = [item['id']['videoId'] for item in search_res['items']]
            videos_res = client.videos().list(
                part="snippet,liveStreamingDetails,contentDetails,status,statistics",
                id=','.join(video_ids)
            ).execute()
            
            for video_data in videos_res['items']:
                # Check if it has live streaming details
                live_info = video_data.get('liveStreamingDetails', {})
                if not live_info:
                    continue
                    
                # Must have actual start time to be a completed live broadcast
                if 'actualStartTime' not in live_info:
                    continue
                    
                vid_id = video_data['id']
                pub_date_str = video_data['snippet']['publishedAt']
                pub_date = iso8601.parse_date(pub_date_str)
                
                # Date filter
                if pub_date < EXTRACT_PERIOD:
                    continue
                
                # Calculate duration if available
                duration_hours = None
                if 'actualEndTime' in live_info and 'actualStartTime' in live_info:
                    start_time = iso8601.parse_date(live_info['actualStartTime'])
                    end_time = iso8601.parse_date(live_info['actualEndTime'])
                    duration_seconds = (end_time - start_time).total_seconds()
                    duration_hours = round(duration_seconds / 3600, 2)
                
                # Get broadcast content type
                live_broadcast_content = video_data['snippet'].get('liveBroadcastContent', 'none')
                
                data.append({
                    'handle': handle,
                    'video_id': vid_id,
                    'title': video_data['snippet']['title'],
                    'published_at': pub_date_str,
                    'live_broadcast_content': live_broadcast_content,
                    'actual_start_time': live_info.get('actualStartTime'),
                    'actual_end_time': live_info.get('actualEndTime'),
                    'scheduled_start_time': live_info.get('scheduledStartTime'),
                    'duration_hours': duration_hours,
                    'view_count': video_data.get('statistics', {}).get('viewCount', 0),
                    'like_count': video_data.get('statistics', {}).get('likeCount', 0),
                    'comment_count': video_data.get('statistics', {}).get('commentCount', 0)
                })
            
            next_page = search_res.get('nextPageToken')
            if not next_page:
                break
    except Exception as e:
        logging.warning(e)
                
    return data

def data_preprocessing(data):
    """
    Preprocesses a list of dictionaries to save data as CSV.
    Args:
        data: List of dictionaries
    """
    
    if not data:
        logging.warning("No live broadcast videos found to save.")
        return

    # Clean data      
    for video in data:
        for key, val in video.items():
            if isinstance(val, str):
                video[key] = _clean_value(val)
        
    df = pd.DataFrame(data)
    
    df.to_csv(DATA_PATH, index=False, encoding="utf-8")

def _clean_value(value):
    """
    Internal utility function to clean and normalize string values.
    Otherwise it may cause issues when writing to CSV.
    Args:
        value: A single string value in a dictionary to clean.
    """

    # Handle missing values
    if not value:
        return "-"
    # Normalize newlines
    value = value.replace("\n", " | ").replace("\r", " ")
    # Normalize curly quotes to straight double/single quotes
    value = value.replace("“", '"').replace("”", '"')
    value = value.replace("‘", "'").replace("’", "'")
    # Unescape HTML entities
    value = html.unescape(value)
    # Replace double quotes with single quotes
    value = value.replace('"', "'")
    # Replace commas to avoid breaking CSV formatting
    value = value.replace(",", ";")
    # Collapse multiple spaces
    value = re.sub(r"\s{2,}", " ", value)

    return value.strip()

def data_loading():
    """
    Load CSV into database
    """
    df = pd.read_csv(DATA_PATH)

    df.to_sql("talent_analytics", ENGINE, schema="hololive", if_exists="replace", index=False)

def main():
    try:
        # Initialize client
        client = initialize_client()
        data_analytics_all = []

        # Get all talent channels to extract data
        logging.info(f"Detected {len(CHANNEL_HANDLES)} to extract analytics.\n")
        for handle in CHANNEL_HANDLES:
            try:
                channel_id = extract_channel_id(client, handle)
                logging.info(f"Processing channel: {handle}")
                data_analytics = extract_analytics(client, channel_id, handle)
                logging.info(f"{handle}: {len(data_analytics)} completed livestreams found.\n")
                data_analytics_all.extend(data_analytics)
            except Exception as e:
                logging.error(f"Failed to process {handle}: {e}")

        # Save the analytics data to CSV
        data_preprocessing(data_analytics_all)
        
        # Load data into DB
        data_loading()

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
