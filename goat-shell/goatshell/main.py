#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, unicode_literals
from goatshell.goatshell import Goatshell
from goatshell.completer import GoatCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.application import Application
from goatshell.style import styles
from toolbox.misc import get_corrupt_provider_files, get_save_path
import os

from goatshell.parser import Parser  # Import the Parser class from the appropriate location
from goatshell.completer import GoatCompleter  # Import the GoatCompleter class from the appropriate location

def startup_check():
    corrupt_providers = get_corrupt_provider_files()

    if corrupt_providers:
        providers = ', '.join(corrupt_providers.keys())
        paths = "\n         ".join(corrupt_providers.values())

        warning_message = f"Corrupt custom JSON files detected for the following providers: {providers}"
        warning_message += f"\n         Consider removing or updating files here:\n         {paths}"
        return warning_message
    return None

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
    goatshell = Goatshell(app, completer, parser) # first init so we have access to our variables

    # startup check for json health
    warning_message = startup_check()

    # setup our initial variables
    last_command = status_text = ""

    # create the custom toolbar with a warning if we have health issues
    if warning_message:
        toolbar_content = goatshell.create_toolbar(last_command, status_text, warning_message)
    else:
        toolbar_content = goatshell.create_toolbar(last_command, status_text)  # Use default toolbar if no warning

    goatshell.toolbar_content = toolbar_content
    
    # run the cli
    goatshell.run_cli()

if __name__ == '__main__':
    cli()

