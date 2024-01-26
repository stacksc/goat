from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import to_formatted_text, HTML
from pathlib import Path

import os
import sys
import subprocess
import re
import click
import logging
import shutil
import json
import configparser
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import Application, PromptSession
from prompt_toolkit.history import InMemoryHistory, FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

from . import misc as misc
from goatshell.style import styles
from goatshell.completer import GoatCompleter
from goatshell.parser import Parser
from goatshell.ui import getLayout
from goatshell.settings_manager import SettingsManager
from goatshell.custom_keys import CustomKeyBindings
from .dynamic_prompt import DynamicPromptSession
from pygments.token import Token
from .toolbar import create_toolbar

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# used to manage settings
settings_manager = SettingsManager()

# make this global to access outside goatshell
def load_default_provider_setting():
    return settings_manager.load_setting('default_provider', default_value='oci')

# Global variables
global vi_mode_enabled, safety_mode_enabled
os.environ['AWS_PAGER'] = ''  # Disable paging in AWS by default
vi_mode_enabled = False       # Default vi mode to false on start up
safety_mode_enabled = False   # Default safety mode to false on start up

current_service = load_default_provider_setting()

# Define the main Goatshell class
class Goatshell(object):
    CLOUD_PROVIDERS = misc.CLOUD_PROVIDERS
    INTERNAL_COMMANDS = misc.INTERNAL_COMMANDS

    def __init__(self, app, completer, parser, toolbar_message=None):
        getLayout()
        self.toolbar_message = toolbar_message
        self.vi_mode_enabled = self.load_vi_mode_setting()
        self.safety_mode_enabled = self.load_safety_mode_setting()
        self.style = Style.from_dict(styles)
        self.app = app
        self.completer = completer
        self.prefix = 'oci'
        self.aws_profiles = misc.read_aws_profiles()
        self.oci_profiles = misc.read_oci_profiles()
        self.key_bindings = CustomKeyBindings(self.app, self)
        self.init_history()
        self.session = self.init_session()
        self.set_parser_and_completer(current_service)
        self.initial_warning_displayed = False
        self.context_stack = []
        self.subscriptions = None
        self.current_subscription_index = 0
        self.aws_index = 0
        self.oci_index = 0
        self.profile = self.init_profile()

        if self.prefix == 'az':
            sub_id, sub_name = self.fetch_current_azure_subscription()
            if sub_id and sub_name:
                self.profile = sub_name  # Set the profile to the current Azure subscription name
        # Add this line to initialize the completer with the current context stack
        self.update_completer_context()
    
    def fetch_current_azure_subscription(self):
        try:
            result = subprocess.run(['az', 'account', 'show', '--output', 'json'],
                                    capture_output=True, text=True, check=True)
            current_subscription = json.loads(result.stdout)
        except Exception as e:
            print(f"Error fetching current Azure subscription: {e}")
            return None, None
        azure_subscription_cache = (current_subscription['id'], current_subscription['name'])
        return azure_subscription_cache 
    
    def fetch_azure_subscriptions(self):
        try:
            # Run Azure CLI command to list subscriptions and capture the output
            result = subprocess.run(['az', 'account', 'list', '--all', '--output', 'json'],
                                    capture_output=True, text=True, check=True)
    
            # Parse the JSON output into Python objects
            subscriptions = json.loads(result.stdout)
    
            # Extract the relevant information (e.g., subscription IDs)
            subscription_ids = [sub['id'] for sub in subscriptions]

            return [(sub['id'], sub['name']) for sub in subscriptions]
    
        except subprocess.SubprocessError as e:
            print(f"Error fetching subscriptions: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding subscription data: {e}")
            return []
        except Exception as e:
            # Catch-all for any other exceptions
            print(f"Unexpected error: {e}")
            return []
    
    def switch_to_next_subscription(self):
        if self.subscriptions is None or len(self.subscriptions) == 0:
            self.subscriptions = self.fetch_azure_subscriptions()

        if len(self.subscriptions) > 0:
            if len(self.subscriptions) < 5:
                current_sub_id, current_sub_name = self.subscriptions[self.current_subscription_index]
                os.system("az account set -s " + current_sub_id)
                self.profile = current_sub_name
                self.current_subscription_index = (self.current_subscription_index + 1) % len(self.subscriptions)
            else:
                from goatshell.switch_azure_subscription import switch_azure_subscription as switch
                subscriptions_dicts = [{'id': sub[0], 'name': sub[1]} for sub in self.subscriptions]
                result = switch(subscriptions_dicts)
                active_subscription_info, error_message = result
                if active_subscription_info:
                    self.profile = active_subscription_info.split(':')[1].strip()

    def set_completer(self, completer):
        self.completer = completer

    def load_vi_mode_setting(self):
        """Load the VI mode setting."""
        return settings_manager.load_setting('vi_mode_enabled', default_value=False)
    
    def load_safety_mode_setting(self):
        """Load the SAFETY mode setting."""
        return settings_manager.load_setting('safety_mode_enabled', default_value=False)
    
    def load_default_provider_setting(self):
        """Load the provider setting."""
        return settings_manager.load_setting('default_provider', default_value='oci')

    def save_vi_mode_setting(self):
        """Save the VI mode setting."""
        settings_manager.save_setting('vi_mode_enabled', self.vi_mode_enabled)
    
    def save_safety_mode_setting(self):
        """Save the safety mode setting."""
        settings_manager.save_setting('safety_mode_enabled', self.safety_mode_enabled)

    def save_default_provider(self, provider):
        settings_manager.save_setting('default_provider', provider)

    def init_profile(self):
        self.aws_index = 0
        self.oci_index = 0
        profile = 'DEFAULT'  # Initial value before getting profile
        return self.get_profile(self.prefix)  # update the profile

    def change_context(self, context_command):
        if context_command == '..':  # Go up one level
            if self.context_stack:
                self.context_stack.pop()
        elif context_command:  # Go into a specific context
            self.context_stack.append(context_command)

        # Update the prompt based on the new context
        self.session.message = self.generate_prompt()

        # Update the context in the completer
        self.completer.set_current_context(self.context_stack)

    # Add this new method
    def update_completer_context(self):
        # Update the completer with the current context stack
        if self.completer:
            self.completer.set_current_context(self.context_stack)

    def init_history(self):
        shell_dir = os.path.expanduser("~/goat/shell/")
        if not os.path.exists(shell_dir):
            os.makedirs(shell_dir)
        try:
            self.history = FileHistory(os.path.join(shell_dir, "history"))
        except:
            self.history = InMemoryHistory()

    def init_session(self):
        return DynamicPromptSession(vi_mode_enabled=self.vi_mode_enabled, style=self.style, history=self.history,
                                   auto_suggest=AutoSuggestFromHistory(), completer=self.completer,
                                   complete_while_typing=True, enable_history_search=True, key_bindings=self.key_bindings)

    def set_parser_and_completer(self, api_type):
        self.prefix = api_type.lower()  # Set prefix
    
        # First, check the user's home directory
        user_home = Path.home()
        user_json_path = user_home / "goat" / "shell" / "data" / f"{api_type}.json"
    
        # If user's custom JSON does not exist, use the default one
        if not user_json_path.exists():
            user_json_path = Path(os.path.dirname(os.path.abspath(__file__))) / "data" / f"{api_type}.json"
    
        self.parser = Parser(str(user_json_path), api_type)  # Reset parser

        # Update this line to pass both self and self.parser to GoatCompleter
        self.completer = GoatCompleter(self.parser)  # Reset completer
        self.completer.set_current_cloud_provider(self.prefix)  # Update current cloud provider in completer
        self.session.completer = self.completer  # Reset session completer

    def switch_to_next_provider(self):
        global current_service
        current_idx = self.CLOUD_PROVIDERS.index(current_service)
        self.context_stack = []

        for _ in range(len(self.CLOUD_PROVIDERS)):  # At most, loop through all providers once
            next_idx = (current_idx + 1) % len(self.CLOUD_PROVIDERS)
            next_service = self.CLOUD_PROVIDERS[next_idx]
        
            if misc.is_command_available(next_service):
                current_service = next_service
                self.prefix = next_service  # Update the instance attribute
                self.set_parser_and_completer(next_service)
                self.save_default_provider(next_service)
                break
            current_idx = next_idx
        else:  # This block runs if the loop completed without finding an available command
            # Handle the case where none of the commands are available.
            # This can be an error message, fallback, etc.
            print(f"None of the providers are available.")

        self.completer.set_current_context(self.context_stack)

    def toggle_vi_mode(self):
        self.vi_mode_enabled = not self.vi_mode_enabled
        self.save_vi_mode_setting()
        self.session = DynamicPromptSession(vi_mode_enabled=self.vi_mode_enabled, style=self.style, history=self.history, auto_suggest=AutoSuggestFromHistory(), completer=self.completer, complete_while_typing=True, enable_history_search=True, key_bindings=self.key_bindings)

    def toggle_safety_mode(self):
        self.safety_mode_enabled = not self.safety_mode_enabled
        self.save_safety_mode_setting()

    def get_profile(self, mode):
        if mode == 'aws':
            if self.aws_profiles:
                self.aws_index = (self.aws_index + 1) % len(self.aws_profiles)
                self.profile = self.aws_profiles[self.aws_index]
            else:
                self.profile = 'DEFAULT'
        elif mode == 'oci':
            if self.oci_profiles:
                self.oci_index = (self.oci_index + 1) % len(self.oci_profiles)
                self.profile = self.oci_profiles[self.oci_index]
            else:
                self.profile = 'DEFAULT'
        else:
            self.profile = 'DEFAULT'
        return self.profile

    def display_environment(self):
        details = {}
        user = tenant = None
        if self.prefix == 'oci':
            user = misc.get_oci_user(self.profile)
            tenant = misc.get_oci_tenant(self.profile)
        elif self.prefix == 'aws':
            user = misc.get_aws_user(self.profile)
            tenant = misc.get_aws_account(self.profile)
        if user and tenant:
            details["user"] = user.strip()
            details["tenant"] = tenant
        return details

    def execute_os_command(self, cmd):
        if self.safety_mode_enabled:  # safe mode
            print("INFO: OS commands are currently blocked due to safety mode. Please disable safety mode [F12] to execute OS commands.")
            return ''
        try:
            result = subprocess.run(cmd, shell=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            return False
    
        # Return None or appropriate response to indicate context change
        return None

    def reset_context(self):
        # Reset the context to the initial state
        self.context_stack = []
        # Notify the completer about the context reset
        self.completer.set_current_context(self.context_stack)

    def process_user_input(self, user_input):
        user_input = user_input.strip()
        tokens = user_input.split(' ')
        first_token = tokens[0].lower()

        # Handle Reset and Context Change Commands
        if user_input.startswith('%%'):
            command = user_input[2:].strip()
            if command == '':
                self.reset_context()
            else:
                self.change_context(command)
            return None

        # Handle the history command
        if user_input == "history":
            history_file = os.path.expanduser("~/goat/shell/history")
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    # Enumerate over the file lines and print them with line numbers
                    for index, line in enumerate(f, 1):
                        print(f"{index}  {line.strip()}")
                return ""  # or return None, so nothing further is executed for this command
            else:
                print("History file not found.")
                return ""
        elif user_input == "cloud":
            details = self.display_environment()
            details_str = f"Cloud Provider: {self.prefix.upper()}\n"
            for key, value in details.items():
                details_str += f"{key.upper()}: {value}\n"
            print()
            print(details_str)
            return ""
        elif user_input.startswith("cd"):
            tokens = user_input.split(" ", 1)
            # Check if a path is provided
            if len(tokens) > 1 and tokens[1]:
                path = tokens[1]
            else:
                # Default to the user's home directory if no path is provided
                path = os.path.expanduser("~")
        
            # Expand any "~" to the user's home directory and change directory
            path = os.path.expanduser(path)
            try:
                os.chdir(path)
            except Exception as e:
                print(f"Error: {e}")
            return ""

        # OS-level command check (starts with '##')
        if user_input.startswith('##'):
            # Execute OS-level command directly
            os_command = user_input[2:].strip()
            self.execute_os_command(os_command)
            return None

        if first_token in Goatshell.CLOUD_PROVIDERS or first_token in Goatshell.INTERNAL_COMMANDS:
            # Handle the 'clear' command specifically
            if first_token == 'clear' or first_token == 'c':
                self.execute_clear_command()
                return None
            else:
                return user_input  # Other internal commands

        # Prepend the cloud provider for other commands
        full_command = ' '.join([self.prefix] + self.context_stack + [user_input])

        if not self.is_valid_command_for_provider(full_command, self.prefix):
            print(f"Invalid command for {self.prefix}. Please check the available commands.")
            return None

        return full_command

    def change_context(self, context_command):
        if context_command == '..':  # Go up one level
            if self.context_stack:
                self.context_stack.pop()
        elif context_command:  # Go into a specific context
            self.context_stack.append(context_command)

        # Update the prompt based on the new context
        self.session.message = self.generate_prompt()

    def execute_clear_command(self):
        # Clear the screen
        os.system('clear' if os.name == 'posix' else 'cls')

    def is_valid_command_for_provider(self, command, provider):
        if not command.strip():
            return False
    
        # Load JSON for the provider
        self.completer.load_json(provider)
    
        # Ensure the JSON data is loaded
        if self.completer.goat_dict is None:
            logger.error(f"No JSON data found for provider {provider}")
            return False
    
        # Parse the user's command
        command_parts = command.split()
    
        # Check for global options if the command has more than one part
        if len(command_parts) > 1 and command_parts[1].startswith('-'):
            return self.is_valid_global_option(command_parts[1])
    
        # Check the primary command
        primary_command = command_parts[0]
        if primary_command not in self.completer.goat_dict:
            return False
    
        # If there are subcommands, check them as well
        if len(command_parts) > 1:
            # Assuming subcommands are nested within the command key
            subcommand = command_parts[1]
            # Check if the subcommand is in the list of valid subcommands
            return subcommand in self.completer.goat_dict[primary_command].get('subcommands', {})
    
        return True

    def is_valid_global_option(self, option):
        # Implement this method based on how you determine valid global options
        # Example:
        valid_global_options = ['-v', '-h', '--version', '--help']
        return option in valid_global_options

    def get_current_context(self, user_input=None):
        # Get the cloud provider and default profile
        cloud_provider = self.prefix
        default_profile = self.profile
        
        # Extract additional context information from user input
        additional_context = self.extract_additional_context(user_input)
        
        # Combine all context information into a dictionary
        current_context = {
            'cloud_provider': cloud_provider,
            'profile': default_profile,
            **additional_context  # Merge in additional context
        }
        
        return current_context
    
    def extract_additional_context(self, user_input):
        # Parse the user input to extract additional context information
        additional_context = {}
        # Your logic to extract context information from user_input goes here
        
        return additional_context
    
    def generate_prompt(self):
        # Getting the cloud provider context
        cloud_context = self.get_current_context()
    
        # Building the custom context stack string
        custom_context = '/'.join(self.context_stack) if self.context_stack else 'root'
    
        # Define your style
        style = Style([
                ('icon', 'bold fg:green'),  # Style for the icon
                ])
    
        # Unicode character for an eye
        icon = '\U0001F441'
    
        # Construct the prompt using both cloud context and custom context
        return HTML(f'[<b><u>{cloud_context["cloud_provider"]}</u></b>:<b><u>{cloud_context["profile"]}</u></b>] [{custom_context}] {icon}  ')
    
    def execute_command(self, cmd):
        # Check for empty command
        if not cmd.strip():
            return "empty command"

        # Split the command safely
        command_parts = cmd.split()
        if not command_parts:
            return "invalid command"

        # Check if the command is recognized for the current provider
        if not self.is_valid_command_for_provider(cmd, self.prefix):
            print(f"'{command_parts[0]}' is misspelled or not recognized by the system.")
            return "invalid command"

        # Proceed with executing the command
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()

        # Check the return code
        if p.returncode != 0:
            return "failure"
        else:
            return ""

    def run_cli(self):
        global current_service
        last_executed_command = ""
        last_executed_status = ""
        while True:
            prompt = self.generate_prompt()
            try:
                if not hasattr(self, 'initial_warning_displayed') or not self.initial_warning_displayed:
                    toolbar_to_use = self.toolbar_content
                    self.initial_warning_displayed = True
                else:
                    toolbar_to_use = create_toolbar(
                        profile=self.profile,
                        prefix=self.prefix,
                        vi_mode_enabled=self.vi_mode_enabled,
                        safety_mode_enabled=self.safety_mode_enabled,
                        last_executed_command=last_executed_command,
                        status_text=last_executed_status
                    )

                user_input = self.session.prompt(prompt,
                                                 style=self.style,
                                                 completer=self.completer,
                                                 complete_while_typing=True,
                                                 bottom_toolbar=toolbar_to_use)
            except (EOFError, KeyboardInterrupt):
                print("\nINFO: you pressed CTRL-C! Exiting gracefully...\n")
                sys.exit()
            
            last_executed_command = user_input
            if user_input == 're-prompt' or user_input is None or user_input == '':
                user_input = ''
                continue

            api_type = user_input.split(' ')[0]

            if api_type.lower() != self.prefix:
                if api_type.lower() in self.CLOUD_PROVIDERS:
                    self.set_parser_and_completer(api_type.lower())

            user_input = re.sub(r'[-]{3,}', '--', user_input)
            if user_input == "clear" or user_input == 'c':
                click.clear()
            elif user_input == "exit" or user_input == 'e':
                user_input = 'exit'
                sys.exit()
            elif user_input == "help" or user_input == 'h':
                getLayout(with_help=True)
                continue

            processed_input = self.process_user_input(user_input)

            if processed_input is None or processed_input == 're-prompt':
                continue

            if processed_input and processed_input.strip():
                last_executed_status = self.execute_command(processed_input)
