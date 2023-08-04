import sys, os
import click, json
from .cspclient import CSPclient
from .idpclient import idpc
from idptools.idpclient import IDPclient
from toolbox.logger import Log
from toolbox.jsontools import filter
from .csp_idp import idp_show
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate
from toolbox.misc import SddcMenuResults

CSP = CSPclient()
CONFIG = Config('csptools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from CSP",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
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

show.add_command(idp_show, name='idp')

@show.command('config', help="retrieve the entire content of csptool's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def csp_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = CSP.display_csp_config(ctx.obj['profile'])

@show.command('features', help="show a summary of available VMC org features", context_settings={'help_option_names':['-h','--help']})
@click.option('-f', '--filter', 'filter_definition', help='filter the result by key:value, key: or :value', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def csp_features(ctx, filter_definition, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    OUTPUT = CSP.show_all_features(raw, AUTH, PROFILE)
    if filter_definition is not None:
        OUTPUT = filter(OUTPUT, filter_definition)
    Log.json(json.dumps(OUTPUT, indent=2))

@show.command('properties', help="show a summary of available VMC org properties", context_settings={'help_option_names':['-h','--help']})
@click.option('-f', '--filter', 'filter_definition', help='filter the result by key:value, key: or :value', required=False, default=None)
@click.pass_context
def csp_properties(ctx, filter_definition):
    AUTH, PROFILE = get_operator_context(ctx)
    OUTPUT = CSP.show_all_properties(AUTH, PROFILE)
    if filter_definition is not None:
        OUTPUT = filter(OUTPUT, filter_definition)
    Log.json(json.dumps(OUTPUT, indent=2))

@show.command('roles', help="show a summary of available VMC org roles", context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def vmc_roles(ctx, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    OUTPUT = CSP.list_roles(raw, AUTH, PROFILE)
    if not raw:
        for ROLE in OUTPUT['all_roles']:
            Log.info(f"{ROLE}")
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.group(help="display info about CSP oauth-app(s)", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def oauth(ctx):
    pass

@oauth.command('apps', help="display list of oauth apps for selected org", context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-m', '--managed', 'managed', help="display only managed oauth-apps for target org", is_flag=True, required=False, default=False)
@click.pass_context
def show_oauth_apps(ctx, target_org, raw, managed):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    if managed is True:
        OUTPUT = CSP.show_oauth_managed_apps(target_org, AUTH, PROFILE, raw)
    else:
        OUTPUT = CSP.show_oauth_apps(target_org, AUTH, PROFILE, raw)
    if raw is False:
        for ITEM in OUTPUT:
            for I in ITEM:
                ID = I['id']
                Log.info(f'{ID}')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@oauth.command('published', help="display published oauth-apps for selected org", context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_oauth_published_apps(ctx, raw):
    AUTH, PROFILE = get_platform_context(ctx)
    OUTPUT = CSP.show_oauth_published_apps(AUTH, PROFILE, raw)
    if raw is False:
        DATA = []
        for ITEM in OUTPUT:
            for I in ITEM:
                DATA_DICT = {}
                try:
                    DATA_DICT['clientID'] = I['clientID']
                    DATA_DICT['orgID'] = I['orgID']
                    DATA_DICT['publisherID'] = I['publisherID']
                    DATA_DICT['role'] = I['role']
                except:
                    pass
                DATA.append(DATA_DICT)
        Log.info(f"\n{tabulate(DATA, headers='keys', tablefmt='rst')}")
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@oauth.command('service-id', help="display the service-definition-id for selected oauth-app", context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.pass_context
def show_oauth_service_definition_id(ctx, target_org, app_id):
    AUTH, PROFILE = get_operator_context(ctx)
    raw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.show_oauth_service_definition_id(target_org, AUTH, PROFILE, raw)
    if raw is False:
        for ITEM in OUTPUT:
            for I in ITEM:
                ID = I['serviceDefinitionId']
                Log.info(f'{ID}')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@oauth.command('details', help="display details for selected oauth-app", context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_oauth_details(ctx, target_org, app_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    myraw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    if app_id:
       Log.info(f"gathering oauth-app {app_id} allowed scopes now, please wait...")
       OUTPUT = CSP.show_oauth_details(target_org, app_id, AUTH, PROFILE, raw)
       Log.json(json.dumps(OUTPUT, indent=2))
       sys.exit(0)
    OUTPUT = CSP.show_oauth_managed_apps(target_org, AUTH, PROFILE, myraw)
    DATA = []
    for ITEM in OUTPUT:
       for I in ITEM:
           ID = I['id']
           DATA.append(ID)
    INPUT = 'oauth-app manager'
    CHOICE = runMenu(DATA, INPUT)
    try:
        CHOICE = ''.join(CHOICE)
        app_id = CHOICE.split('\t')[0]
        if app_id:
           Log.info(f"gathering oauth-app {app_id} allowed scopes now, please wait...")
           OUTPUT = CSP.show_oauth_details(target_org, app_id, AUTH, PROFILE, raw)
           Log.json(json.dumps(OUTPUT, indent=2))
        else:
           Log.critical("please select an oauth-app to continue...")
    except:
        Log.critical("please select an oauth-app to continue...")

@oauth.command('scopes', help="display list of scopes for selected oauth-app", context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_oauth_scopes(ctx, target_org, app_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    myraw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    if app_id:
       Log.info(f"gathering oauth-app {app_id} allowed scopes now, please wait...")
       OUTPUT = CSP.show_oauth_scopes(target_org, app_id, AUTH, PROFILE, raw)
       Log.json(json.dumps(OUTPUT, indent=2))
       sys.exit(0)
    OUTPUT = CSP.show_oauth_managed_apps(target_org, AUTH, PROFILE, myraw)
    DATA = []
    for ITEM in OUTPUT:
       for I in ITEM:
           ID = I['id']
           DATA.append(ID)
    INPUT = 'oauth-app manager'
    CHOICE = runMenu(DATA, INPUT)
    try:
        CHOICE = ''.join(CHOICE)
        app_id = CHOICE.split('\t')[0]
        if app_id:
           Log.info(f"gathering oauth-app {app_id} allowed scopes now, please wait...")
           OUTPUT = CSP.show_oauth_scopes(target_org, app_id, AUTH, PROFILE, raw)
           Log.json(json.dumps(OUTPUT, indent=2))
        else:
           Log.critical("please select an oauth-app to continue...")
    except:
        Log.critical("please select an oauth-app to continue...")

@oauth.command('roles', help="display list of roles for selected oauth-app", context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.option('-o', '--org-roles', 'org_roles', help="flag to display only the organization roles", is_flag=True, required=False, default=None)
@click.option('-s', '--service-roles', 'service_roles', help="flag to display only the service roles", is_flag=True, required=False, default=None)
@click.pass_context
def show_oauth_roles(ctx, target_org, app_id, org_roles, service_roles):
    AUTH, PROFILE = get_operator_context(ctx)
    raw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    if app_id:
       Log.info(f"gathering oauth-app {app_id} roles now, please wait...")
       OUTPUT = CSP.show_oauth_roles(target_org, app_id, AUTH, PROFILE, raw, org_roles, service_roles)
       Log.json(json.dumps(OUTPUT, indent=2))
       sys.exit(0)
    OUTPUT = CSP.show_oauth_managed_apps(target_org, AUTH, PROFILE, raw)
    DATA = []
    if not OUTPUT:
        Log.critical(f"unable to find oauth managed apps in target org: {target_org}")
    for ITEM in OUTPUT:
       for I in ITEM:
           ID = I['id']
           DATA.append(ID)
    INPUT = 'oauth-app manager'
    CHOICE = runMenu(DATA, INPUT)
    try:
        CHOICE = ''.join(CHOICE)
        app_id = CHOICE.split('\t')[0]
        if app_id:
           Log.info(f"gathering oauth-app {app_id} roles now, please wait...")
           OUTPUT = CSP.show_oauth_roles(target_org, app_id, AUTH, PROFILE, raw, org_roles, service_roles)
           Log.json(json.dumps(OUTPUT, indent=2))
        else:
           Log.critical("please select an oauth-app to continue...")
    except:
        Log.critical("please select an oauth-app to continue...")

@show.group(help="display info about CSP org(s)", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def org(ctx):
    pass

@org.command(name="properties", help='show VMC properties about a CSP org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.pass_context
def org_property_list(ctx, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.org_property_list(target_org, AUTH, PROFILE)
    if OUTPUT == []:
        Log.warn('specified org does not have any properties - probably not enabled for VMC yet')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))
    
@org.command(name="all", help='show all CSP orgs registered in VMC', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_orgs(ctx, raw=False):
    AUTH, PROFILE = get_operator_context(ctx)
    OUTPUT = CSP.list_orgs(AUTH, PROFILE, raw)
    if OUTPUT == []:
        Log.critical('unable to find any orgs')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="features", help='list enabled features for a CSP org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_org_features(ctx, target_org, raw=False):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.list_org_features(target_org, AUTH, PROFILE, raw)
    if OUTPUT == []:
        Log.warn('Specified org does not have any enabled features')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="tags", help='list all tags for a CSP org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.pass_context
def list_org_tags(ctx, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.list_org_tags(target_org, AUTH, PROFILE)
    if OUTPUT == []:
        Log.warn('Specified org does not have any tags')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="tasks", help='show tasks for a CSP org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-s', '--summary', 'summary', help="display task summary", is_flag=True, required=False, default=False)
@click.pass_context
def org_task_list(ctx, target_org, summary):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    if summary:    
        OUTPUT = CSP.org_show_task_summary(target_org, AUTH, PROFILE)
        if OUTPUT:
            Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
            sys.exit()
        else:
            Log.critical("unable to list task summary")
    OUTPUT = CSP.org_task_list(target_org, AUTH, PROFILE)
    if OUTPUT == []:
        Log.warn('no tasks found')
    else:
        DATA = []
        for I in OUTPUT:
            DATA.append(I['id'])
        Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="details", help='show all details about a given org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.pass_context
def show_org_details(ctx, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    if target_org is None:
        Log.critical("please select an Org to continue using the menu interface or provide one on the CLI.")

    OUTPUT = CSP.org_show_details(target_org, AUTH, PROFILE)
    if OUTPUT == []:
        Log.critical('unable to find org details or org doesnt exist')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="sddcs", help='show all sddcs deployed under a given org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-o', '--only-aws-ready', 'aws_ready',  help='only show SDDCs in AWS and in READY state', default=False, is_flag=True, required=False)
@click.option('-v', '--version', 'version_only',  help='only show versions of the SDDCs', default=False, is_flag=True, required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_org_sddcs(ctx, target_org, aws_ready, version_only, raw=False):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = SddcMenuResults(ctx)
    OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
    if not OUTPUT:
        Log.critical(f"unable to find sddcs in target org: {target_org}")
    Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="users", help='list all users in an org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-f', '--filter', 'filter_definition', help='filter the result by key:value, key: or :value', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_org_users(ctx, target_org, filter_definition, raw):
    AUTH, PROFILE = get_platform_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
    if not OUTPUT:
        Log.critical(f"unable to find users in target org: {target_org}")
    if filter_definition is not None:
        OUTPUT = filter(OUTPUT, filter_definition)
    Log.json(json.dumps(OUTPUT, indent=2))

@org.command(name="task", help='show details about a specific task', context_settings={'help_option_names':['-h','--help']})
@click.argument('task_id', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def show_task_details(ctx, task_id, target_org):
    from operator import itemgetter, attrgetter
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.org_task_list(target_org, AUTH, PROFILE)
    if OUTPUT == []:
        Log.warn('no tasks found')
    else:
        DATA = []
        for I in OUTPUT:
            STATUS = I['status'].rjust(10)
            ID = I['id'].ljust(30)
            TYPE = I['task_type'].rjust(40)
            CREATED = I['created'].rjust(10)
            STR = ID + '\t' + STATUS + '\t' + TYPE + '\t' + CREATED
            DATA.append(STR)
    S = sorted(DATA, reverse=True, key=lambda x: str(x.rsplit('\t', 1)[1]))
    INPUT = 'task manager'
    CHOICE = runMenu(S, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        task_id = CHOICE.split('\t')[0]
    if not task_id:
        Log.critical("please provide a task-id")
    OUTPUT = CSP.org_show_task_details(task_id, target_org, AUTH, PROFILE)
    if OUTPUT == []:
        Log.critical('unable to find org details or org doesnt exist')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@org.command('refresh-token', help='API refresh-token used for generating an API access token', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_refresh_token(ctx):
    RESULT = CSP.get_org_refresh_token(ctx.obj['auth'], org_name=None, user_profile=ctx.obj['profile'])
    Log.info(f"Refresh token:\n{RESULT}")
    return RESULT

@org.command('access-token', help='API token for accessing the CSP functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = CSP.get_org_access_token(ctx.obj['auth'], org_name=None, user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@org.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = CSP.get_org_access_token_age(ctx.obj['auth'], org_name=None, user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

@org.command('config', help="retrieve all stored config for an org", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def org_config(ctx):
    RESULT = CSP.display_org_config(None, None, ctx.obj['profile'])
    if RESULT:
        Log.json(json.dumps(RESULT, indent=2, sort_keys=True))

@org.command(help='lookup a CSP org ID using the name configured for it in csptools', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.pass_context
def org_id(ctx, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org_id, target_org = MenuResults(ctx)
        Log.info(f"org ID: {target_org_id} org name: {target_org}")
        sys.exit(0)
    try:
        OUTPUT = CSP.list_orgs(AUTH, PROFILE)
        if OUTPUT == []:
            Log.critical('unable to find any orgs')
        else:
            for i in OUTPUT:
                target_org_id = i['id']
                DISPLAY_NAME = i['display_name'].strip()
                if target_org == DISPLAY_NAME:
                    Log.info(f"org ID: {target_org_id} org name: {target_org}")
                    break
    except:
        Log.critical(f"unable to find target org: {target_org} in csptools database")

@org.command(help='lookup a CSP org name (if configured) using its org ID', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.pass_context
def org_name(ctx, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
        Log.info(f"org ID: {target_org} org name: {name}")
        sys.exit(0)
    try:
        OUTPUT = CSP.list_orgs(AUTH, PROFILE)
        if OUTPUT == []:
            Log.critical('unable to find any orgs')
        else:
            for i in OUTPUT:
                target_org_id = i['id']
                name = i['display_name'].strip()
                if target_org == target_org_id:
                    Log.info(f"org ID: {target_org_id} org name: {name}")
                    break
    except:
        Log.critical(f"unable to find target org: {target_org} in csptools database")

@org.command('account', help='show details about AWS account associated with a given org')
@click.argument('target_org', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_org_account(ctx, target_org, raw):
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    AUTH, PROFILE = get_operator_context(ctx)
    RESULT = CSP.show_org_account(target_org, AUTH, PROFILE, raw)
    Log.info(RESULT)

@show.group(help="display info about CSP user(s)", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def user(ctx):
    pass

@user.command(name="orgs", help='list orgs associated with the user', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.option('-r', '--remove', 'remove', help="remove the associated user from each org found", is_flag=True, required=False, default=False)
@click.pass_context
def list_user_orgs(ctx, user_name, remove):
    AUTH, PROFILE = get_platform_context(ctx)
    if user_name:
       Log.info(f"gathering username {user_name} orgs now, please wait...")
       OUTPUT = CSP.user_list_orgs(user_name, AUTH, PROFILE)
       if OUTPUT is not None:
           for ITEM in OUTPUT:
               AUTH, PROFILE = get_operator_context(ctx)
               ID = f"{ITEM.split('/')[-1]}"
               print("*******************************************************")
               Log.info(ID)
               print("*******************************************************")
               OUTPUT = CSP.org_show_details(ID, AUTH, PROFILE)
               if OUTPUT == []:
                   Log.critical('unable to find org details or org doesnt exist')
               else:
                   Log.info(f'Display Name:  {OUTPUT["display_name"]}')
                   Log.info(f'Project State: {OUTPUT["project_state"]}')
                   if remove:
                       AUTH, PROFILE = get_platform_context(ctx)
                       OUTPUT = CSP.org_remove_user(user_name, ID, AUTH, PROFILE)
                       try:
                           if OUTPUT['succeeded'] is not None:
                               Log.info(OUTPUT['succeeded'])
                               Log.info(f"user {user_name} removed from {ID}")
                           else:
                               Log.warn(f'failed to remove user {user_name} from {ID}')
                       except:
                           Log.warn(f'failed to remove user {user_name} from {ID}')
       else:
           Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
       sys.exit()

    IDP = idpc(PROFILE)
    TENANTS = _get_tenants()
    TENANTS.sort()
    INPUT = 'Tenant Manager'
    CHOICE = runMenu(TENANTS, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        TENANT = CHOICE.split('\t')[1].strip()
        if 'VMwareFed' in TENANT:
            TENANT = 'vmc-prod'
        elif 'customer.local' in TENANT:
            TENANT = 'customer-local'
        elif 'CSP User Local' in TENANT:
            TENANT = 'csp-user-local'
        URL = CHOICE.split('\t')[0].strip()
        Log.info(f'gathering users belonging to tenant {TENANT} => {URL}')
    else:
        Log.critical("please select a tenancy to gather users")

    ctx.obj['profile'] = TENANT
    IDP = IDPclient(ctx)
    RESULT = IDP.list_users(ctx)
    DATA = []
    for I in RESULT:
        USERNAME = I['username'].ljust(50)
        ID = I['id']
        EMAIL = I['email'].rjust(50)
        STRING = USERNAME + '\t' + ID + '\t' + EMAIL
        DATA.append(STRING)
        DATA.sort()
    INPUT = 'User Manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        USERNAME = CHOICE.split('\t')[0].strip()
        ID = CHOICE.split('\t')[1].strip()
        EMAIL = CHOICE.split('\t')[2].strip() 
        Log.info(f"gathering username {USERNAME} orgs now, please wait...")
    else:
        Log.critical("please select a username to continue...")

    OUTPUT = CSP.user_list_orgs(USERNAME, AUTH, PROFILE)
    if OUTPUT is not None:
        for ITEM in OUTPUT:
            AUTH, PROFILE = get_operator_context(ctx)
            ID = f"{ITEM.split('/')[-1]}"
            print("*******************************************************")
            Log.info(ID)
            print("*******************************************************")
            OUTPUT = CSP.org_show_details(ID, AUTH, PROFILE)
            if OUTPUT == []:
                Log.critical('unable to find org details or org doesnt exist')
            else:
                Log.info(f'Display Name:  {OUTPUT["display_name"]}')
                Log.info(f'Project State: {OUTPUT["project_state"]}')
                if remove:
                    AUTH, PROFILE = get_platform_context(ctx)
                    OUTPUT = CSP.org_remove_user(USERNAME, ID, AUTH, PROFILE)
                    try:
                        if OUTPUT['succeeded'] is not None:
                            Log.info(OUTPUT['succeeded'])
                            Log.info(f"user {USERNAME} removed from {ID}")
                        else:
                            Log.warn(f'failed to remove user {USERNAME} from {ID}')
                    except:
                        Log.warn(f'failed to remove user {USERNAME} from {ID}')
    else:
        Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))

@user.command(name="details", help='list details about the user', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def list_user_details(ctx, user_name, target_org):
    raw = False
    AUTH, PROFILE = get_platform_context(ctx)
    if user_name:
       Log.info(f"gathering username {user_name} details now, please wait...")
       OUTPUT = CSP.user_list_details(user_name, AUTH, PROFILE)
       Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
       sys.exit(0)

    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
    DATA = []
    for I in OUTPUT:
       DATA.append(I['username'])
    INPUT = 'user manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        user_name = CHOICE.split('\t')[0]
        if user_name:
           Log.info(f"gathering username {user_name} details now, please wait...")
           OUTPUT = CSP.user_list_details(user_name, AUTH, PROFILE)
           Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
        else:
           Log.critical("please select a username to continue...")
    else:
       Log.critical("please select a username to continue...")

@user.command(name="roles", help='list roles associated with the user', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def list_user_roles(ctx, user_name, target_org):
    raw = False
    AUTH, PROFILE = get_platform_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    if user_name:
       Log.info(f"gathering username {user_name} roles now, please wait...")
       OUTPUT = CSP.user_list_roles(user_name, target_org, AUTH, PROFILE)
       Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
       sys.exit(0)
    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
    DATA = []
    for I in OUTPUT:
       DATA.append(I['username'])
    INPUT = 'user manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        user_name = CHOICE.split('\t')[0]
        if user_name:
           Log.info(f"gathering username {user_name} roles now, please wait...")
           OUTPUT = CSP.user_list_roles(user_name, target_org, AUTH, PROFILE)
           Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
        else:
           Log.critical("please select a username to continue...")
    else:
       Log.critical("please select a username to continue...")

@user.command(name="service-roles", help='list service roles associated with the user', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def list_user_service_roles(ctx, user_name, target_org):
    raw = False
    AUTH, PROFILE = get_platform_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    if user_name:
       Log.info(f"gathering username {user_name} service-roles now, please wait...")
       OUTPUT = CSP.user_list_service_roles(user_name, target_org, AUTH, PROFILE)
       Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
       sys.exit(0)
    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
    DATA = []
    for I in OUTPUT:
       DATA.append(I['username'])
    INPUT = 'user manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        user_name = CHOICE.split('\t')[0]
        if user_name:
           Log.info(f"gathering username {user_name} service-roles now, please wait...")
           OUTPUT = CSP.user_list_service_roles(user_name, target_org, AUTH, PROFILE)
           Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
        else:
           Log.critical("please select a username to continue...")
    else:
       Log.critical("please select a username to continue...")

@user.command('userid', help='get userid for a specific user in CSP', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_name', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def show_user_id(ctx, user_name, target_org):
    raw = False
    AUTH, PROFILE = get_platform_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    if user_name:
       Log.info(f"gathering username {user_name} user-id now, please wait...")
       OUTPUT = CSP.get_user_id(user_name.split('@')[0], AUTH, PROFILE)
       Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
       sys.exit(0)
    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
    DATA = []
    for I in OUTPUT:
       DATA.append(I['username'])
    INPUT = 'user manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        user_name = CHOICE.split('\t')[0]
        if user_name:
           Log.info(f"gathering username {user_name} user-id now, please wait...")
           OUTPUT = CSP.get_user_id(user_name.split('@')[0], AUTH, PROFILE)
           Log.info(f"userId pulled for {user_name} is: {OUTPUT}")
        else:
           Log.critical("please select a username to continue...")
    else:
       Log.critical("please select a username to continue...")

@user.command('sessions', help='get max session limit for the user and their active sessions', context_settings={'help_option_names':['-h','--help']})
@click.argument('user_id', required=False, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def show_user_sessions(ctx, user_id, target_org):
    raw = False
    AUTH, PROFILE = get_platform_context(ctx)
    if ctx.obj['menu'] is True or target_org is None:
        target_org, name = MenuResults(ctx)
    if user_id:
       Log.info(f"gathering username {user_id} sessions now, please wait...")
       MAX, ACTIVE = CSP.get_user_sessions(user_id, AUTH, PROFILE)
       Log.info(f"max sessions: ")
       Log.json(json.dumps(MAX, indent=2, sort_keys=True))
       Log.info(f"active sessions: ")
       Log.json(json.dumps(ACTIVE, indent=2, sort_keys=True))
       sys.exit(0)
    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
    DATA = []
    for I in OUTPUT:
       DATA.append(I['username'])
    INPUT = 'user manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        user_id = CHOICE.split('\t')[0]
        if user_id:
           Log.info(f"gathering username {user_id} sessions now, please wait...")
           MAX, ACTIVE = CSP.get_user_sessions(user_id, AUTH, PROFILE)
           Log.info(f"max sessions: ")
           Log.json(json.dumps(MAX, indent=2, sort_keys=True))
           Log.info(f"active sessions: ")
           Log.json(json.dumps(ACTIVE, indent=2, sort_keys=True))
        else:
           Log.critical("please select a username to continue...")
    else:
       Log.critical("please select a username to continue...")

def get_target_org(user_profile):
    PROFILE = CONFIG.get_profile(user_profile)
    ALL_ORGS = PROFILE['config']
    for ORG_NAME in ALL_ORGS:
        ORG = ALL_ORGS[ORG_NAME]
        target_org = ORG['id']
    return target_org

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
