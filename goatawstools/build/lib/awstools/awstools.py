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
from .iam import get_latest_profile, get_latest_region
from .iam_nongc import update_latest_profile, force_cache, cache_all_hack
from .aws_config import AWSconfig

MESSAGE="AWS CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET + " Region: " + misc.GREEN + misc.UNDERLINE + get_latest_region(get_latest_profile()).upper() + misc.RESET

@click.group('aws', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'aws_profile_name', help='profile name to use when working with awstools', required=False, default=get_latest_profile(), shell_complete=complete_aws_profiles)
@click.option('-r', '--region', 'aws_region_name', help='region name to use when working with awstools', required=False, type=str, shell_complete=complete_aws_regions, default=None)
@click.option('-c', '--cache', 'cache', help="refresh all cache for region and tenant", is_flag=True, required=False, default=False, show_default=True)
@click.pass_context
def CLI(ctx, aws_profile_name, aws_region_name, cache):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = aws_profile_name
    ctx.obj['REGION'] = aws_region_name
    if cache is True:
        force_cache(aws_profile_name, aws_region_name)
        sys.exit()
    if aws_region_name != get_latest_region(aws_profile_name) and aws_region_name != None:
        CONFIG = AWSconfig()
        CONFIG.update_aws_config('creds', aws_profile_name, 'region', aws_region_name)
        CONFIG.update_aws_config('config', aws_profile_name, 'region', aws_region_name)
        cache_all_hack(aws_profile_name, aws_region_name)
    if aws_profile_name != get_latest_profile():
        update_latest_profile(aws_profile_name)
        cache_all_hack(aws_profile_name, aws_region_name)
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
