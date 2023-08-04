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

@click.group(help="manage users per tenant", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def users(ctx, debug, menu):
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

@users.command('remove', help="remove user from selected tenant", context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--username', help="provide username to add", type=str, default=None, required=False)
@click.pass_context
def remove_user(ctx, username):
    AUTH, PROFILE = get_platform_context(ctx)
    TENANTS = _get_tenants()
    TENANTS.sort()
    INPUT = 'Tenant Manager'
    CHOICE = runMenu(TENANTS, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        tenant = CHOICE.split('\t')[1].strip()
        url = CHOICE.split('\t')[0].strip()
        Log.info(f'gathering users belonging to tenant {tenant} => {url}')
    else:
        Log.critical("please select a tenancy to gather users")
    ctx.obj['profile'] = tenant
    IDP = IDPclient(ctx)
    OUTPUT = IDP.list_users(raw=False)
    DATA = []
    for I in OUTPUT:
        USERNAME = I['username'].ljust(50)
        ID = I['id']
        DATA.append(USERNAME + '\t' + ID)
    DATA.sort()
    INPUT = 'User Manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        USERNAME = CHOICE.split('\t')[0].strip()
        ID = CHOICE.split('\t')[1].strip()
        Log.info(f'removing user {USERNAME} => {ID}')
    else:
        Log.critical("please select a username to remove")
    RESULT = IDP.delete_user(USERNAME, ID)
    if RESULT == 200 or RESULT == 204:
        Log.info(f'removed username {USERNAME} successfully')
    else:
        Log.critical(f'remove username {USERNAME} failed')

@users.command('add', help="add user to selected tenant", context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--username', help="provide username to add", type=str, default=None, required=True)
@click.option('-f', '--firstname', help="provide firstname", type=str, default=None, required=True)
@click.option('-l', '--lastname', help="provide lastname", type=str, default=None, required=True)
@click.option('-e', '--email', help="provide email address", type=str, default=None, required=True)
@click.option('-d', '--domain', help="provide domain", type=str, default='customer.local', required=False)
@click.pass_context
def add_user(ctx, username, firstname, lastname, email, domain):
    AUTH, PROFILE = get_platform_context(ctx)
    if '.' not in username:
        Log.info(f'running add user on username: {username}')
    else:
        Log.critical('please provide a username without a "." in it')
    TENANTS = _get_tenants()
    TENANTS.sort()
    INPUT = 'Tenant Manager'
    CHOICE = runMenu(TENANTS, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        tenant = CHOICE.split('\t')[1].strip()
        url = CHOICE.split('\t')[0].strip()
        Log.info(f'gathering users belonging to tenant {tenant} => {url}')
    else:
        Log.critical("please select a tenancy to gather users")
    IDP = IDPclient(ctx)
    IDP.add_user(username, firstname, lastname, email, tenant, domain)

@users.command('password-reset', help="password-reset per selected user and target", context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--user', help="provide username for password-reset", type=str, default=None, required=False)
@click.option('-g', '--generate', help="automatically generate a random password", is_flag=True)
@click.pass_context
def password_reset(ctx, user, generate):
    if user is None or ctx.obj['menu'] is True:
        username, user = MenuResults(ctx)
    if user is None:
        Log.critical('please select a username to continue')
    Log.info(f'running passsword reset on user ID: {user}')
    if generate is True:
        password = IDPclient.generate_password()
    else:
        password = getpass.getpass('Enter password: ')
    IDP = IDPclient(ctx)
    IDP.set_password(user, password)

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
