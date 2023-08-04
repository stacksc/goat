import sys, os
import click, json
from .idpclient import IDPclient
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

CONFIG = Config('idptools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from IDP/vIDP", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    PROFILE = CONFIG.get_profile(user_profile)
    ALL = PROFILE['config']
    for I in ALL:
        client_id = ALL[I]['client-id']
        secret = ALL[I]['client-secret']
        if client_id and secret:
            ctx.obj['client-id'] = client_id
            ctx.obj['client-secret'] = secret
            break
    log = Log('idptools.log', debug)

@show.command('directories', help="retrieve a list of directories from tenant", context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_directories(ctx, raw):
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    OUTPUT = IDP.list_directories(raw)
    if OUTPUT:
        Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
    else:
        Log.critical(f"tenant directory list failed for tenant {ctx.obj['profile']}")

@show.command('users', help="retrieve all users from target tenant", context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_users(ctx, raw):
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    OUTPUT = IDP.list_users(raw)
    Log.json(json.dumps(OUTPUT, indent=2))

@show.command('expired', help="retreive information about users with expired passwords", context_settings={'help_option_names':['-h','--help']})
@click.option('-w', '--within', help="search for accounts with expired passwords greater than X days", type=int, default=1)
@click.pass_context
def list_password_expiration(ctx, within):
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    OUTPUT = IDP.listPasswordExpiration(within)
    Log.json(json.dumps(OUTPUT, indent=2))

@show.command('config', help="retrieve the entire content of idptools configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def idp_config(ctx):
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    IDP.display_idp_config(user_profile)

@show.command('tenant-config', help="retrieve the entire tenant config", context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def idp_tenant_config(ctx, raw):
    DATA = []
    IDP = IDPclient(ctx)
    OUTPUT = IDP.list_tenant_config(ctx.obj['profile'].replace('.','-'))
    if OUTPUT:
        if raw is True:
            Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
        else:
            for ITEM in OUTPUT:
                for I in ITEM:
                    LINKS = I['_links']
                    try:
                        SELF = LINKS['self']['href']
                    except:
                        SELF = ''
                    DATA_DICT = {}
                    DATA_DICT['name'] = I['name']
                    DATA_DICT['self'] = SELF
                    Log.info(f"{I['name']} => {I['value']}")
                    DATA.append(DATA_DICT)
            Log.info(f"\n\n{tabulate(DATA, headers='keys', tablefmt='rst')}")
    else:
        Log.critical(f"tenant config list failed for tenant {ctx.obj['profile']}")

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'CSP Menu: {INPUT}'
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

def MenuResults(ctx):

    DATA = []
    OUTPUT = CSP.list_orgs(ctx.obj['operator'], 'operator')
    if OUTPUT == []:
        Log.critical('unable to find any orgs')
    else:
        for i in OUTPUT:
            ID = i['id']
            DISPLAY_NAME = i['display_name'].ljust(50)
            STR = DISPLAY_NAME + "\t" + ID
            DATA.append(STR)
        DATA.sort()
        INPUT = 'ORG Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            target_org = CHOICE.split('\t')[1]
            DISPLAY_NAME = CHOICE.split('\t')[0].strip()
            if DISPLAY_NAME:
                Log.info(f"displaying {DISPLAY_NAME} details now, please wait...")
            else:
                Log.critical("please select an Org to continue...")
        except:
            Log.critical("please select an Org to continue...")
    return target_org, DISPLAY_NAME

