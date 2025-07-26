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
dummy_df = pd.DataFrame([
    [12, 45, 78, 23, 56, 89, 34, 67],
    [90, 11, 22, 33, 44, 55, 66, 77],
    [88, 76, 54, 32, 10, 98, 76, 54],
    [12, 45, 78, 23, 56, 89, 34, 67]
], columns=[f'col{i+1}' for i in range(8)])

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
def layout(title: str, image_path: str, row_df: pd.DataFrame, label_text: str):
    """
    Full page layout including header, sidebar, footer, and content.

    Args:
        title (str): Page title (not used yet, but can be shown in content)
        image_path (str): Path to the image for the left column
        row_df (pd.DataFrame): A single-row DataFrame (max 16 values)
        label_text (str): Text to display below the grid
    """
    # Header
    with ui.header().classes('row items-center'):
        ui.label("Test Web App").classes('font-bold text-white')
    # Footer
    with ui.footer().classes('justify-center'):
        ui.label('Test Web App')
    # Sidebar
    with ui.left_drawer().props('width=300').classes('bg-blue-100'):
        with ui.column().classes('p-2').style('gap: 12px'):
            with ui.row().classes('justify-between'):
                clickable_img_button('assets/flower1.jfif', '/page1')
                clickable_img_button('assets/flower2.jfif', '/page2')
            with ui.row().classes('justify-between'):
                clickable_img_button('assets/flower3.jpg', '/page3')
                clickable_img_button('assets/flower4.jpg', '/page4')
    # # Sidebar
    # with ui.left_drawer().props('width=300').classes('bg-blue-100'):
    #     with ui.column().classes('p-2').style('gap: 12px'):
    #         for i in range(0, len(dummy_df), 2):  # Two per row
    #             with ui.row().classes('justify-between'):
    #                 # First button
    #                 if i < len(dummy_df):
    #                     img1 = dummy_df.iloc[i]['img_path']
    #                     clickable_img_button(img1, f'/page{i+1}')
    #                 # Second button, if it exists
    #                 if i + 1 < len(dummy_df):
    #                     img2 = dummy_df.iloc[i + 1]['img_path']
    #                     clickable_img_button(img2, f'/page{i+2}')
    # Main content
    with ui.row().classes('w-full flex-nowrap items-start gap-4'):
        ui.column().style('width: 100px;')  # Spacer
        with ui.column().style('width: 35%'):
            character_img_display(image_path)
        with ui.column().style('width: 30%'):
            with ui.grid(columns=2).classes('gap-y-10 gap-x-2'):
                for col, val in row_df.iloc[0].items():
                    ui.label(f'{col}:').classes('font-medium')
                    ui.label(str(val))


#########################################################
# Page Layout
#########################################################

# Page 1 (Start Page)
@ui.page('/')
@ui.page('/page1')
def page1():
    row_df = dummy_df.iloc[[0]]
    layout(
        title='Page One',
        image_path='assets/flower1.jfif',
        row_df=row_df,
        label_text='Page 1 Data Overview'
    )

# Page 2
@ui.page('/page2')
def page2():
    row_df = dummy_df.iloc[[1]]
    layout(
        title='Page Two',
        image_path='assets/flower2.jfif',
        row_df=row_df,
        label_text='Page 2 Data Overview'
    )
    # ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# Page 3
@ui.page('/page3')
def page3():
    row_df = dummy_df.iloc[[2]]
    layout(
        title='Page Three',
        image_path='assets/flower3.jpg',
        row_df=row_df,
        label_text='Page 3 Data Overview'
    )
    # ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# Page 4
@ui.page('/page4')
def page4():
    row_df = dummy_df.iloc[[3]]
    layout(
        title='Page Four',
        image_path='assets/flower4.jpg',
        row_df=row_df,
        label_text='Page 4 Data Overview'
    )
    # ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# Run App
ui.run(title='Test Web App')