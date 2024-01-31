import os, csv, time, click, re, threading
from typing import List, Tuple, Optional
from configstore.configstore import Config
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from azdevops.auth import get_user_profile_based_on_key
import shutil

def get_terminal_size():
    try:
        terminal_width, terminal_height = shutil.get_terminal_size()
        return terminal_width, terminal_height
    except Exception as e:
        print(f"Error: {e}")
        return None

def calculate_dialog_size():
    terminal_width, terminal_height = get_terminal_size()

    # Define your desired dialog width and height, or adjust it dynamically
    dialog_width = min(terminal_width - 2, 90)  # Adjust as needed
    dialog_height = min(terminal_height - 4, 24)  # Adjust as needed

    return dialog_width, dialog_height

def center_text(text, width):
    # Calculate the left indentation to center text within 'width' columns
    left_indent = (width - len(text)) // 2
    return ' ' * left_indent + text

def get_default_profile():
    PROFILE = 'default'
    try:
        CONFIG = Config('azdev')
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y' or VAL == 'y':
                return PROFILE
    except:
        pass
    return PROFILE

def get_default_url():
    URL = 'default'
    try:
        CONFIG = Config('azdev')
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y' or VAL == 'y':
                URL = CONFIG.get_config('url', PROFILE)
                if URL:
                    return URL.upper()  # Ensure URL is not None and convert to uppercase
    except Exception as e:
        print(f"Error in get_default_url: {str(e)}")

    # Check if URL is not None before calling upper()
    if URL is not None:
        return URL.upper()
    else:
        return 'DEFAULT'

def remove_equals(ctx, param, value):
    if value:
        if isinstance(value, str):
            modified_value = value.replace('=', '')
            return modified_value
        elif isinstance(value, tuple):
            modified_value = tuple(v.replace('=', '') if isinstance(v, str) else v for v in value)
            return modified_value
    return value

def join_lists_to_strings(*lists, separator=','):
    """
    Joins elements of multiple lists into strings with the specified separator.

    Args:
        *lists (list): Variable number of lists to join.
        separator (str, optional): Separator to use (default is ',').

    Returns:
        tuple: A tuple containing the joined strings for each input list.
    """
    joined_strings = tuple(
        separator.join(map(str, lst)) if lst else ""  # Join if not None or empty
        for lst in lists
    )
    return joined_strings

# Function to clear the terminal screen
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the visible content
    print("\033c", end='')  # Clear the terminal history (scroll-back buffer)


def display_menu(data, ctx):
    WIDTH, HEIGHT = calculate_dialog_size()
    INSTRUCTIONS = "[INSTRUCTIONS]"
    MANUAL = "[ARROW KEYS] to navigate | [SPACEBAR] to select | [TAB] to OK | [ENTER] to execute"

    # Calculate the padding for the "INSTRUCTIONS" line
    instructions_padding = " " * ((WIDTH - len(INSTRUCTIONS)) // 2)

    # Calculate the padding for the "MANUAL" line
    manual_padding = " " * ((WIDTH - len(MANUAL)) // 2)

    MANUAL = f"{instructions_padding}{INSTRUCTIONS}\n{manual_padding}{MANUAL}\n"

    selected_id = None
    if not data:
        print("No items match the selected criteria.")
        return None

    if ctx.obj['menu']:
        def run_dialog():
            nonlocal selected_id
            style = Style.from_dict({
                'dialog': 'bg:#4B4B4B',
                'dialog.body': 'bg:#242424 fg:#FFFFFF',
                'dialog.title': 'bg:#00aa00',
                'radiolist': 'bg:#1C1C1C fg:#FFFFFF',
                'button': 'bg:#528B8B',
                'button.focused': 'bg:#00aa00',
            })

            menu_key = 'ID' if ctx.obj['menu'] else 'Id'
            menu_items = []

            for item in data:
                item_id = item.get(menu_key, item.get('Id', None))
                if item_id is not None:
                    menu_items.append((item_id, f"ID: {item_id} => {item['Title']}"))

            selected_id = radiolist_dialog(
                title="Select Issue",
                text=MANUAL + "\nChoose an Issue:",
                values=menu_items,
                style=style
            ).run()

        dialog_thread = threading.Thread(target=run_dialog)
        dialog_thread.start()
        dialog_thread.join()
    else:
        return None
    return selected_id

def generic_menu(data):
    WIDTH, HEIGHT = calculate_dialog_size()
    INSTRUCTIONS = "[INSTRUCTIONS]"
    MANUAL = "[ARROW KEYS] to navigate | [SPACEBAR] to select | [TAB] to OK | [ENTER] to execute"

    # Calculate the padding for the "INSTRUCTIONS" line
    instructions_padding = " " * ((WIDTH - len(INSTRUCTIONS)) // 2)

    # Calculate the padding for the "MANUAL" line
    manual_padding = " " * ((WIDTH - len(MANUAL)) // 2)

    MANUAL = f"{instructions_padding}{INSTRUCTIONS}\n{manual_padding}{MANUAL}\n"

    selected = None
    if not data:
        print("No items match the selected criteria.")
        return None

    def run_dialog():
        nonlocal selected
        style = Style.from_dict({
            'dialog': 'bg:#4B4B4B',
            'dialog.body': 'bg:#242424 fg:#FFFFFF',
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C fg:#FFFFFF',
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        values = [(b, b) for b in data]

        selected = radiolist_dialog(
            title="Select Item",
            text="Choose an Object:",
            values=values,
            style=style
        ).run()

    run_dialog()  # Call run_dialog to display the menu and make a selection

    return (selected,)

def setup_runner(ctx, projects):
    # setup our config store to use
    CONFIG = Config('azdev')
    # define the profile if its configured in ctx.obj
    PROFILE = ctx.obj['PROFILE']
    # init our RUN dictionary
    RUN = {}
    # rip thru each project

    if projects:
        for project in projects:
            PROFILE = get_user_profile_based_on_key(project)
            if PROFILE not in RUN:
                RUN[PROFILE] = {
                    "%s" %(project)
                }
            else:
                RUN[PROFILE].update({ "%s" %(project) })
    else:
        # init a dictionary to hold ALL projects to prepare for menu
        CACHED_PROJECTS = {}
        for PROFILE in CONFIG.PROFILES:
            CACHED_PROJECTS.update(CONFIG.get_metadata('projects', PROFILE))
        if CACHED_PROJECTS:
            CACHED_PROJECTS = sorted(CACHED_PROJECTS)
        projects = generic_menu(CACHED_PROJECTS)
        if projects:
            # rip thru each project now
            for project in projects:
                # get the profile
                PROFILE = get_user_profile_based_on_key(project)
                # if profile exists based on project selected
                if PROFILE not in RUN:
                    RUN[PROFILE] = {
                        "%s" %(project)
                    }
                else:
                    RUN[PROFILE].update({ "%s" %(project) })
    return RUN

def setup_az_ctx(ctx, debug, menu):
    from azdevops.azdevclient import AzDevClient
    AZDEV = AzDevClient()
    user_profile = ctx.obj['PROFILE']
    url = None

    ctx.obj['menu'] = bool(menu)

    if ctx.obj.get('setup', False):
        if user_profile is None:
            user_profile = 'default'

        try:
            INPUT = click.prompt(f'INFO: profile "{user_profile}" not found - create a new one now? (y/n)')
        except click.exceptions.ExitSignal:
            click.echo("\nINFO: operation was canceled.")
            exit(-1)

        if 'y' in INPUT.lower():
            AZDEV.get_session(url, user_profile, force=True)
        else:
            exit(0)

