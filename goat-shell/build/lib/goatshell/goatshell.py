from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import to_formatted_text, HTML

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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Global variables
global vi_mode_enabled
current_service = 'oci'       # You can set it to 'aws' if you prefer AWS mode initially
os.environ['AWS_PAGER'] = ''  # Disable paging in AWS by default
vi_mode_enabled = False       # Default vi mode to false on start up

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

# Function to save VI mode setting
def save_vi_mode_setting():
    global vi_mode_enabled
    shell_dir = os.path.expanduser("~/goat/shell/")
    if not os.path.exists(shell_dir):
        os.makedirs(shell_dir)
    config = configparser.ConfigParser()
    config['Settings'] = {'vi_mode_enabled': str(vi_mode_enabled)}
    with open(shell_dir + 'config.ini', 'w') as configfile:
        config.write(configfile)

# Function to load VI mode setting from a configuration file
def load_vi_mode_setting():
    global vi_mode_enabled
    shell_dir = os.path.expanduser("~/goat/shell/")
    config = configparser.ConfigParser()
    try:
        config.read(shell_dir + 'config.ini')
        vi_mode_enabled = config.getboolean('Settings', 'vi_mode_enabled')
    except (configparser.NoSectionError, configparser.NoOptionError, FileNotFoundError):
        # Handle exceptions or file not found gracefully
        pass
    return vi_mode_enabled

# Load the VI mode setting when the script starts
vi_mode_enabled = load_vi_mode_setting()

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

        @self.add(Keys.F10)
        def handle_f10(event):
            self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F9)
        def handle_f9(event):
            self.goatshell_instance.toggle_vi_mode()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F8)
        def handle_f8(event):
            goatshell_instance.switch_to_next_provider()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

# Define the main Goatshell class
class Goatshell(object):
    CLOUD_PROVIDERS = ['aws', 'oci', 'ibmcloud', 'gcloud', 'goat', 'az', 'aliyun']

    def __init__(self, app, completer, parser):
        getLayout()
        self.vi_mode_enabled = load_vi_mode_setting()
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
        self.update_parser_and_completer(current_service)

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

    def update_parser_and_completer(self, api_type):
        self.prefix = api_type.lower()  # Set prefix
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{api_type}.json')
        self.parser = Parser(json_path, api_type)  # Reset parser
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
        save_vi_mode_setting()
        self.session = DynamicPromptSession(vi_mode_enabled=self.vi_mode_enabled, style=self.style, history=self.history, auto_suggest=AutoSuggestFromHistory(),
                                           completer=self.completer, complete_while_typing=True,
                                           enable_history_search=True, key_bindings=self.key_bindings)

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

    def create_toolbar(self, last_executed_command, status_text=""):
        self.upper_profile = self.profile.upper()
        self.upper_prefix = self.prefix.upper()
        vi_mode_text = "ON" if self.vi_mode_enabled else "OFF"

        toolbar_html = f'<b>F8</b> Cloud: <u>{self.upper_prefix}</u>   <b>F9</b> VIM {vi_mode_text}   <b>F10</b> Profile: <u>{self.upper_profile}</u>'
        if status_text == "failure":
            toolbar_html += f' | Last Executed: {status_text} => {last_executed_command}'
        else:
            toolbar_html += f' | Last Executed: {last_executed_command}'

        toolbar_content = to_formatted_text(HTML(toolbar_html))

        return toolbar_content

    def set_parser_and_completer(self, api_type):
        self.prefix = api_type.lower()  # Set prefix
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{api_type}.json')
        self.parser = Parser(json_path, api_type)  # Reset parser
        self.completer = GoatCompleter(self.parser)  # Reset completer
        self.session.completer = self.completer  # Reset session completer

    def process_user_input(self, user_input):
        user_input = user_input.strip()
      
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
            
        if user_input.startswith("!"):
            return user_input[1:]

        if self.prefix not in [self.prefix, 'oci']:
            return self.handle_non_provider_input(user_input)

        return self.handle_non_provider_input(user_input)

    def handle_non_provider_input(self, user_input):
        tokens = user_input.split(' ')
        first_token = tokens[0].lower()

        if first_token not in Goatshell.CLOUD_PROVIDERS and first_token not in ['help', 'h', 'c', 'clear', 'e', 'exit']:
            print("INFO: please select a cloud provider as the first command, or precede OS commands with an !")
            return ''

        return user_input

    def process_oci_input(self, user_input, first_token, last_token, last_but_one_token):
        if self.profile not in self.oci_profiles:
            self.profile = self.get_profile(first_token.lower())

        if last_but_one_token in ['--compartment-id', '--tenancy-id'] and not last_token.startswith('ocid'):
            try:
                OCID = self.get_account_or_tenancy(self.profile)
                user_input += f' {OCID}'
            except:
                pass

        if last_but_one_token == '--user-id' and not last_token.startswith('ocid'):
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
                user_input = self.session.prompt(prompt,
                                                 style=self.style,
                                                 completer=self.completer,
                                                 complete_while_typing=True,
                                                 bottom_toolbar=self.create_toolbar(last_executed_command, last_executed_status))
            except (EOFError, KeyboardInterrupt):
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
           
