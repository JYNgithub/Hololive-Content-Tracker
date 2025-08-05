import os
import re
import html
import iso8601
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build

############################################
# Configuration
############################################

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

load_dotenv()
API_KEY = os.getenv("YT_API_KEY")
CHANNEL_HANDLES = ['@NBA', '@ESPN']
EXTRACT_PERIOD = datetime.now(timezone.utc) - timedelta(days=182)  
data_path = './data/talent_analytics.csv'

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

def extract_analytics(client, channel_id):
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
                    'videoId': vid_id,
                    'title': video_data['snippet']['title'],
                    'publishedAt': pub_date_str,
                    'liveBroadcastContent': live_broadcast_content,
                    'actualStartTime': live_info.get('actualStartTime'),
                    'actualEndTime': live_info.get('actualEndTime'),
                    'scheduledStartTime': live_info.get('scheduledStartTime'),
                    'durationHours': duration_hours,
                    'viewCount': video_data.get('statistics', {}).get('viewCount', 0),
                    'likeCount': video_data.get('statistics', {}).get('likeCount', 0),
                    'commentCount': video_data.get('statistics', {}).get('commentCount', 0)
                })
                
            logging.info(f"Extracted {len(videos_res['items'])} archived live broadcasts.")
            
            next_page = search_res.get('nextPageToken')
            if not next_page:
                break
    except Exception as e:
        logging.warning(e)
        
    # Search for currently live and upcoming broadcasts
    try: 
        for event_type in ['live', 'upcoming']:
            search_res = client.search().list(
                part="snippet",
                channelId=channel_id,
                eventType=event_type,
                type="video",
                order="date",
                maxResults=50
            ).execute()
            
            if search_res.get('items'):
                video_ids = [item['id']['videoId'] for item in search_res['items']]
                videos_res = client.videos().list(
                    part="snippet,liveStreamingDetails,contentDetails,status,statistics",
                    id=','.join(video_ids)
                ).execute()
                
                for video_data in videos_res['items']:
                    live_info = video_data.get('liveStreamingDetails', {})
                    if not live_info:
                        continue
                    
                    vid_id = video_data['id']
                    pub_date_str = video_data['snippet']['publishedAt']
                    
                    # Calculate duration for live streams
                    duration_hours = None
                    if event_type == 'live' and 'actualStartTime' in live_info:
                        start_time = iso8601.parse_date(live_info['actualStartTime'])
                        current_time = datetime.now(timezone.utc)
                        duration_seconds = (current_time - start_time).total_seconds()
                        duration_hours = round(duration_seconds / 3600, 2)
                    
                    live_broadcast_content = video_data['snippet'].get('liveBroadcastContent', 'none')
                    
                    data.append({
                        'videoId': vid_id,
                        'title': video_data['snippet']['title'],
                        'publishedAt': pub_date_str,
                        'liveBroadcastContent': live_broadcast_content,
                        'actualStartTime': live_info.get('actualStartTime'),
                        'actualEndTime': live_info.get('actualEndTime'),
                        'scheduledStartTime': live_info.get('scheduledStartTime'),
                        'durationHours': duration_hours,
                        'viewCount': video_data.get('statistics', {}).get('viewCount', 0),
                        'likeCount': video_data.get('statistics', {}).get('likeCount', 0),
                        'commentCount': video_data.get('statistics', {}).get('commentCount', 0)
                    })
                    
                logging.info(f"Extracted {len(videos_res['items'])} {event_type} broadcasts.")

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
    
    df.to_csv(data_path, index=False, encoding="utf-8")

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

def main():
    try:
        # Initialize client
        client = initialize_client()
        data_analytics_all = []

        # Get all talent channels to extract data
        for handle in CHANNEL_HANDLES:
            try:
                channel_id = extract_channel_id(client, handle)
                logging.info(f"Processing channel: {handle}")
                data_analytics = extract_analytics(client, channel_id)
                logging.info(f"{handle}: {len(data_analytics)} broadcasts found.")
                data_analytics_all.extend(data_analytics)
            except Exception as e:
                logging.error(f"Failed to process {handle}: {e}")

        data_preprocessing(data_analytics_all)

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
