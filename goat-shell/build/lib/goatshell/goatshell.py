from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
import os
import sys
import subprocess
import logging
import re
import click

from goatshell.style import styles_dict
from goatshell.completer import GoatCompleter
from goatshell.parser import Parser

logger = logging.getLogger(__name__)
registry = KeyBindings()
oci_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/oci.json')
parser = Parser(oci_json_path) # Create a Parser instance
completer = GoatCompleter(parser)  # Create a GoatCompleter instance with the parser

def add_prefix_if_missing(user_input, prefix="oci"):
    shell_commands = ["clear", "exit"]
    if not user_input.strip():
        return user_input

    if user_input.split()[0] not in shell_commands and not user_input.startswith(prefix):
        user_input = f"{prefix} {user_input}"

    return user_input

class Goatshell(object):

    @staticmethod
    def bottom_toolbar():
        SHORT_CUTS_TEXT = "oci [Tab][Tab] - autocompletion"
        return f'{SHORT_CUTS_TEXT}   [F10] Quit'

    def __init__(self, completer, parser, refresh_resources=True):
        self.style = Style.from_dict(styles_dict)
        shell_dir = os.path.expanduser("~/goat/shell/")
        self.history = InMemoryHistory()
        if not os.path.exists(shell_dir):
            os.makedirs(shell_dir)
        self.session = PromptSession(history=self.history, auto_suggest=AutoSuggestFromHistory(),
                                     completer=completer, complete_while_typing=True)
        self.parser = parser

    @registry.add_binding('f10')
    def _(event):
        sys.exit()

    def run_cli(self):
        logger.info("running goat event loop")
        while True:
            try:
                user_input = self.session.prompt('goat> ',
                                                 style=self.style,
                                                 enable_history_search=True,
                                                 vi_mode=True,
                                                 key_bindings=registry,
                                                 complete_while_typing=True,
                                                 bottom_toolbar=self.bottom_toolbar,
                                                 completer=completer)
            except (EOFError, KeyboardInterrupt):
                sys.exit()

            user_input = add_prefix_if_missing(user_input)
            user_input = re.sub(r'[-]{3,}', '--', user_input)
            if user_input == "clear":
                click.clear()
            elif user_input == "exit":
                sys.exit()

            if user_input.startswith("!"):
                user_input = user_input[1:]

            if user_input:
                if '-o' in user_input and 'json' in user_input:
                    user_input += ' | pygmentize -l json'
                p = subprocess.Popen(user_input, shell=True)
                p.communicate()

if __name__ == '__main__':
    oci_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/oci.json')
    parser = Parser(oci_json_path) # Create a Parser instance
    completer = GoatCompleter(parser)  # Create a GoatCompleter instance with the parser
    app = Goatshell(completer=completer, parser=parser)  # Pass both completer and parser instances to Goatshell
    app.run_cli()
