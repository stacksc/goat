#!/usr/bin/env python3
import sys, click
from toolbox.logger import Log
from .iam import iam
from .ocicli_wrapper import cli
from .ocitools_show import show
from toolbox import misc
from toolbox.misc import debug
from .iam import get_latest_profile

MESSAGE="OCI CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group('aws', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'profile_name', help='profile name to use when working with ocitools', required=False, default=get_latest_profile())
@click.pass_context
def CLI(ctx, profile_name):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile_name
    Log.setup('ocitools', int(debug))
    pass
    
CLI.add_command(iam)
#CLI.add_command(s3)
#CLI.add_command(ec2)
#CLI.add_command(rds)
CLI.add_command(cli)
CLI.add_command(show)

if __name__ == "__main__":
    cli(ctx)
