import click, os, json
from toolbox.logger import Log
from .dbsclient import DBSclient
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from toolbox.menumaker import Menu

CONFIG = Config('ocitools')

@click.group('dbs', invoke_without_command=True, help='dbs module to manage the DBS instances and related configuration', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform DBS actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def dbs(ctx, menu):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@dbs.command(help='manually refresh dbs cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _refresh('cached_dbs_instances', oci_region, profile_name)

def _refresh(cache_type, oci_region, profile_name):
    try:
        if cache_type == 'cached_dbs_instances':
            DBS = get_DBSclient(profile_name, oci_region, auto_refresh=False)
            RESULT = DBS.refresh('cached_dbs_instances', profile_name)
        return True
    except:
        False
    
@dbs.command(help='show the data stored in dbs cache', context_settings={'help_option_names':['-h','--help']})
@click.argument('database', required=False)
@click.pass_context
def show(ctx, database):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _show(ctx, profile_name, oci_region, database)

def _show(ctx, profile_name, oci_region, database):
    if not database:
        if ctx.obj["MENU"]:
            DATA = []
            DBS = get_DBSclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
            RESPONSE = DBS.show_dbs_instances(profile_name)
            for data in RESPONSE[oci_region]:
                ID = data
                DATA.append(ID)
            INPUT = 'DBS Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE) 
            except:
                Log.critical("please select a DBS Identifier to continue...")
            RESPONSE = DBS.describe(CHOICE)
            Log.info(f"describing {CHOICE}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))
        else:
            DBS = get_DBSclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
            RESPONSE = DBS.show_dbs_instances(profile_name)
            try:
                show_as_table(RESPONSE[oci_region], name='DBS TABLE')
            except:
                Log.warn(f'there are 0 DBS instances in {oci_region} and profile: {profile_name}')
                pass
    else:
        DBS = get_DBSclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
        RESPONSE = DBS.describe(database)
        Log.info(f"describing {database}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data, name=None):
    DATA = []
    for ENTRY in source_data:
        DATA_ENTRY = {}
        if ENTRY != 'last_cache_update':
            DATA_ENTRY['display_name'] = ENTRY
            for PROPERTY in source_data[ENTRY]:
                DATA_ENTRY[PROPERTY] = source_data[ENTRY][PROPERTY]
            DATA.append(DATA_ENTRY)
    if DATA != []:
        Log.info(f"{name}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")

def get_DBSclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = DBSclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'DBS Menu: {INPUT}'
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
    OCI_REGION = ctx.obj['REGION']
    if not OCI_REGION:
        DBS = get_DBSclient(profile_name)
        OCI_REGION = DBS.get_region_from_profile(profile_name)
    return OCI_REGION
