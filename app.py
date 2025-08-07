from contextlib import contextmanager
from nicegui import ui
import pandas as pd
from typing import Union, List

#########################################################
# Configuration
#########################################################

# Let app content fill full viewport height
ui.context.client.content.classes('h-screen')

# Dummy data
df = pd.read_csv('.data/talent_info.csv')

#########################################################
# Utility functions
#########################################################

@contextmanager
def clickable_img_button(image_path: str, target_page: str):
    """
    Turns an image into a standardized clickable button that navigates to a specified page
    """
    with ui.element('div').style('width: 110px; height: 110px; overflow: hidden;'):
        ui.image(image_path).on('click', lambda: ui.navigate.to(target_page)).classes('cursor-pointer object-cover w-full h-full')

@contextmanager
def character_img_display(image_path: str, box_width: int = 300, box_height: int = 800):
    """
    Displays an image scaled to fit within a fixed-size vertical rectangle,
    maintaining its aspect ratio without cropping.

    Args:
        image_path (str): Path to the image
        box_width (int): Width of the container box in pixels
        box_height (int): Height of the container box in pixels
    """
    with ui.element('div').style(f'width: {box_width}px; height: {box_height}px; display: flex; align-items: flex-start; justify-content: center; background-color: transparent;'):
        ui.image(image_path).style('max-width: 100%; max-height: 100%; object-fit: contain;')

@contextmanager
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
        ui.label("Test Web App").classes('font-bold text-white')

    # Footer
    with ui.footer().classes('justify-center'):
        ui.label('Test Web App')

    # Dynamic Sidebar 
    with ui.left_drawer().props('width=300').classes('bg-blue-100'):
        with ui.column().classes('p-2').style('gap: 12px'):
            for sidebar_i, sidebar_row in df.iterrows():
                page_name = f"/page{sidebar_i}"
                img_path = sidebar_row['default_image']
                clickable_img_button(img_path, page_name)

    # Main Content
    with ui.row().classes('w-full flex-nowrap items-start gap-4'):
        
        ui.column().style('width: 100px;')  # Spacer
        
        with ui.column().style('width: 35%'):
            character_img_display(image_path)
            
        with ui.column().style('width: 30%'):
            with ui.grid(columns=2).classes('gap-y-10 gap-x-2'):
                for col in ['Name', 'Birthday']:
                    val = row.iloc[0][col]
                    ui.label(f'{col}:').classes('font-medium')
                    ui.label(str(val))
            ui.label(label_text).classes('text-lg font-semibold pt-4')

#########################################################
# Page Layout
#########################################################

# Dynamic Pages
for i, row in df.iterrows():
    route = f"/page{i}"
    @ui.page(route)
    def _(i=i, row=row):  # bind loop variable
        layout(
            title=f"Page {i}",
            image_path=row['default_image'],
            row=df.iloc[[i]],
            label_text=f"Data for {row['Name']}",
            i=i
        )
