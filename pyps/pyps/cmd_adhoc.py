#!/usr/bin/env python3

import click
from adhoc import adhoc
from adhoc.command import run_command
from toolbox.logger import Log
from toolbox.misc import set_terminal_width

@click.group(help="CLI for VMware Favorite Workflows", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
def adhoc():
    pass

@adhoc.command(help='run any external command or script(s) to chain as workflows', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-c', '--command', help='provide an external script or command to execute', required=True, type=str)

def command(command):
    Log.info(f" [+] {command}", output=True)
    Log.info(" [*] the following output was returned: ", output=True)
    RESPONSES = run_command(command)
    for RESPONSE in RESPONSES:
        print("\t" + RESPONSE, end='')

adhoc.add_command(command)
