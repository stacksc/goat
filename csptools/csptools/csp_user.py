import click, json
from .cspclient import CSPclient
from .csp_show import user as user_show
from csptools.csp_idp import _get_tenants as get_tenants
from idptools.idpclient import IDPclient
from toolbox.logger import Log
from toolbox import misc
from toolbox.menumaker import Menu
from configstore.configstore import Config

CSP = CSPclient()
CONFIG = Config('csptools')

@click.group(help="manage users in CSP orgs for VMC",  context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for CSP user add/remove actions", is_flag=True)
@click.pass_context
def user(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False

    PROFILE = CONFIG.get_profile('operator')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj['operator'] = AUTH
        if AUTH:
            break

    PROFILE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj['platform'] = AUTH
        if AUTH:
            break
    log = Log('csptools.log', debug)

@user.command(name="add", help='add user to a CSP org', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.option('-r', '--role', help="provide a target role level", required=True, default=None, type=click.Choice(['member','operator','owner']))
@click.option('-o', '--org', help="provide a target org to add a user to", required=False, default=None, type=str)
@click.pass_context
def add_to_org(ctx, user_name, role, org):
    AUTH, PROFILE = get_operator_context(ctx)
    csp_profile = ctx.obj['profile']
    if user_name is None:
        TENANTS = get_tenants()
        TENANTS.sort()
        INPUT = 'User Setup'
        CHOICE = runMenu(TENANTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            profile = CHOICE.split('\t')[1].strip()
            url = CHOICE.split('\t')[0].strip()
            ctx.obj['profile'] = profile
            ctx.obj['url'] = url
            user_name, user_email = MenuResults(ctx)
        else:
            Log.critical("please select a tenancy to select a user to add...")

    if role == 'member' or role == 'owner':
        user_role = f"org_{role}"
    else:
        user_role = f"platform_{role}"

    if ctx.obj['menu'] is True or org is None or user_name is None:
        DATA = []
        OUTPUT = CSP.list_orgs(AUTH, PROFILE)
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
            CHOICE = ''.join(CHOICE)
            org = CHOICE.split('\t')[1]
            DISPLAY_NAME = CHOICE.split('\t')[0].strip()
            if user_name:
                Log.info(f"adding user {user_name} to {DISPLAY_NAME} now, please wait...")
                if '@' not in user_name:
                    user_name = user_email
            else:
                Log.critical("please select/or enter a username to continue...")

    AUTH, PROFILE = get_platform_context(ctx)
    if org is None or user_name is None:
        Log.critical("please provide an org and user_name to continue")

    OUTPUT = CSP.org_add_user(user_name, user_role, org, AUTH, PROFILE)
    try:
        if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
            Log.info('added the user')
        else:
            Log.critical('failed to add the user')
    except:
        Log.json(json.dumps(OUTPUT, indent=2))

@user.command('remove', help='remove an user from a CSP org', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def remove_from_org(ctx, user_name, target_org):
    if ctx.obj['menu'] is True or target_org is None:
        AUTH, PROFILE = get_operator_context(ctx)
        DATA = []
        OUTPUT = CSP.list_orgs(AUTH, PROFILE)
        if OUTPUT == []:
            Log.critical('unable to find any orgs')
        else:
            for i in OUTPUT:
                ID = i['id']
                DISPLAY_NAME = i['display_name'].ljust(50)
                STR = DISPLAY_NAME + "\t" + ID
                DATA.append(STR)
            DATA.sort()
            INPUT = 'User Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE)
                target_org = CHOICE.split('\t')[1]
                DISPLAY_NAME = CHOICE.split('\t')[0].strip()
                if user_name is None:
                    AUTH, PROFILE = get_platform_context(ctx)
                    OUTPUT = CSP.show_all_users(target_org, False, AUTH, PROFILE)
                    DATA = []
                    for I in OUTPUT:
                        DATA.append(I['username'])
                    DATA.sort()
                    INPUT = 'USER Manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        user_name = CHOICE.split('\t')[0]
                    else:
                        Log.critical("please select a username to continue...")
                if DISPLAY_NAME:
                    Log.info(f"removing user {user_name} from {DISPLAY_NAME} now, please wait...")
                else:
                    Log.critical("please select a username to continue...")
            except:
                Log.critical("please select an org to continue...")

    AUTH, PROFILE = get_platform_context(ctx)
    if target_org is None:
        Log.critical("please select an org to continue using the menu interface or provide one on the CLI.")
    OUTPUT = CSP.org_remove_user(user_name, target_org, AUTH, PROFILE)
    try:
        if OUTPUT['succeeded'] is not None:
            Log.info(OUTPUT['succeeded'])
            Log.info("user removed")
        else:
            Log.critical('failed to remove the user')
    except:
        Log.critical('failed to remove the user')

@user.command('search', help='search for a user in CSP', context_settings={'help_option_names':['-h','--help']})
@click.argument('search_term', required=True, default=None)
@click.pass_context
def user_search(ctx, search_term):
    AUTH, PROFILE = get_platform_context(ctx)
    OUTPUT = CSP.user_search(search_term, AUTH, PROFILE)
    Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))

@user.group(help="manage user session settings", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def session(ctx):
    pass

@session.command('delete', help='delete active user session', context_settings={'help_option_names':['-h','--help']})
@click.argument('session_id', required=True, default=None)
@click.pass_context
def delete_user_session(ctx, session_id):
    AUTH, PROFILE = get_platform_context(ctx)
    OUTPUT = CSP.delete_user_session(session_id, AUTH, PROFILE)
    if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
        Log.info("session removed")
    else:
        Log.critical('failed to remove the session')

@session.command('limit', help="change a user's active session limit", context_settings={'help_option_names':['-h','--help']})
@click.argument('user_id', required=True)
@click.argument('new_limit', required=True)
@click.pass_context
def user_session_limit(ctx, user_id, new_limit):
    AUTH, PROFILE = get_platform_context(ctx)
    OUTPUT = CSP.user_session_limit(user_id, new_limit, AUTH, PROFILE)
    if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
        Log.info(f"session limit has been set to {new_limit} for {user_id}")
        OUTPUT = CSP.get_user_sessions(user_id, AUTH, PROFILE)
        Log.json(json.dumps(OUTPUT, indent=2))
    else:
        Log.critical('failed to edit the session limit')

@user.group(help="manage user roles within an organization", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def role(ctx):
    pass

@role.command('change', help='change role assigned to the user', context_settings={'help_option_names':['-h','--help']})
@click.argument('new_role', required=True, default=None)
@click.argument('user_name', required=False, default=None)
@click.pass_context
def user_role_change(ctx, new_role, user_name):
    AUTH, PROFILE = get_operator_context(ctx)
    csp_profile = ctx.obj['profile']
    if user_name is None:
        TENANTS = get_tenants()
        TENANTS.sort()
        INPUT = 'User Setup'
        CHOICE = runMenu(TENANTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            profile = CHOICE.split('\t')[1].strip()
            url = CHOICE.split('\t')[0].strip()
            ctx.obj['profile'] = profile
            ctx.obj['url'] = url
            user_name, user_email = MenuResults(ctx)
        else:
            Log.critical("please select a tenancy to select a user to change...")

    DATA = []
    OUTPUT = CSP.list_orgs(AUTH, PROFILE)
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
        CHOICE = ''.join(CHOICE)
        target_org = CHOICE.split('\t')[1]
        DISPLAY_NAME = CHOICE.split('\t')[0].strip()
        if DISPLAY_NAME:
            Log.info(f"modifying user {user_name} for {DISPLAY_NAME} now, please wait...")
        else:
            Log.critical("please select an organization name to continue")

    OUTPUT = CSP.user_list_roles(user_name, target_org, AUTH, PROFILE)
    for I in OUTPUT:
        current_role = I['name']

    OUTPUT = CSP.org_user_role_change(user_name, target_org, current_role, new_role, AUTH, PROFILE)
    if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
        Log.info('changed user roles')
    else:
        Log.critical('failed to change user roles')

@role.command('admin', help='set the user as an admin for the org', context_settings={'help_option_names':['-h','--help']})
@click.argument('admin_type', required=True, default=None, type=click.Choice(['vmc-full', 'operator-sre', 'operator-re']))
@click.argument('user_name', required=False, default=None)
@click.pass_context
def user_to_admin(ctx, admin_type, user_name):
    AUTH, PROFILE = get_operator_context(ctx)
    csp_profile = ctx.obj['profile']
    if user_name is None:
        TENANTS = get_tenants()
        TENANTS.sort()
        INPUT = 'User Setup'
        CHOICE = runMenu(TENANTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            profile = CHOICE.split('\t')[1].strip()
            url = CHOICE.split('\t')[0].strip()
            ctx.obj['profile'] = profile
            ctx.obj['url'] = url
            user_name, user_email = MenuResults(ctx)
        else:
            Log.critical("please select a tenancy to select a user to add...")

    DATA = []
    OUTPUT = CSP.list_orgs(AUTH, PROFILE)
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
        CHOICE = ''.join(CHOICE)
        target_org = CHOICE.split('\t')[1]
        DISPLAY_NAME = CHOICE.split('\t')[0].strip()
        if DISPLAY_NAME:
            Log.info(f"modifying user {user_name} for {DISPLAY_NAME} now, please wait...")
        else:
            Log.critical("please select an organization name to continue")

    # do this portion as the operator user
    OUTPUT = CSP.show_oauth_service_definition_id(target_org, AUTH, PROFILE, raw=False)
    for ITEM in OUTPUT:
        for I in ITEM:
            service_id = I['serviceDefinitionId']
    # switch to platform user
    AUTH, PROFILE = get_platform_context(ctx)
    OUTPUT = CSP.org_user_to_admin(service_id, user_name, target_org, admin_type, AUTH, PROFILE)

    if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
        Log.info('admin rights assigned')
    else:
        Log.critical('failed to assign admin rights')

user.add_command(user_show, name='show')

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
            EMAIL = i['email']
            STR = USERNAME + "\t" + EMAIL
            DATA.append(STR)
        DATA.sort()
        INPUT = 'IDP User Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            USERNAME = CHOICE.split('\t')[0].strip()
            EMAIL = CHOICE.split('\t')[1].strip()
            if USERNAME:
                Log.info(f"gathering {USERNAME} details now, please wait...")
            else:
                Log.critical("please select a username to continue...")
        except:
            Log.critical("please select a username to continue...")
    return USERNAME, EMAIL

def get_operator_context(ctx):
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
    PROFILE_NAME = 'platform'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

