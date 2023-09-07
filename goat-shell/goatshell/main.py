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

    oci_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/oci.json')
    parser = Parser(oci_json_path)  # Create a Parser instance
    completer = GoatCompleter(parser)  # Create a GoatCompleter instance with the parser
    app = Application()
    goatshell = Goatshell(app, completer, parser)
    goatshell.run_cli()

if __name__ == '__main__':
    cli()
