from contextlib import contextmanager
from nicegui import ui

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
def frame(title: str):
    """
    Sets up basic structure for each page
    """
    with ui.header().classes('row items-center'):
        ui.label("Test Web App").classes('font-bold text-white')
    with ui.footer().classes('justify-center'):
        ui.label('Test Web App')
    with ui.left_drawer().props('width=290').classes('bg-blue-100') as left_drawer:
        with ui.column().classes('p-2').style('gap: 12px'):
            with ui.row().classes('justify-between'):
                # def clickable_img_button(image_path: str, target_page: str):
                #     """
                #     Turns an image into a standardized clickable button that navigates to a specified page
                #     """
                #     with ui.element('div').style('width: 110px; height: 110px; overflow: hidden;'):
                #         ui.image(image_path).on('click', lambda: ui.navigate.to(target_page)).classes('cursor-pointer object-cover w-full h-full')
                clickable_img_button('assets/flower1.jfif', '/page1')
                clickable_img_button('assets/flower2.jfif', '/page2')
            with ui.row().classes('justify-between'):
                clickable_img_button('assets/flower3.jpg', '/page3')
    with ui.column():
        yield
        
#########################################################
# Page Layout
#########################################################

# Page 1 (Start Page)
@ui.page('/')
@ui.page('/page1')
def page1():
    with frame('Page One'):
        with ui.column():
            ui.markdown('## This is **Column 1**')
        with ui.column():
            ui.markdown('## This is **Column 2**')

# Page 2
@ui.page('/page2')
def page2():
    with frame('Page Two'):
        ui.markdown('## You are on **Page Two**')

        ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# Page 3
@ui.page('/page3')
def page3():
    with frame('Page Three'):
        ui.markdown('## You are on **Page Three**')

        ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# Run App
ui.run(title='Test Web App')
