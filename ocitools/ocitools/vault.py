import click, os, json
from toolbox.logger import Log
from .vaultclient import VAULTclient
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from toolbox.menumaker import Menu

CONFIG = Config('ocitools')

@click.group('vault', invoke_without_command=True, help='module to manage vaults', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform vault actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def vault(ctx, menu):
    profile_name = ctx.obj['PROFILE']
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@vault.command(help='manually refresh vaults stored in cache', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    _refresh('cached_vaults', profile_name)

def _refresh(cache_type, profile_name):
    try:
        if cache_type == 'cached_vaults':
            VAULT = get_VAULTclient(profile_name, auto_refresh=False)
            RESULT = VAULT.refresh('cached_vaults', profile_name)
        return True
    except:
        False
    
@vault.command(help='show the data stored in cached vault', context_settings={'help_option_names':['-h','--help']})
@click.argument('vault', required=False)
@click.pass_context
def show(ctx, vault):
    profile_name = ctx.obj['PROFILE']
    _show(ctx, profile_name, vault)

def _show(ctx, profile_name, vault):
    if not vault:
        if ctx.obj["MENU"]:
            DATA = []
            DICT = {}
            VAULT = get_VAULTclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = VAULT.get_cached_vaults(profile_name)
            for I in RESPONSE:
                if I not in 'last_cache_update':
                    NAME = RESPONSE[I]['display_name']
                    DATA.append(I + '\t' + NAME)
            INPUT = 'Vault Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE)
                OCID = CHOICE.split('\t')[0].strip()
            except:
                Log.critical("please select a vault to continue...")
            RESPONSE = VAULT.describe(OCID, profile_name)
            Log.info(f"describing {OCID}:\n")
            for I in RESPONSE:
                print(RESPONSE[I])
        else:
            VAULT = get_VAULTclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = VAULT.get_cached_vaults(profile_name)
            show_as_table(RESPONSE)
    else:
        VAULT = get_VAULTclient(profile_name, auto_refresh=False, cache_only=True)
        RESPONSE = VAULT.describe(vault)
        Log.info(f"describing {secret}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data):
    IGNORE = ['last_cache_update']
    DATADICT = {}
    DATA = []
    try:
        for I in source_data:
            if I not in IGNORE:
                DATA.append(source_data[I])
                if DATA:
                    DATADICT = DATA
        if DATADICT != []:
            Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}\n")
    except:
        return None

def get_VAULTclient(profile_name, region='us-ashburn-1', auto_refresh=True, cache_only=False):
    CLIENT = VAULTclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Vault Menu: {INPUT}'
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
