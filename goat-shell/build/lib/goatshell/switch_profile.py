from typing import List, Tuple, Optional
import click, threading
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from configstore.configstore import Config
from prompt_toolkit.styles import Style

def get_profiles_for_store(config_store):
    CONFIG = Config(config_store)
    return [PROFILE for PROFILE in CONFIG.PROFILES if 'latest' not in PROFILE]

def display_profile_menu_thread(profiles):
    def run_dialog():
        nonlocal selected_profile_id
        style = Style.from_dict({
            'dialog': 'bg:#4B4B4B',
            'dialog.body': 'bg:#242424 fg:#FFFFFF',
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C fg:#FFFFFF',
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        # Assuming profiles is a list of dicts, each with 'id' and 'name' keys
        values = [(profile, profile) for profile in profiles]


        selected_profile_id = radiolist_dialog(
            title="Select Profile",
            text="Choose a profile:",
            values=values,
            style=style
        ).run()

    selected_profile_id = None
    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()
    return selected_profile_id

def switch_profile(config_store, verbose: bool = False) -> Tuple[str, Optional[str]]:
    """
    Fetch a list of profiles, present them to the user, and switch to the selected profile.

    Args:
        config_store (str): The config store name to fetch profiles from.
        verbose (bool): If True, print additional info.

    Returns:
        Tuple[str, Optional[str]]: A tuple containing the ID of the active profile, and an error message if any.
    """

    profiles = get_profiles_for_store(config_store)  # Fetch profiles for the given config store

    # Check if the profiles list is empty
    if not profiles: 
        return "", "No profiles found for the given config store!"
    if len(profiles) <= 1:
        selected_profile_id = profiles[0]
        return f"{selected_profile_id}", None

    selected_profile_id = display_profile_menu_thread(profiles)

    # Check if a profile was selected
    if selected_profile_id:
        # Logic to switch to the selected profile
        # This is where you would put the logic to actually switch profiles based on your application's needs
        return f"{selected_profile_id}", None
    else:
        return "", "Profile selection failed"

def select_profile(config_store):
    config_store = ''.join(config_store)
    result, error = switch_profile(config_store, verbose=True)
    if error:
        return 'DEFAULT'
    else:
        return result

