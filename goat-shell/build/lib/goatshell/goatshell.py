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
from pygments.token import Token
from .toolbar import create_toolbar

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Global variables
global vi_mode_enabled, safety_mode_enabled
current_service = 'oci'       # You can set it to 'aws' if you prefer AWS mode initially
os.environ['AWS_PAGER'] = ''  # Disable paging in AWS by default
vi_mode_enabled = False       # Default vi mode to false on start up
safety_mode_enabled = False   # Default safety mode to false on start up

# Function to print instructions
def printInstructions():
    instructions = """
    Auto-Completion Instructions:
    ----------------------------
    1. To trigger auto-completion, start with TAB or type the beginning of a command or option and press Tab.
    2. Auto-completion will suggest available commands, options, and arguments based on your input.
    3. Use the arrow keys or Tab to navigate through the suggestions.
    4. Press Enter to accept a suggestion or Esc to cancel.
    5. If an option requires a value, use --option=value instead of --option value.
    6. The prompt will change dynamically based on cloud provider interaction.
    """
    print(instructions)

def save_setting(setting_key, setting_value):
    """Generic function to save a setting to config.ini."""
    shell_dir = os.path.expanduser("~/goat/shell/")
    if not os.path.exists(shell_dir):
        os.makedirs(shell_dir)

    config_path = os.path.join(shell_dir, 'config.ini')
    config = configparser.ConfigParser()

    # Load existing settings if they exist
    if os.path.exists(config_path):
        config.read(config_path)

    if 'Settings' not in config:
        config['Settings'] = {}

    config['Settings'][setting_key] = str(setting_value)

    with open(config_path, 'w') as configfile:
        config.write(configfile)

def load_setting(setting_key, default_value=None):
    """Generic function to load a setting from config.ini."""
    shell_dir = os.path.expanduser("~/goat/shell/")
    config_path = os.path.join(shell_dir, 'config.ini')
    config = configparser.ConfigParser()

    if not os.path.exists(config_path):
        return default_value

    config.read(config_path)

    if 'Settings' in config and setting_key in config['Settings']:
        value = config['Settings'][setting_key]
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        else:
            return value

    return default_value

# Define a custom PromptSession class
class DynamicPromptSession(PromptSession):
    def __init__(self, vi_mode_enabled=True, *args, **kwargs):
        self.vi_mode_enabled = vi_mode_enabled
        super().__init__(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        # Set the 'vi_mode' parameter based on 'vi_mode_enabled'
        kwargs['vi_mode'] = self.vi_mode_enabled
        return super().prompt(*args, **kwargs)

# Define key bindings class
class CustomKeyBindings(KeyBindings):
    def __init__(self, app, goatshell_instance):
        super().__init__()
        self.app = app  # Store the Application reference
        self.goatshell_instance = goatshell_instance

        @self.add(Keys.F8)
        def handle_f8(event):
            goatshell_instance.switch_to_next_provider()
            self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F9)
        def handle_f9(event):
            self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F10)
        def handle_f10(event):
            self.goatshell_instance.toggle_vi_mode()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F12)
        def handle_f12(event):
            self.goatshell_instance.toggle_safety_mode()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.


