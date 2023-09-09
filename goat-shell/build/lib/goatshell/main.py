#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, unicode_literals
from goatshell.goatshell import Goatshell
from goatshell.completer import GoatCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.application import Application
from goatshell.style import styles_dict
import os

from goatshell.parser import Parser  # Import the Parser class from the appropriate location
from goatshell.completer import GoatCompleter  # Import the GoatCompleter class from the appropriate location

def cli():
    # Default to the 'oci' service
    service = 'oci'

    # Construct the path to the JSON file based on the selected service
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{service}.json')

    # Create a Parser instance
    parser = Parser(json_path, service)
    completer = GoatCompleter(parser)

    # Initialize and run Goatshell
    app = Application()
    goatshell = Goatshell(app, completer, parser)
    goatshell.run_cli()

if __name__ == '__main__':
    cli()

