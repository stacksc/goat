#!/usr/bin/env python3
import sys, click
from toolbox.logger import Log
from .iam import iam
from .compartment import compartment
from .oss import oss
from .dbs import dbs
from .vault import vault
from .regions import regions
from .compute import compute
from .ocicli_wrapper import cli
from .ocitools_show import show
from .oci_config import OCIconfig
from toolbox import misc
from toolbox.misc import debug
from .iam import get_latest_profile, get_latest_region
from .iam_nongc import update_latest_profile, force_cache, cache_all_hack
from toolbox.click_complete import complete_oci_regions, complete_oci_profiles

MESSAGE="OCI CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET + " Region: " + misc.GREEN + misc.UNDERLINE + get_latest_region(get_latest_profile()).upper() + misc.RESET

@click.group('oci', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'profile_name', help='profile name to use when working with ocitools', required=False, default=get_latest_profile(), shell_complete=complete_oci_profiles)
@click.option('-r', '--region', 'region', help='region name to use when working with ocitools', required=False, type=str, shell_complete=complete_oci_regions, default=None)
@click.option('-c', '--cache', help="refresh all cache for region and tenant", is_flag=True, required=False, default=False, show_default=True)
@click.pass_context
def CLI(ctx, profile_name, region, cache):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile_name
    ctx.obj['REGION'] = region
    if cache is True:
        force_cache(profile_name, region)
        sys.exit()
    if region != get_latest_region(profile_name) and region != None:
        CONFIG = OCIconfig()
        CONFIG.update_oci_config('config', profile_name, 'region', region)
        cache_all_hack(profile_name, region)
    if profile_name != get_latest_profile():
        update_latest_profile(profile_name)
        cache_all_hack(profile_name, region)
    Log.setup('ocitools', int(debug))
    pass
    
CLI.add_command(cli)
CLI.add_command(compute)
CLI.add_command(compartment)
CLI.add_command(dbs)
CLI.add_command(iam)
CLI.add_command(oss)
CLI.add_command(regions)
CLI.add_command(show)
CLI.add_command(vault)

if __name__ == "__main__":
    cli(ctx)
