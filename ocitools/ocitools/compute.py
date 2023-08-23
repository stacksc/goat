import click, os, gnureadline, csv
from toolbox.logger import Log
from .computeclient import MyComputeClient
from toolbox.menumaker import Menu
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile

CONFIG = Config('ocitools')

try: input = raw_input
except NameError: raw_input = input

@click.group('compute', invoke_without_command=True, help='compute to manage the instances and related configuration', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform compute actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def compute(ctx, menu):
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False

@compute.command(help='manually refresh compute cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('cache_type', required=False, default='all', type=click.Choice(['all', 'instances', 'public_ips', 'regions', 'auto']))
def refresh(ctx, cache_type):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _refresh(cache_type, profile_name, oci_region)

def _refresh(cache_type, profile_name, oci_region):
    try:    
        COMPUTE = get_compute_client(profile_name, oci_region, auto_refresh=False, cache_only=True)
        if cache_type == 'all':
            COMPUTE.refresh(profile_name)
        if cache_type == 'instances':
            COMPUTE.cache_instances(profile_name)
        if cache_type == 'public_ips':
            COMPUTE.cache_public_ips(profile_name)
        if cache_type == 'regions':
            COMPUTE.cache_regions(profile_name)
        if cache_type == 'auto':
            COMPUTE.auto_refresh(profile_name)
        return True
    except:
        return False

@compute.command(help='show the data stored in compute cache (instacnes, IPs, regions)', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('target', required=False, default='all', type=click.Choice(['all', 'instances', 'public_ips', 'regions', 'orphaned_ebs', 'orphaned_snaps']))
def show(ctx, target):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    if ctx.obj["MENU"] and target == "instances":
        CACHED_INSTANCES = {}
        DATA = []
        for PROFILE in CONFIG.PROFILES:
            if PROFILE == 'latest':
                continue
            if PROFILE == profile_name:
                COMPUTE = get_compute_client(profile_name, oci_region, auto_refresh=False, cache_only=True)
                RES = COMPUTE.show_cache(profile_name, oci_region, 'cached_instances', display=False)
                for data in RES:
                    NAME = data["display_name"].ljust(50)
                    IP = data["private_ips"].strip()
                    STATE = data["lifecycle_state"]
                    details = NAME + "\t" + IP + "\t" + STATE
                    DATA.append(details)
                break
        INPUT = 'Login Manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            IP = CHOICE[0].split("\t")[1]
            Log.info(f"you chose to SSH to {IP} which will be implemented later...")
    else:
        _show(target, profile_name, oci_region, display=True)

def _show(target, profile_name, oci_region, display):
    try:
        COMPUTE = get_compute_client(profile_name, oci_region, auto_refresh=False, cache_only=True)
        if target == 'instances' or target == 'all':
            COMPUTE.show_cache(profile_name, oci_region, 'cached_instances', display)
        if target == 'public_ips' or target == 'all':
            COMPUTE.show_cache(profile_name, oci_region, 'cached_public_ips', display)
        if target == 'regions' or target == 'all':
            COMPUTE.show_cache(profile_name, oci_region, 'cached_regions', display)
        return True
    except:
        return False

def get_compute_client(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = MyComputeClient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Compute Menu: {INPUT}'
    for data in DATA:
        COUNT = COUNT + 1
        RESULTS = []
        RESULTS.append(data)
        FINAL.append(RESULTS)
    SUBTITLE = f'showing {COUNT} available object(s)'
    JOINER = '\t\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, SUBTITLE)
    CHOICE = FINAL_MENU.display()
    return CHOICE

def get_region(ctx, profile_name):
    oci_region = ctx.obj['REGION']
    if not oci_region:
        COMPUTE = get_compute_client(profile_name)
        oci_region = COMPUTE.get_region_from_profile(profile_name)
    return oci_region
