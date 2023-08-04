import sys, os, getpass
import click, json
from .idpclient import IDPclient
from csptools.idpclient import idpc
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu

CONFIG = Config('idptools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="manage tenants", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def tenants(ctx, debug):
    user_profile = ctx.obj['profile']
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

@tenants.command('create', help="create new child tenant", context_settings={'help_option_names':['-h','--help']})
@click.option('-n', '--name', help="provide tenant name", type=str, default=None, required=True)
@click.option('-t', '--type', help="provide tenant type", default='PAID', required=True, type=click.Choice(['PAID','INTERNAL']), show_default=True)
@click.option('-p', '--parent', help="provide parent tenant", default='vmc-prod', required=True, type=click.Choice(['vmc-prod']), show_default=True)
@click.pass_context
def create(ctx, name, type, parent):
    parent = ctx.obj['profile']
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = IDPclient(ctx)
    RESULT = IDP.add_tenant(name, type)
    if RESULT:
        Log.json(json.dumps(RESULT.json(), indent=2))
    else:
        Log.critical(f'failure while creating tenant {name}')

@tenants.command('delete', help="delete child tenant", context_settings={'help_option_names':['-h','--help']})
@click.option('-n', '--name', help="provide tenant name deletion", type=str, default=None, required=False)
@click.pass_context
def delete(ctx, name):
    parent = ctx.obj['profile']
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = IDPclient(ctx)
    RESULT = IDP.delete_tenant(name)
    if RESULT:
        Log.json(json.dumps(RESULT.json(), indent=2))
    else:
        Log.critical(f'failure while deleting tenant {name}')

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
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    OUTPUT = IDP.list_users()

    if OUTPUT == []:
        Log.critical(f'unable to find any users for tenant {user_profile}')
    else:
        for i in OUTPUT:
            ID = i['id']
            USERNAME = i['username'].ljust(50)
            STR = USERNAME + "\t" + ID
            DATA.append(STR)
        DATA.sort()
        INPUT = 'IDP User Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            USERNAME = CHOICE.split('\t')[0].strip()
            USER_ID = CHOICE.split('\t')[1].strip()
            if USERNAME:
                Log.info(f"gathering {USERNAME} details now, please wait...")
            else:
                Log.critical("please select a username to continue...")
        except:
            Log.critical("please select a username to continue...")
    return USERNAME, USER_ID

def _get_tenants(filter_definition=None):
    CONFIG = Config('csptools')
    PROFILE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        if AUTH:
            break
    IDP = idpc('platform')
    DATA = IDP.get_tenant_names(filter_definition, AUTH)
    return DATA

def get_operator_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'operator'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def get_platform_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'platform'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME
