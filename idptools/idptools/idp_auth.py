import click, getpass, os
from csptools.csp_idp import _get_tenants as get_tenants
from .idpclient import env_from_sourcing, IDPclient
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox import misc

CONFIG = Config('idptools')

@click.group(help="perform authentication operations against IDP/vIDP", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def auth(ctx, debug):
    user_profile = ctx.obj['profile']
    PROFILE = CONFIG.get_profile(user_profile)
    ctx.obj['setup'] = False
    try:
        ALL = PROFILE['config']
        for I in ALL:
            client_id = ALL[I]['client-id']
            secret = ALL[I]['client-secret']
            if client_id and secret:
                ctx.obj['client-id'] = client_id
                ctx.obj['client-secret'] = secret
                break
    except:
        pass
    log = Log('idptools.log', debug)

def get_latest_profile():
    LATEST = CONFIG.get_profile('latest')
    if LATEST is None:
        IDP_PROFILE = 'default'
    else:
        IDP_PROFILE = LATEST['config']['role']
    return IDP_PROFILE

@auth.command(help='update the default profile', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def update_profile(ctx):
    update_latest_profile(ctx.obj['profile'])

@auth.command(help='setup your API access to a given IDP tenancy', context_settings={'help_option_names':['-h','--help']})
@click.option('-m', '--manual', help="skip the menu interface", is_flag=True, required=False, default=False)
@click.pass_context
def setup(ctx, manual):
    ctx.obj['setup'] = True
    IDP = IDPclient(ctx)
    if manual is False:
        TENANTS = get_tenants()
        TENANTS.sort()
        INPUT = 'Tenancy Setup'
        CHOICE = runMenu(TENANTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            profile = CHOICE.split('\t')[1].strip()
            url = CHOICE.split('\t')[0].strip()
            Log.info(f'setting up access to tenant {profile} => {url}')
            RESULT = IDP.setup_access(url, client_id=None, secret=None, profile=profile)
        else:
            Log.critical("please select a tenancy for setup")
    else:
        profile = ctx.obj['profile']
        url = f'https://{profile}.gc1.vmwareidentity.us'
        Log.info(f'setting up access to tenant {profile} => {url}')
        RESULT = IDP.setup_access(url, client_id=None, secret=None, profile=profile)
    if RESULT:
       Log.info(f"org settings saved succesfully for tenancy: {profile}")
       update_latest_profile(profile)

def update_latest_profile(profile_name):
    BASICS = Config('idptools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'TENANT Menu: {INPUT}'
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

