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
from ocitools.iam import get_latest_profile  
from toolbox import misc  
from ocitools.oci_config import OCIconfig  
from goatshell.style import styles_dict 
from goatshell.completer import GoatCompleter 
from goatshell.parser import Parser  
from goatshell.ui import getLayout  

logger = logging.getLogger(__name__)
current_service = 'oci'  # You can set it to 'aws' if you prefer AWS mode initially
os.environ['AWS_PAGER'] = ''

# Define key bindings class
class CustomKeyBindings(KeyBindings):
    def __init__(self, app):
        super().__init__()

        @self.add(Keys.F10)
        def handle_f10(event):
            sys.exit()

        @self.add(Keys.F9)  # Use F9 key for toggling
        def handle_f9(event):
            global current_service
            current_service = 'aws' if current_service == 'oci' else 'oci'
            app.set_parser_and_completer(current_service)

# Define the main Goatshell class
class Goatshell(object):
    def __init__(self, app, completer, parser):
        getLayout()
        self.style = Style.from_dict(styles_dict)
        self.app = app
        self.completer = completer
        self.prefix = 'oci'

        self.key_bindings = CustomKeyBindings(self)
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

    def toggle_service(self, event):
        global current_service  # Declare current_service as a global variable
        if current_service == 'oci':
            current_service = 'aws'
        else:
            current_service = 'oci'

        self.prefix = current_service
        self.set_parser_and_completer(current_service)

    def get_service_info(self):
        use_aws = True  # or False
        if use_aws:
            return 'aws', 'data/aws.json'
        else:
            return 'oci', 'data/oci.json'

    def create_toolbar(self):
        return HTML(
            'Use [Tab][Tab] for autocompletion <b>F9</b> Toggle Provider <b>F10</b> Quit'
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

            api_type = user_input.split(' ')[0]

            if api_type.lower() != self.prefix:  # If a different prefix is detected
                if api_type.lower() in ['oci', 'aws']:
                    self.set_parser_and_completer(api_type.lower())

            user_input = re.sub(r'[-]{3,}', '--', user_input)
            if user_input == "clear":
                click.clear()
            elif user_input == "exit":
                sys.exit()

            if user_input.startswith("!"):
                user_input = user_input[1:]

            if user_input:
                if '--profile' not in user_input:
                    user_input = user_input + ' --profile ' + get_latest_profile()
                if '-o' in user_input and 'json' in user_input:
                    user_input += ' | pygmentize -l json'
                p = subprocess.Popen(user_input, shell=True)
                p.communicate()

if __name__ == '__main__':
    service = 'oci'

    # Construct the path to the JSON file based on the selected service
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{service}.json')

    # Create a Parser instance
    parser = Parser(json_path, service)

    # Create a GoatCompleter instance with the parser
    completer = GoatCompleter(parser)

    # Initialize and run Goatshell
    app = Application()
    goatshell = Goatshell(app, completer, parser)
    goatshell.run_cli()
