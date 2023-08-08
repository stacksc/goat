#!/usr/bin/env python3
import sys, click
from toolbox.logger import Log
from .s3 import s3
from .iam import iam, iam_ingc
from .ec2 import ec2
from .rds import rds
from .awscli_wrapper import cli
from .awstools_show import show
from toolbox import misc
from toolbox.misc import debug
from .iam import get_latest_profile

MESSAGE="AWS CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group('aws', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-w', '--whoami', help="display the latest assumed profile for the CLI client", default=False, is_flag=True)
@click.option('-p', '--profile', 'aws_profile_name', help='profile name to use when working with awstools', required=False, default=get_latest_profile())
@click.pass_context
def CLI(ctx, whoami, aws_profile_name):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = aws_profile_name
    if whoami:
        if misc.detect_environment() == 'gc-prod':
            iam_ingc.get_latest_profile_data(ctx)
        sys.exit(0)
    Log.setup('awstools', int(debug))
    pass
    
CLI.add_command(iam)
CLI.add_command(s3)
CLI.add_command(ec2)
CLI.add_command(rds)
CLI.add_command(cli)
CLI.add_command(show)

if __name__ == "__main__":
    cli(ctx)
