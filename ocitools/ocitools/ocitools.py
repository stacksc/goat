#!/usr/bin/env python3
import sys, click
from toolbox.logger import Log
from .iam import iam
from .oss import oss
from .dbs import dbs
from .regions import regions
from .compute import compute
from .ocicli_wrapper import cli
from .ocitools_show import show
from toolbox import misc
from toolbox.misc import debug
from .iam import get_latest_profile
from toolbox.click_complete import complete_oci_regions

MESSAGE="OCI CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group('oci', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'profile_name', help='profile name to use when working with ocitools', required=False, default=get_latest_profile())
@click.option('-r', '--region', 'region', help='region name to use when working with ocitools', required=False, type=str, shell_complete=complete_oci_regions, default='us-ashburn-1')
@click.pass_context
def CLI(ctx, profile_name, region):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile_name
    ctx.obj['REGION'] = region
    Log.setup('ocitools', int(debug))
    pass
    
CLI.add_command(cli)
CLI.add_command(compute)
CLI.add_command(dbs)
CLI.add_command(iam)
CLI.add_command(oss)
CLI.add_command(regions)
CLI.add_command(show)

if __name__ == "__main__":
    cli(ctx)
