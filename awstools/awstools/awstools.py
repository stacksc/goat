#!/usr/bin/env python3
import sys, click
from toolbox.logger import Log
from .s3 import s3
from .iam import iam
from .ec2 import ec2
from .rds import rds
from .awscli_wrapper import cli
from .awstools_show import show
from toolbox import misc
from toolbox.click_complete import complete_aws_regions, complete_aws_profiles
from toolbox.misc import debug
from .iam import get_latest_profile
from .iam_nongc import update_latest_profile

MESSAGE="AWS CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group('aws', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'aws_profile_name', help='profile name to use when working with awstools', required=False, default=get_latest_profile())
@click.option('-r', '--region', 'aws_region_name', help='region name to use when working with awstools', required=False, type=str, shell_complete=complete_aws_regions, default='us-east-1')
@click.option('-t', '--toggle', 'toggle', help='toggle default profile to use when working with awstools', required=False, type=str, shell_complete=complete_aws_profiles, default=get_latest_profile())
@click.pass_context
def CLI(ctx, aws_profile_name, aws_region_name, toggle):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = aws_profile_name
    ctx.obj['REGION'] = aws_region_name
    if toggle:
        if toggle != get_latest_profile(): 
            update_latest_profile(toggle)
            exit()
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
