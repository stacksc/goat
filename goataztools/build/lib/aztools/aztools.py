#!/usr/bin/env python3
import sys, click
from toolbox.logger import Log
from toolbox import misc
from toolbox.misc import debug
from .extract import extract

MESSAGE="AZ CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + "DEFAULT" + misc.RESET + " Region: " + misc.GREEN + misc.UNDERLINE + 'USWEST2' + misc.RESET

@click.group('az', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.pass_context
def CLI(ctx):
    ctx.ensure_object(dict)
    Log.setup('aztools', int(debug))
    pass
    
CLI.add_command(extract)

if __name__ == "__main__":
    cli(ctx)
