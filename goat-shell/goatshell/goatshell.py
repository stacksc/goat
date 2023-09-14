from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import Application, PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
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
from . import misc as misc
from goatshell.style import styles_dict 
from goatshell.completer import GoatCompleter 
from goatshell.parser import Parser  
from goatshell.ui import getLayout  

logger = logging.getLogger(__name__)
current_service = 'oci'  # You can set it to 'aws' if you prefer AWS mode initially
os.environ['AWS_PAGER'] = ''

# Define key bindings class
class CustomKeyBindings(KeyBindings):
    def __init__(self, app, goatshell_instance):
        super().__init__()
        self.app = app  # Store the Application reference
        self.goatshell_instance = goatshell_instance

        @self.add(Keys.F12)
        def handle_f10(event):
            sys.exit()

        @self.add(Keys.F10)
        def handle_f12(event):
            self.profile = self.goatshell_instance.get_profile(self.goatshell_instance.prefix)  # Access the get_profile method of Goatshell
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F8)
        def handle_f8(event):
            getLayout()
            self.app.invalidate()
            event.app.exit(result='re-prompt')  # Signal to reprompt.

        @self.add(Keys.F9)  # Use F9 key for toggling
        def handle_f9(event):
            global current_service
            if current_service == 'aws':
                current_service = 'oci'
            elif current_service == 'oci':
                current_service = 'gcloud'
            elif current_service == 'gcloud':
                current_service = 'az'
            elif current_service == 'az':
                current_service = 'goat'
            else:
                current_service = 'aws'
            app.set_parser_and_completer(current_service)
            app.current_input = None  # Reset current input and retrigger prompt
        
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
        self.profile = self.get_profile(self.prefix)
        self.key_bindings = CustomKeyBindings(self.app, self)
        self.key_bindings.add(Keys.F9)(self.toggle_service)

        shell_dir = os.path.expanduser("~/goat/shell/")
        self.history = InMemoryHistory()
        if not os.path.exists(shell_dir):
            os.makedirs(shell_dir)
        self.session = PromptSession(history=self.history, auto_suggest=AutoSuggestFromHistory(),
                                     completer=self.completer, complete_while_typing=True,
                                     enable_history_search=True, vi_mode=True,
                                     key_bindings=self.key_bindings)

        root_name, json_path = self.get_service_info()
        self.parser = Parser(json_path, root_name)
   
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

    def toggle_service(self, event):
        global current_service  # Declare current_service as a global variable
        if current_service == 'aws':
            current_service = 'oci'
        elif current_service == 'oci':
            current_service = 'gcloud'
        elif current_service == 'gcloud':
            current_service = 'az'
        elif current_service == 'az':
            current_service = 'goat'
        else:
            current_service = 'aws'

        # re-prompt hack
        self.prefix = current_service
        self.set_parser_and_completer(current_service)
        os.system('clear')
        getLayout()
        self.app.invalidate()
        event.app.exit(result='re-prompt')  # signal to reprompt.

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
            return 'az', json_path
        else:
            return 'aws', json_path
    
    def create_toolbar(self):
        self.upper_profile = self.profile.upper()
        self.upper_prefix = self.prefix.upper()
        return HTML(
            f'<b>F8</b> Usage <b>F9</b> Toggle Provider: {self.upper_prefix} <b>F10</b> Toggle Profile: {self.upper_profile} <b>F12</b> Quit'
        )

    def set_parser_and_completer(self, api_type):
        self.prefix = api_type.lower()  # Set prefix
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{api_type}.json')
        self.parser = Parser(json_path, api_type)  # Reset parser
        self.completer = GoatCompleter(self.parser)  # Reset completer
        self.session.completer = self.completer  # Reset session completer

    def run_cli(self):
        global current_service
        logger.info("running goat event loop")
        while True:
            try:
                user_input = self.session.prompt(f'{current_service}> ',
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

            if api_type.lower() != self.prefix:  # If a different prefix is detected
                if api_type.lower() in ['oci', 'aws', 'gcloud', 'az', 'goat']:
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
                continue

            if user_input.startswith("!"):
                user_input = user_input[1:]
            else:
                if user_input:
                    if api_type.lower() == 'oci':
                        if '--compartment-id' in user_input or '--tenancy-id' in user_input and 'ocid' not in user_input:
                            try:
                                OCID = self.get_account_or_tenancy(self.profile)
                                user_input += f' {OCID}'
                            except:
                                pass
                        if '--user-id' in user_input and 'ocid' not in user_input:
                            try:
                                OCID = misc.get_oci_user(self.profile)
                                user_input += f' {OCID}'
                            except:
                                pass
                    if api_type.lower() not in ['gcloud','az','goat'] and '--profile' not in user_input:
                        user_input = user_input + ' --profile ' + self.profile
                    if '-o' in user_input and 'json' in user_input:
                        user_input += ' | pygmentize -l json'
            p = subprocess.Popen(user_input, shell=True)
            p.communicate()

