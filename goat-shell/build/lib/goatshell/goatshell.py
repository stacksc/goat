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

# Define key bindings class
class CustomKeyBindings(KeyBindings):
    def __init__(self, app):
        super().__init__()

        @self.add(Keys.F9)
        def handle_f9(event):
            app.toggle_prompt_prefix()

        @self.add(Keys.F10)
        def handle_f10(event):
            sys.exit()

# Define the main Goatshell class
class Goatshell(object):
    def __init__(self, app, completer, parser):
        getLayout()
        self.style = Style.from_dict(styles_dict)
        self.prefix = "oci"  # Initial prefix
        self.app = app
        self.completer = completer
        self.c = 0

        self.key_bindings = CustomKeyBindings(self)

        shell_dir = os.path.expanduser("~/goat/shell/")
        self.history = InMemoryHistory()
        if not os.path.exists(shell_dir):
            os.makedirs(shell_dir)
        self.session = PromptSession(history=self.history, auto_suggest=AutoSuggestFromHistory(),
                                     completer=self.completer, complete_while_typing=True,
                                     enable_history_search=True, vi_mode=True,
                                     key_bindings=self.key_bindings)

        self.parser = parser

    def toggle_prompt_prefix(self):
        if self.prefix == 'oci':
            self.prefix = 'aws'
        else:
            self.prefix = 'oci'

    def create_toolbar(self):
        return HTML(
            'OCI [Tab][Tab] - autocompletion   <b>F9</b> Toggle OCI|AWS    <b>F10</b> Quit'
        )

    def run_cli(self):
        logger.info("running goat event loop")
        while True:
            try:
                user_input = self.session.prompt(f'{self.prefix}> ',
                                                 style=self.style,
                                                 enable_history_search=True,
                                                 vi_mode=True,
                                                 complete_while_typing=True,
                                                 bottom_toolbar=self.create_toolbar())
            except (EOFError, KeyboardInterrupt):
                sys.exit()

            user_input = self.add_prefix_if_missing(user_input, self.prefix)
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

    def add_prefix_if_missing(self, user_input, prefix="oci"):
        shell_commands = ["clear", "exit"]
        if not user_input.strip():
            return user_input

        if user_input.split()[0] not in shell_commands and not user_input.startswith(prefix):
            user_input = f"{prefix} {user_input}"

        return user_input

if __name__ == '__main__':
    oci_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/oci.json')
    parser = Parser(oci_json_path)  # Create a Parser instance
    completer = GoatCompleter(parser)  # Create a GoatCompleter instance with the parser
    app = Application()
    goatshell = Goatshell(app, completer, parser)
    goatshell.run_cli()