# Define the main Goatshell class
class Goatshell(object):
    CLOUD_PROVIDERS = ['aws', 'oci', 'ibmcloud', 'gcloud', 'goat', 'az', 'aliyun', 'ovhai']

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
        self.profile = self.init_profile()
        self.key_bindings = CustomKeyBindings(self.app, self)
        self.init_history()
        self.session = self.init_session()
        self.set_parser_and_completer(current_service)
        self.initial_warning_displayed = False

    def load_vi_mode_setting(self):
        """Load the VI mode setting."""
        return load_setting('vi_mode_enabled', default_value=False)
    
    def load_safety_mode_setting(self):
        """Load the SAFETY mode setting."""
        return load_setting('safety_mode_enabled', default_value=False)

    def save_vi_mode_setting(self):
        """Save the VI mode setting."""
        save_setting('vi_mode_enabled', self.vi_mode_enabled)
    
    def save_safety_mode_setting(self):
        """Save the safety mode setting."""
        save_setting('safety_mode_enabled', self.safety_mode_enabled)

    def init_profile(self):
        self.aws_index = 0
        self.oci_index = 0
        profile = 'DEFAULT'  # Initial value before getting profile
        return self.get_profile(self.prefix)  # update the profile

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
        self.completer = GoatCompleter(self.parser)  # Reset completer
        self.session.completer = self.completer  # Reset session completer
    
    def switch_to_next_provider(self):
        global current_service
        current_idx = self.CLOUD_PROVIDERS.index(current_service)
        
        for _ in range(len(self.CLOUD_PROVIDERS)):  # At most, loop through all providers once
            next_idx = (current_idx + 1) % len(self.CLOUD_PROVIDERS)
            next_service = self.CLOUD_PROVIDERS[next_idx]
        
            if misc.is_command_available(next_service):
                current_service = next_service
                self.prefix = next_service  # Update the instance attribute
                self.set_parser_and_completer(next_service)
                break
        
            current_idx = next_idx
        else:  # This block runs if the loop completed without finding an available command
            # Handle the case where none of the commands are available.
            # This can be an error message, fallback, etc.
            print(f"None of the providers are available.")
    
    def toggle_vi_mode(self):
        self.vi_mode_enabled = not self.vi_mode_enabled
        self.save_vi_mode_setting()
        self.session = DynamicPromptSession(vi_mode_enabled=self.vi_mode_enabled, style=self.style, history=self.history, auto_suggest=AutoSuggestFromHistory(),
                                           completer=self.completer, complete_while_typing=True,
                                           enable_history_search=True, key_bindings=self.key_bindings)

    def toggle_safety_mode(self):
        self.safety_mode_enabled = not self.safety_mode_enabled
        self.save_safety_mode_setting()

    def get_account_or_tenancy(self, profile):
        if self.prefix == 'oci':
            # Label as account for variable consistency and get the OCID
            account = misc.get_oci_tenant(profile_name=profile).id
        elif self.prefix == 'aws':
            account = misc.get_aws_account(profile_name=profile)
        else:
            return 'UNKNOWN'
        return account

    def get_profile(self, mode):
        if mode == 'aws':
            if self.aws_profiles:
                if self.profile in self.aws_profiles:
                    self.aws_index = self.aws_profiles.index(self.profile)
                self.aws_index = (self.aws_index + 1) % len(self.aws_profiles)
                self.profile = self.aws_profiles[self.aws_index]
            else:
                self.profile = 'DEFAULT'
        elif mode == 'oci':
            if self.oci_profiles:
                if self.profile in self.oci_profiles:
                    self.oci_index = self.oci_profiles.index(self.profile)
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
    
    def process_user_input(self, user_input):
        user_input = user_input.strip()
        tokens = user_input.split(' ')
        first_token = tokens[0].lower()
      
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
        elif user_input.startswith("cd "):
            path = user_input.split(" ", 1)[1]
            # expand any "~" to the users home directory
            path = os.path.expanduser(path)
            try:
                os.chdir(path)
            except Exception as e:
                print(f"Error: {e}")
            return ""

        if first_token not in Goatshell.CLOUD_PROVIDERS:
            return self.handle_non_provider_input(user_input)

        return self.handle_provider_input(user_input)

    def update_profile_for_provider(self, provider):
        if provider == 'aws':
            self.aws_profiles = misc.read_aws_profiles()
            self.profile = self.get_profile('aws')
        elif provider == 'oci':
            self.oci_profiles = misc.read_oci_profiles()
            self.profile = self.get_profile('oci')

    def handle_non_provider_input(self, user_input):
        tokens = user_input.split(' ')
        first_token = tokens[0].lower()

        if first_token in Goatshell.CLOUD_PROVIDERS or first_token in ['help', 'h', 'c', 'clear', 'e', 'exit']:
            return user_input
        elif self.safety_mode_enabled:  # safe mode
            print("INFO: OS commands are currently blocked due to safety mode. Please disable safety mode [F12] to execute OS commands.")
            return ''
        else:
            return user_input

    def handle_provider_input(self, user_input):
        tokens = user_input.split(' ')
        first_token = tokens[0]
        last_token = tokens[-1]
        last_but_one_token = tokens[-2] if len(tokens) > 1 else None

        if self.prefix == 'aws':
            return self.process_aws_input(user_input, first_token, last_token, last_but_one_token)
        elif self.prefix == 'oci':
            return self.process_oci_input(user_input, first_token, last_token, last_but_one_token)
        return user_input

    def process_oci_input(self, user_input, first_token, last_token, last_but_one_token):
        if self.profile not in self.oci_profiles:
            self.profile = self.get_profile(first_token.lower())

        if last_token in ['--compartment-id', '--tenancy-id'] and not last_token.startswith('ocid'):
            try:
                OCID = self.get_account_or_tenancy(self.profile)
                user_input += f' {OCID}'
            except:
                pass

        if last_token == '--user-id' and not last_token.startswith('ocid'):
            try:
                OCID = misc.get_oci_user(self.profile)
                user_input += f' {OCID}'
            except:
                pass

        return user_input

    def process_aws_input(self, user_input, first_token, last_token, last_but_one_token):
        if self.profile not in self.aws_profiles:
            self.profile = self.get_profile(first_token.lower())

        if last_but_one_token == '--user-name' and not last_token:
            try:
                USER = misc.get_aws_user(self.profile)
                user_input += f' {USER}'
            except:
                pass

        return user_input

    def get_current_context(self):
        return {
            'cloud_provider': self.prefix,
            'profile': self.profile
        }

    def generate_prompt(self):
        context = self.get_current_context()
        return HTML(f'[<b><u>{context["cloud_provider"]}</u></b>:<b><u>{context["profile"]}</u></b>]> ')

    def execute_command(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
    
        # If the return code is 0, it means success. Otherwise, it's a failure.
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
            if user_input == 're-prompt':
                user_input = ''
                continue

            api_type = user_input.split(' ')[0]

            if api_type.lower() != self.prefix:
                if api_type.lower() in self.CLOUD_PROVIDERS:
                    self.set_parser_and_completer(api_type.lower())

            user_input = re.sub(r'[-]{3,}', '--', user_input)
            if user_input == "clear" or user_input == 'c':
                user_input = 'clear'
                click.clear()
            elif user_input == "exit" or user_input == 'e':
                user_input = 'exit'
                sys.exit()
            elif user_input == "help" or user_input == 'h':
                getLayout()
                printInstructions()
                continue

            user_input = self.process_user_input(user_input)
            last_executed_status = self.execute_command(user_input)
           
