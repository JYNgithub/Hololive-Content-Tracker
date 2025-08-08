from contextlib import contextmanager
from nicegui import ui
import pandas as pd
from PIL import Image
import os
import requests
import hashlib
import base64
from urllib.parse import urlparse

#########################################################
# Configuration
#########################################################

# Let app content fill full viewport height
ui.context.client.content.classes('h-screen')

# Read data
df = pd.read_csv('./data/talent_schedule.csv')

# Ensure dirs
CACHE_DIR = "./data/cache"
PADDED_DIR = "./data/padded"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PADDED_DIR, exist_ok=True)

#########################################################
# Utility functions
#########################################################

def clickable_img_button(image_path: str, target_page: str, box_width: int = 110, box_height: int = 110):
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
        f'width: {box_width}px; height: {box_height}px; overflow: hidden; '
        'border: 1px solid #ccc; border-radius: 6px; display: flex; justify-content: center; align-items: flex-start;'
    ):
        ui.image(local_input).style(
            f'cursor: pointer; border-radius: 6px; '
            f'transform: scale({zoom_in}); '
            f'transform-origin: top center; '
            f'width: {box_width}px; height: auto;'
        ).on(
            'click', lambda: ui.run_javascript(f'window.location.href = "{target_page}"')
        )

def character_img_display(image_path: str, box_width: int = 300, box_height: int = 500):
    """
    Displays an image scaled to fit within a fixed-size vertical rectangle,
    maintaining its aspect ratio without cropping.

    Args:
        image_path (str): Path to the image
        box_width (int): Width of the container box in pixels
        box_height (int): Height of the container box in pixels
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
        'background-color: transparent; overflow: hidden;'
    ):
        ui.image(padded_path).style(
            'max-width: 100%; max-height: 100%; object-fit: contain;'
        )

def layout(title: str, image_path: str, row: pd.DataFrame, label_text: str, i: int):
    """
    Full page layout including header, sidebar, footer, and content.

    Args:
        title (str): Page title (not used yet, but can be shown in content)
        image_path (str): Path to the image for the left column
        row (pd.DataFrame): A single-row DataFrame 
        label_text (str): Text to display below the grid
        i (int): Index of that row
    """
    # Header
    with ui.header().classes('row items-center'):
        ui.label("Hololive Content Tracker").classes('font-bold text-white')

    # Footer
    with ui.footer().classes('justify-center'):
        ui.label('Hololive Content Tracker')

    # Dynamic Sidebar 
    with ui.left_drawer().props('width=320').classes('bg-blue-100'):
        with ui.grid(columns=2).classes('p-2 gap-4'):
            for sidebar_i, sidebar_row in df.iterrows():
                page_name = f"/page{sidebar_i}"
                img_path = sidebar_row['default_image']
                clickable_img_button(img_path, page_name)

    # Main Content
    with ui.row().classes('w-full flex-nowrap items-start gap-4'):
        
        # Spacer column
        ui.column().style('width: 100px;')  
        
        # Character column
        with ui.column().style('width: 30%'):

            # Character image
            character_img_display(image_path)
            
            # Talent name
            ui.label(row['name'].iloc[0]).classes('text-3xl font-bold pb-3')

            # Talent information
            for col in ['birthday', 'unit', 'hashtags']:
                val = row.iloc[0][col]
                if pd.notna(val) and str(val).strip():
                    with ui.row().classes('items-baseline gap-1'):
                        ui.label(f"{col.capitalize()}:").classes('text-base font-bold text-gray-800')
                        ui.label(str(val)).classes('text-sm text-gray-600')

        # Content column
        with ui.column().style('width: 30%'):
            ui.label(label_text).classes('text-xl font-semibold pt-5')

#########################################################
# Page Layout
#########################################################

# Dynamic Pages
for i in range(len(df)):
    route = f"/page{i}"
    @ui.page(route)
    def _(i=i):
        row = df.iloc[[i]]
        layout(
            title=f"Page {i}",
            image_path=row['default_image'].iloc[0],
            row=row,
            label_text=f"Upcoming Content",
            i=i
        )

@ui.page('/')
def index():
    ui.label('Welcome! Redirecting...')
    ui.timer(0.5, lambda: ui.navigate.to('/page0'))  # Redirect to first page
ui.run()