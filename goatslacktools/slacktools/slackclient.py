#!/usr/bin/env python3

import argcomplete, shutil
from .auth import get_slackclient_config
from . import post, react, unpost, unreact, channel
from toolbox.logger import Log
import toolbox.argparse_mod as argparse
from toolbox.argparse_mod import MyFormatter

class Commands():
    def __init__(self):
        self.MAP = {}

    def setup_command(self, GROUP, NAME):
        WIDTH = max(80, shutil.get_terminal_size().columns - 2)
        formatter_class=lambda prog: MyFormatter(prog, max_help_position=40, width=WIDTH)
        MODULE_NAME = NAME.replace('-','_')
        SUBPARSER = GROUP.add_parser(NAME, help=globals()[MODULE_NAME].help, formatter_class=formatter_class)
        globals()[MODULE_NAME].setup_args(SUBPARSER)
        self.MAP.update({NAME: globals()[MODULE_NAME].main})

def init_parsers(COMMANDS):
    LINE='CLI client for Slack'
    PARSER = argparse.ArgumentParser(
        description=LINE, 
        allow_abbrev=True, 
        add_help=True, 
        conflict_handler='resolve'
    )
    PARSER.add_argument(
        "-d","--debug",
        help='debug level; 0 - no output, 1 - normal (default), 2 - verbose', 
        required=False,
        choices=['0','1','2'],
        default='1',
        dest='DEBUG',
    )
    PARSER.add_argument(
        "-c", "--config",
        help="Display the config of slackclient",
        required=False,
        default=False,
        action='store_true',
        dest='SHOW_CONFIG'
    )
    PARSER.add_argument(
        "-p", "--profile",
        help='name of the user profile to use',
        required=False,
        default='default',
        dest='PROFILE'
    )
    SUBPARSERS = PARSER.add_subparsers(dest="CMD", metavar='')
    CMDGROUP_MESSAGES = SUBPARSERS.add_parser_group("\ncommon slack actions include:")
    COMMANDS.setup_command(CMDGROUP_MESSAGES, "post")
    COMMANDS.setup_command(CMDGROUP_MESSAGES, "react")
    COMMANDS.setup_command(CMDGROUP_MESSAGES, "unpost")
    COMMANDS.setup_command(CMDGROUP_MESSAGES, "unreact")
    COMMANDS.setup_command(CMDGROUP_MESSAGES, "channel")
    argcomplete.autocomplete(PARSER)
    return PARSER.parse_args()

def cli():
    COMMANDS = Commands()
    PARSED_ARGS = init_parsers(COMMANDS)
    Log.setup('slacktools', int(PARSED_ARGS.DEBUG))
    if PARSED_ARGS.SHOW_CONFIG:
        get_slackclient_config()
    else:
        try:
            COMMANDS.MAP[PARSED_ARGS.CMD](PARSED_ARGS)
        except KeyError:
            Log.debug(f"No command detected")

if __name__ == "__main__":
    cli()
