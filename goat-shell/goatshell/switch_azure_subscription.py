from typing import List, Tuple, Optional
import click, threading
from .azure_cli import az
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

#from prompt_toolkit.shortcuts.dialogs import radiolist_dialog
#import threading

def display_subscription_menu_thread(subscriptions):
    def run_dialog():
        nonlocal selected_subscription_id
        # Define custom styles for the dialog
        style = Style.from_dict({
            'dialog': 'bg:#4B4B4B',
            'dialog.body': 'bg:#242424 fg:#FFFFFF',  # Change fg to a lighter color (white in this case)
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C fg:#FFFFFF',  # Change fg to a lighter color
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        # Create and run the dialog
        selected_subscription_id = radiolist_dialog(
            title="Select Azure Subscription",
            text="Choose a subscription:",
            values=[(sub['id'], f"{sub['name']} (ID: {sub['id']})") for sub in subscriptions],
            style=style
        ).run()

    selected_subscription_id = None

    # Run the dialog in a separate thread
    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()

    return selected_subscription_id

def switch_azure_subscription(subscriptions_list, verbose: bool = False) -> Tuple[str, Optional[str]]:
    """
    Fetch a list of Azure subscriptions, present them to the user, and switch to the selected subscription.

    Args:
        subscriptions_list (List[dict]): List of subscription dictionaries.
        verbose (bool): If True, print the azure-cli commands and additional info.

    Returns:
        Tuple[str, Optional[str]]: A tuple containing the ID of the active subscription, and an error message if any.
    """

    # Check if the subscriptions list is empty
    if not subscriptions_list:
        return "", "No subscriptions found, requires: az login!"

    selected_subscription_id = display_subscription_menu_thread(subscriptions_list)

    # Find the selected subscription index
    selected_index = next((i for i, sub in enumerate(subscriptions_list) if sub['id'] == selected_subscription_id), -1)
    if selected_index != -1:
        _select_subscription(selected_index + 1, subscriptions_list, verbose)
        active = subscriptions_list[selected_index]
        return f"{active['id']}: {active['name']}", None
    else:
        return "", "Subscription selection failed"

def _select_subscription(n: int, subscriptions: List[dict], verbose: bool = False):
    subscription_id = subscriptions[n - 1]["id"]
    switch_cmd = f"account set -s {subscription_id}"

    if verbose:
        print(f'Issuing AZ CLI command: "{switch_cmd}"')

    exit_code, _, logs = az(switch_cmd)
    if exit_code != 0:
        raise ValueError(logs)

def _find_current_subscription(subscriptions: List[dict]) -> int:
    for idx, subscription in enumerate(subscriptions):
        if subscription["isDefault"]:
            return idx + 1
    return -1

def display_subscription_menu(subscriptions):
    """
    Display a menu to select an Azure subscription.

    Args:
        subscriptions (List[dict]): List of subscription dictionaries.

    Returns:
        str: The ID of the selected subscription.
    """
    choices = [(sub['id'], f"{sub['name']} (ID: {sub['id']})") for sub in subscriptions]
    selected_subscription_id = radiolist_dialog(
        title="Select Azure Subscription",
        text="Choose a subscription:",
        values=choices
    ).run()

    return selected_subscription_id

