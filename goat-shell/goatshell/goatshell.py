from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import Application, PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

import time
import os
import sys
import subprocess
import re
import click
import logging
import configparser
from . import misc as misc
from goatshell.style import styles_dict 
from goatshell.completer import GoatCompleter 
from goatshell.parser import Parser  
from goatshell.ui import getLayout  

logger = logging.getLogger(__name__)
current_service = 'oci'  # You can set it to 'aws' if you prefer AWS mode initially
os.environ['AWS_PAGER'] = ''

def printInstructions():
    instructions = """
    Auto-Completion Instructions:
    ----------------------------
    1. To trigger auto-completion, start with TAB or type the beginning of a command or option and press Tab.
    2. Auto-completion will suggest available commands, options, and arguments based on your input.
    3. Use the arrow keys or Tab to navigate through the suggestions.
    4. Press Enter to accept a suggestion or Esc to cancel.
    5. If an option requires a value, use --option=value instead of --option value.

    INFO: resource completion coming soon!
    """
    print(instructions)

def get_region_for_oci_profile(profile_name):
    config_file = os.path.expanduser("~/.oci/config") # Path to the OCI CLI config file
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        # Check if the profile exists in the OCI config file
        if profile_name in config:
            if "region" in config[profile_name]:
                region = config[profile_name]["region"]
                return region

    return None

def get_region_for_aws_profile(profile_name):
    config_file = os.path.expanduser("~/.aws/config") # Path to the AWS CLI config file
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        # Check if the profile exists in the AWS config file
        if profile_name in config:
            if "region" in config[profile_name]:
                return config[profile_name]["region"]

    # if we get this far try the credentials file
    config_file = os.path.expanduser("~/.aws/credentials") # Path to the AWS CLI credentials file
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        # Check if the profile exists in the AWS config file
        if profile_name in config:
            if "region" in config[profile_name]:
                return config[profile_name]["region"]

    return None  # Profile or region not found

# Define key bindings class
class CustomKeyBindings(KeyBindings):
    def __init__(self, app, goatshell_instance):
        super().__init__()
        self.app = app  # Store the Application reference
        self.goatshell_instance = goatshell_instance

        @self.add(Keys.F12)
        def handle_f10(event):
            print("")
            sys.exit()

        @self.add(Keys.F10)
        def handle_f12(event):
            self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F9)
        def handle_f9(event):
            if self.goatshell_instance.prefix == 'oci':
                from ocitools.iam_nongc import force_cache
                self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
                region = get_region_for_oci_profile(self.profile)
            elif self.goatshell_instance.prefix == 'aws':
                from awstools.iam_nongc import force_cache
                self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
                region = get_region_for_aws_profile(self.profile)
            if region is not None:
                print()
                force_cache(self.profile, region)
                self.app.invalidate()
                event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F8)
        def handle_f8(event):
            getLayout()
            printInstructions()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

# Define the main Goatshell class
class Goatshell(object):
    def __init__(self, app, completer, parser):
        getLayout()
        self.style = Style.from_dict(styles_dict)
        self.app = app
        self.completer = completer
        self.prefix = 'oci'
        self.current_input = None
        self.aws_profiles = misc.read_aws_profiles()
        self.oci_profiles = misc.read_oci_profiles()
        self.aws_index = 0
        self.oci_index = 0
        self.profile = 'DEFAULT' # init this variable before we call the get_profile function
        self.profile = self.get_profile(self.prefix)
        self.key_bindings = CustomKeyBindings(self.app, self)
        shell_dir = os.path.expanduser("~/goat/shell/")
        if not os.path.exists(shell_dir):
            os.makedirs(shell_dir)
        try:
            self.history = FileHistory(os.path.join(shell_dir, "history"))
        except:
            self.history = InMemoryHistory()

        self.session = PromptSession(history=self.history, auto_suggest=AutoSuggestFromHistory(),
                                     completer=self.completer, complete_while_typing=True,
                                     enable_history_search=True, vi_mode=True,
                                     key_bindings=self.key_bindings)

        root_name, json_path = self.get_service_info()
        try:
            self.parser = Parser(json_path, root_name)
        except Exception as e:
            logger.info(f"Exception caught: {e}")
            logger.info(f"json_path = {json_path}, root_name = {root_name}")
   
    def get_account_or_tenancy(self, profile):
        if self.prefix == 'oci':
            # label as account for variable consistency and get the ocid
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

    def get_service_info(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{self.prefix}.json')
        global current_service  # Declare current_service as a global variable
        if current_service == 'aws':
            return 'aws', json_path
        elif current_service == 'oci':
            return 'oci', json_path
        elif current_service == 'gcloud':
            return 'gcloud', json_path
        elif current_service == 'az':
            return 'az', json_path
        elif current_service == 'goat':
            return 'goat', json_path
        elif current_service == 'aliyun':
            return 'aliyun', json_path
        elif current_service == 'ibmcloud':
            return 'ibmcloud', json_path
        else:
            return 'aws', json_path
    
    def create_toolbar(self):
        self.upper_profile = self.profile.upper()
        self.upper_prefix = self.prefix.upper()
        return HTML(
            f'Current Cloud: <u>{self.upper_prefix}</u>  <b>F8</b> Usage <b>F10</b> Toggle Profile: <u>{self.upper_profile}</u> <b>F12</b> Quit'
        )

    def set_parser_and_completer(self, api_type):
        self.prefix = api_type.lower()  # Set prefix
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{api_type}.json')
        self.parser = Parser(json_path, api_type)  # Reset parser
        self.completer = GoatCompleter(self.parser)  # Reset completer
        self.session.completer = self.completer  # Reset session completer

    def process_user_input(self, user_input):
        if user_input.startswith("!"):
            user_input = user_input[1:]
        else:
            tokens = user_input.split(' ')
            first_token = tokens[0]
            last_token = tokens[-1]
            last_but_one_token = tokens[-2] if len(tokens) > 1 else None
    
            if first_token.lower() == 'oci':
                user_input = self.process_oci_input(user_input, first_token, last_token, last_but_one_token)
    
            elif first_token.lower() == 'aws':
                user_input = self.process_aws_input(user_input, first_token, last_token, last_but_one_token)
    
            elif first_token.lower() in ['aws', 'oci'] and '--profile' not in user_input:
                user_input = user_input + ' --profile ' + self.profile
    
            if '-o' in user_input and 'json' in user_input:
                user_input += ' | pygmentize -l json'

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
    
    def run_cli(self):
        global current_service
        logger.info("running goat event loop")
        while True:
            try:
                user_input = self.session.prompt(f'goat> ',
                                                 style=self.style,
                                                 enable_history_search=True,
                                                 vi_mode=True,
                                                 complete_while_typing=True,
                                                 bottom_toolbar=self.create_toolbar())
            except (EOFError, KeyboardInterrupt):
                sys.exit()

            if user_input == 're-prompt':
                user_input = ''
                continue
            api_type = user_input.split(' ')[0]

            if api_type.lower() != self.prefix:
                if api_type.lower() in ['oci', 'aws', 'gcloud', 'az', 'goat', 'aliyun', 'ibmcloud']:
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
            p = subprocess.Popen(user_input, shell=True)
            p.communicate()

