#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, unicode_literals
from goatshell.goatshell import Goatshell
from goatshell.completer import GoatCompleter
import os

from goatshell.parser import Parser  # Import the Parser class from the appropriate location
from goatshell.completer import GoatCompleter  # Import the GoatCompleter class from the appropriate location

def cli():
    oci_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/oci.json')
    parser = Parser(oci_json_path)  # Create an instance of the Parser class
    completer = GoatCompleter(parser)  # Create a GoatCompleter instance with the parser
    goat_shell = Goatshell(completer=completer, parser=parser)  # Pass the completer instance to Goatshell
    goat_shell.run_cli()

if __name__ == '__main__':
    cli()
