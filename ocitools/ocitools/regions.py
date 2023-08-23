import click, os, json
from toolbox.logger import Log
from .regionsclient import REGIONSclient
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from toolbox.menumaker import Menu

CONFIG = Config('ocitools')

@click.group('regions', invoke_without_command=True, help='module to manage region subscriptions', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform region actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def regions(ctx, menu):
    profile_name = ctx.obj['PROFILE']
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@regions.command(help='manually refresh regions cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    _refresh('cached_regions', profile_name)

def _refresh(cache_type, profile_name):
    try:
        if cache_type == 'cached_regions':
            REGIONS = get_REGIONclient(profile_name, auto_refresh=False)
            RESULT = REGIONS.refresh('cached_regions', profile_name)
        return True
    except:
        False
    
@regions.command(help='show the data stored in cached regions', context_settings={'help_option_names':['-h','--help']})
@click.argument('region', required=False)
@click.pass_context
def show(ctx, region):
    profile_name = ctx.obj['PROFILE']
    _show(ctx, profile_name, region)

def _show(ctx, profile_name, region):
    if not region:
        if ctx.obj["MENU"]:
            DATA = []
            REGIONS = get_REGIONclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = REGIONS.get_cached_regions(profile_name)
            for data in RESPONSE:
                ID = data
                DATA.append(ID)
            INPUT = 'Region Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE) 
            except:
                Log.critical("please select a region identifier to continue...")
            RESPONSE, DATA = REGIONS.describe(profile_name)
            print(RESPONSE, DATA)
        else:
            REGIONS = get_REGIONclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = REGIONS.get_cached_regions(profile_name)
            show_as_table(RESPONSE)
    else:
        REGIONS = get_REGIONclient(profile_name, auto_refresh=False, cache_only=True)
        RESPONSE = REGIONS.describe(region)
        Log.info(f"describing {region}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data):
    DATADICT = {}
    DATA = []
    for I in source_data:
        if 'last_cache_update' not in I:
            DATA.append(source_data[I])
            if DATA:
                DATADICT = DATA
    if DATADICT != []:
        Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}\n")

def get_REGIONclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = REGIONSclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Region Menu: {INPUT}'
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
