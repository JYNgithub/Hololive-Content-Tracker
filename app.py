from contextlib import contextmanager
from nicegui import ui

# --- Shared Layout ---
@contextmanager
def frame(title: str):
    with ui.header().classes('row items-center'):
        ui.button(icon='menu', on_click=lambda: left_drawer.toggle()).props('flat color=white')
        ui.label(title).classes('font-bold text-white')
    with ui.footer().classes('justify-center'):
        ui.label('© 2025 My App')
    with ui.left_drawer().classes('bg-blue-100') as left_drawer:
        ui.link('Page One', '/page1').classes('text-black')
        ui.link('Page Two', '/page2').classes('text-black')
        ui.link('Page Three', '/page3').classes('text-black')
    with ui.column().classes('absolute-center items-center p-6 w-full'):
        yield

# --- Page 1 (Start Page) ---
@ui.page('/')
@ui.page('/page1')
def page1():
    with frame('Page One'):
        ui.markdown('## Welcome to **Page One**')

# --- Page 2 ---
@ui.page('/page2')
def page2():
    with frame('Page Two'):
        ui.markdown('## You are on **Page Two**')

        ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# --- Page 3 ---
@ui.page('/page3')
def page3():
    with frame('Page Three'):
        ui.markdown('## You are on **Page Three**')

        ui.button('Back to Page One', on_click=lambda: ui.navigate.to('/page1'))

# --- Run App ---
ui.run(title='NiceGUI Multipage with Dropdown')
