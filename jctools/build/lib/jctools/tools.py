#!/usr/bin/env python3

import os, click
from toolbox.logger import Log
from .start import start
from .stop import stop
from toolbox import misc
from configstore.configstore import Config

os.environ['NCURSES_NO_UTF8_ACS'] = "1"
CONFIG = Config('jctools')
MESSAGE="VMware JC CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + 'N/A' + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'user_profile', help='user profile for FLY operations', required=False, default='default')
@click.pass_context
def cli(ctx, debug, user_profile):
    ctx.ensure_object(dict)
    if user_profile is not None:
        try:
            ctx.obj['profile'] = user_profile
        except:
            pass
    Log.setup('flytools', int(debug))
    pass
    
cli.add_command(start)
cli.add_command(stop)

if __name__ == "__main__":
    cli(ctx)
