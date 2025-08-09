from nicegui import ui
import pandas as pd
from PIL import Image
import os
import requests
import hashlib
from urllib.parse import urlparse

#########################################################
# Configuration
#########################################################

# Let app content fill full viewport height
ui.context.client.content.classes('h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 text-gray-800 font-sans')

# Read talent data 
df = pd.read_csv('./data/talent_schedule.csv')

# Read analytics data (Data transformation runs here for now, in case of future updates)
df_analytics = pd.read_csv('./data/talent_analytics.csv')
df_analytics = df_analytics.groupby('handle', as_index=False)[['duration_hours', 'view_count', 'like_count', 'comment_count']].sum()

# Ensure dirs
CACHE_DIR = "./data/cache"
PADDED_DIR = "./data/padded"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PADDED_DIR, exist_ok=True)

#########################################################
# Utility functions
#########################################################

def clickable_img_button(image_path: str, target_page: str, live: bool = False, box_width: int = 110, box_height: int = 110):
    """
    Buttons in sidebar to redirect to respective talent's page
    Applied in layout()
    Args:
        image_path: link to image in row['default_image']
        target_page: target page defined in Sidebar code chunk
        live: Whether talent has upcoming content or not
        box_width
        box_height
    """
    
    p = urlparse(image_path)
    ext = os.path.splitext(os.path.basename(p.path))[1] or ".png"
    name = hashlib.sha1(image_path.encode()).hexdigest() + ext
    local_input = os.path.join(CACHE_DIR, name)

    if not os.path.exists(local_input):
        resp = requests.get(image_path, stream=True, timeout=10)
        resp.raise_for_status()
        with open(local_input, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

    zoom_in = 1.5
    with ui.element('div').style(
        f'position: relative; width: {box_width}px; height: {box_height}px; overflow: hidden; '
        'border: 1px solid #e2e8f0; border-radius: 12px; display: flex; justify-content: center; align-items: flex-start; '
        'background-color: white; box-shadow: 0 2px 6px rgba(0,0,0,0.05); transition: transform 0.2s ease;'
    ).classes('hover:shadow-md hover:-translate-y-0.5'):
        ui.image(local_input).style(
            f'cursor: pointer; border-radius: 12px; '
            f'transform: scale({zoom_in}); '
            f'transform-origin: top center; '
            f'width: {box_width}px; height: auto;'
        ).on(
            'click', lambda: ui.run_javascript(f'window.location.href = "{target_page}"')
        )

        if live:
            with ui.element('div').style(
                'position: absolute; top: 5px; right: 5px; width: 10px; height: 10px; '
                'background-color: #facc15; border-radius: 50%; '
                'box-shadow: 0 0 12px 4px rgba(250, 204, 21, 0.9); animation: pulse 1s infinite;'
            ):
                pass

    # Add keyframes for pulse animation globally (run once)
    if not hasattr(clickable_img_button, 'pulse_style_added'):
        ui.run_javascript('''
            const style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = `
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.4); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }
            `;
            document.head.appendChild(style);
        ''')
        clickable_img_button.pulse_style_added = True

def character_img_display(image_path: str, box_width: int = 300, box_height: int = 500):
    """
    Display full image of talent in main content column
    Applied in layout()
    Args:
        image_path: link to image in row['default_image']/image_path (same thing, fix later)
        box_width
        box_height
    """
    
    p = urlparse(image_path)
    ext = os.path.splitext(os.path.basename(p.path))[1] or ".png"
    name = hashlib.sha1(image_path.encode()).hexdigest() + ext
    local_input = os.path.join(CACHE_DIR, name)

    if not os.path.exists(local_input):
        resp = requests.get(image_path, stream=True, timeout=10)
        resp.raise_for_status()
        with open(local_input, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

    padded_name = hashlib.sha1(f"{image_path}_{box_width}x{box_height}".encode()).hexdigest() + ext
    padded_path = os.path.join(PADDED_DIR, padded_name)
    if not os.path.exists(padded_path):
        img = Image.open(local_input).convert("RGBA")
        img.thumbnail((box_width, box_height), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (box_width, box_height), (255, 255, 255, 255))
        x = (box_width - img.width) // 2
        y = (box_height - img.height) // 2
        bg.paste(img, (x, y), img)
        bg.save(padded_path)

    with ui.element('div').style(
        f'width: {box_width}px; height: {box_height}px; '
        'display: flex; align-items: center; justify-content: center; '
        'background-color: white; overflow: hidden;'
    ):
        ui.image(padded_path).style(
            'max-width: 100%; max-height: 100%; object-fit: contain;'
        )

def clickable_wide_button(image_path: str, youtube_link: str, box_width: int = 300, box_height: int = 150):
    """
    Buttons to display upcoming content and redirect to that YouTube page
    Applied in layout()
    Args:
        image_path: link to image in image{idx}
        youtube_link: target page defined in youtube_link{idx}
        box_width
        box_height
    """
    
    p = urlparse(image_path)
    ext = os.path.splitext(os.path.basename(p.path))[1] or ".png"
    name = hashlib.sha1(image_path.encode()).hexdigest() + ext
    local_input = os.path.join(CACHE_DIR, name)

    if not os.path.exists(local_input):
        resp = requests.get(image_path, stream=True, timeout=10)
        resp.raise_for_status()
        with open(local_input, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

    with ui.element('div').style(
        f'width: {box_width}px; height: {box_height}px; overflow: hidden; '
        'border: 1px solid #e2e8f0; border-radius: 12px; display: flex; align-items: center; cursor: pointer; '
        'background-color: white; box-shadow: 0 2px 6px rgba(0,0,0,0.05); transition: transform 0.2s ease;'
    ).classes('hover:shadow-md hover:-translate-y-0.5').on('click', lambda: ui.run_javascript(f'window.open("{youtube_link}", "_blank")')):
        ui.image(local_input).style(
            'max-height: 100%; max-width: 100%; object-fit: contain; border-radius: 12px 0 0 12px;'
        )

def layout(image_path: str, row: pd.DataFrame, i: int):
    """
    Full page layout including header, sidebar, footer, and content.
    Args:
        image_path: To display talent image (row['default_image'].iloc[0])
        row: A single row of pd.DataFrame representing the talent displayed
        i: Index of that row
    """
    
    # Theme
    ui.add_head_html('''
    <style>
        body {font-family: 'Inter', sans-serif; }
        header, footer { background-color: #1e293b; color: white; }
        .hl-card { background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 16px; }
        .hl-section-title { border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 8px; font-size: 1.2rem; font-weight: 600; color: #0f172a; }
        .hl-label { color: #475569; font-weight: 500; }
        .hl-value { color: #1e293b; }
    </style>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    ''')

    # Header
    with ui.header().classes('row items-center px-6 py-3 shadow-md bg-sky-400 text-white'):
        ui.label("Hololive Content Tracker").classes('font-bold text-lg tracking-wide')

    # Footer
    with ui.footer().classes('justify-center py-2 text-sm text-white bg-sky-400 shadow-md'):
        ui.label('Made by JYNgithub')


    # Sidebar
    with ui.left_drawer().props('width=320').classes('bg-sky-100 shadow-md border-r border-blue-200'):
        with ui.grid(columns=2).classes('p-4 gap-6'):
            for sidebar_i, sidebar_row in df.iterrows():
                page_name = f"/page{sidebar_i}"
                img_path = sidebar_row['default_image']
                live = pd.notna(sidebar_row.get('image1'))
                clickable_img_button(img_path, page_name, live=live)

    # Main Content
    with ui.row().classes('w-full flex-nowrap items-start gap-4'):
        ui.column().style('width: 100px;')

        # Character column
        with ui.column().style('width: 30%'):
            character_img_display(image_path)
            ui.label(row['name'].iloc[0]).classes('text-3xl font-bold pb-3')
            for col in ['birthday', 'unit', 'hashtags']:
                val = row.iloc[0][col]
                if pd.notna(val) and str(val).strip():
                    with ui.row().classes('items-baseline gap-1'):
                        ui.label(f"{col.capitalize()}:").classes('hl-label text-black')
                        ui.label(str(val)).classes('text-sm text-gray-600')

        # Content column
        if "[" not in str(row['name'].iloc[0]): # Logic to detect if talent has graduated
            with ui.column().style('width: 30%'):
                ui.label("Upcoming Content").classes('hl-section-title')
                all_missing = True
                for idx in range(1, 5):
                    img_col = f'image{idx}'
                    yt_col = f'youtube_link{idx}'
                    if img_col in row.columns and yt_col in row.columns and pd.notna(row.iloc[0][img_col]) and pd.notna(row.iloc[0][yt_col]) and str(row.iloc[0][yt_col]).strip():
                        all_missing = False
                        break
                if all_missing: # Logic to detect if talent has no upcoming content
                    ui.label("No upcoming content yet").classes('text-sm text-gray-500 pt-2')
                    ui.element('div').style('height: 350px')
                else:
                    buttons = []
                    for idx in range(1, 5): # Up to 4 upcoming content
                        img_col = f'image{idx}'
                        yt_col = f'youtube_link{idx}'
                        desc_col = f'description{idx}'
                        dt_col = f'datetime{idx}'
                        if img_col in row.columns and yt_col in row.columns and pd.notna(row.iloc[0][img_col]) and pd.notna(row.iloc[0][yt_col]) and str(row.iloc[0][yt_col]).strip():
                            image_path = row.iloc[0][img_col]
                            youtube_link = row.iloc[0][yt_col]
                            description = row.iloc[0][desc_col] if desc_col in row.columns else ''
                            datetime_val = row.iloc[0][dt_col] if dt_col in row.columns else ''
                            buttons.append((image_path, youtube_link, description, datetime_val))
                    for i in range(0, len(buttons), 2):
                        with ui.row().classes('gap-20 pt-5').style('flex-wrap: nowrap;'):
                            for b in buttons[i:i+2]:
                                with ui.column().style('width: 48%; min-width: 150px; padding: 8px; box-sizing: border-box;'):
                                    clickable_wide_button(b[0], b[1])
                                    ui.label(f"{b[2]}").classes('text-sm font-medium pt-1')
                                    ui.label(f"{b[3]}").classes('text-xs text-gray-500')
                    ui.element('div').style('height: 40px')

                # Analytics section
                ui.label("Livestream Analytics (Past 7 days)").classes('hl-section-title')
                handle = row['Handle'].iloc[0]
                analytics_row = df_analytics[df_analytics['handle'] == handle]
                if not analytics_row.empty: # Logic to detect if talent has any analytics past 7 days
                    metrics = [
                        ('Total Duration', f"{analytics_row['duration_hours'].iloc[0]:.2f} hours"),
                        ('Total Views', f"{analytics_row['view_count'].iloc[0]:,}"),
                        ('Total Likes', f"{analytics_row['like_count'].iloc[0]:,}"),
                        ('Total Comments', f"{analytics_row['comment_count'].iloc[0]:,}")
                    ]
                    for label, value in metrics:
                        with ui.row().classes('items-baseline gap-1'):
                            ui.label(f"{label}:").classes('hl-label text-black')
                            ui.label(value).classes('hl-value')
                else:
                    ui.label("No analytics data available").classes('text-sm text-gray-500')
        else:
            with ui.column().style('width: 30%').classes('items-center justify-center'):
                ui.element('div').style('height: 200px')
                ui.label("This talent has parted ways with Hololive.").classes('text-sm text-gray-500 pt-5 text-center')
                ui.label("Maybe they're still out there somewhere?").classes('text-sm text-gray-500 pt-5 text-center')

#########################################################
# Pages
#########################################################

# Dynamic Pages
for i in range(len(df)):
    route = f"/page{i}"
    @ui.page(route)
    def _(i=i):
        row = df.iloc[[i]]
        layout(
            image_path=row['default_image'].iloc[0],
            row=row,
            i=i
        )

@ui.page('/')
def index():
    ui.label('Welcome! Redirecting...')
    ui.timer(0.5, lambda: ui.navigate.to('/page0'))  # Redirect to first page
ui.run()