import os, click, json
from .cspclient import CSPclient
from .csp_user import user
from .csp_show import oauth as oauth_show
from idptools.idpclient import IDPclient
from toolbox.logger import Log
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu

CSP = CSPclient()
CONFIG = Config('csptools')

@click.group(help="manage CSP oauth-apps for VMC",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def oauth(ctx, debug, menu):
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
    log = Log('csptools.log', debug)

@oauth.command(name="patch", help='patch an oauth-app in CSP and set default roles', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.pass_context
def patch_oath_app(ctx, target_org, app_id):
    raw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.show_oauth_service_definition_id(target_org, ctx.obj['auth'], ctx.obj['profile'], raw)
    if raw is False:
        for ITEM in OUTPUT:
            for I in ITEM:
                ID = I['serviceDefinitionId']
                if ID:
                    service_id = ID
                    break
    if app_id and service_id:
       Log.info(f"patching oauth-app {app_id} and setting default roles now, please wait...")
       OUTPUT = CSP.patch_oauth_app(target_org, app_id, service_id, ctx.obj['auth'], ctx.obj['profile'], raw)
       if OUTPUT.status_code == 200:
           Log.info(f"patching complete for {app_id} and default roles")
       else:
           Log.critical(f"patching failed for {app_id} and default roles: " + OUTPUT.status_code)
       sys.exit(0)
    OUTPUT = CSP.show_oauth_managed_apps(target_org, ctx.obj['auth'], ctx.obj['profile'], raw)
    DATA = []
    for ITEM in OUTPUT:
       for I in ITEM:
           ID = I['id']
           DATA.append(ID)
    INPUT = 'oauth-app manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        app_id = CHOICE.split('\t')[0]
    if app_id and service_id:
        Log.info(f"patching oauth-app {app_id} and setting default roles now, please wait...")
        OUTPUT = CSP.patch_oauth_app(target_org, app_id, service_id, ctx.obj['auth'], ctx.obj['profile'], raw)
        print(OUTPUT)
        if OUTPUT.status_code == 200:
            Log.info(f"patching complete for {app_id} and default roles")
        else:
            Log.critical(f"patching failed for {app_id} and default roles: " + OUTPUT.status_code)
    else:
        Log.critical("please select an oauth-app to continue...")

@oauth.command(name="publisher-id", help='create publisher-id for a specific app-id', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.pass_context
def create_oauth_publisher_id(ctx, target_org, app_id):
    raw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.show_oauth_service_definition_id(target_org, ctx.obj['auth'], ctx.obj['profile'], raw)
    if raw is False:
        for ITEM in OUTPUT:
            for I in ITEM:
                ID = I['serviceDefinitionId']
                if ID:
                    service_id = ID
                    break
    if app_id and service_id:
       Log.info(f"creating oauth-app publisher id for {app_id} now, please wait...")
       OUTPUT = CSP.create_oauth_publisher_id(target_org, app_id, service_id, ctx.obj['auth'], ctx.obj['profile'], raw)
       if OUTPUT.status_code == 200:
           Log.info(f"publisher ID created for {app_id}")
       else:
           Log.critical(f"publisher ID creation failed for {app_id}: " + OUTPUT.status_code)
       sys.exit(0)

    OUTPUT = CSP.show_oauth_managed_apps(target_org, ctx.obj['auth'], ctx.obj['profile'], raw)
    DATA = []
    for ITEM in OUTPUT:
       for I in ITEM:
           ID = I['id']
           DATA.append(ID)
    INPUT = 'oauth-app manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        app_id = CHOICE.split('\t')[0]

    if app_id and service_id:
        Log.info(f"creating oauth-app publisher id for {app_id} now, please wait...")
        OUTPUT = CSP.create_oauth_publisher_id(target_org, app_id, service_id, ctx.obj['auth'], ctx.obj['profile'], raw)
        if OUTPUT.status_code == 200:
           Log.info(f"publisher ID created for {app_id}")
        else:
            Log.critical(f"publisher ID creation failed for {app_id}: " + OUTPUT.status_code)
    else:
        Log.critical("please select an oauth-app to continue...")

@oauth.command(name="create", help='create an oauth-app in CSP', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=True, default=None)
@click.pass_context
def create_oauth_app(ctx, target_org, app_id):
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    SECRET = IDPclient.generate_password()
    OUTPUT = CSP.create_oauth_app(target_org, app_id, SECRET, ctx.obj['auth'], ctx.obj['profile'])
    if OUTPUT['clientId'] is not None:
        Log.info(f"oauth-app {app_id} created successfully in target org: {target_org}")
        Log.json(json.dumps(OUTPUT, indent=2))
        Log.info(f"adding oauth-app {app_id} to org {target_org} now")
        OUTPUT = CSP.add_oauth_app_to_org(target_org, app_id, ctx.obj['auth'], ctx.obj['profile'])
        if OUTPUT['failures'] is None or OUTPUT['failures'] == []:
            Log.info(f"successfully added oauth app {app_id} to target org: {target_org}")
        else:
            Log.critical(f"failed to add app-id {app_id} to target org: {target_org}")
    else:
        Log.critical(f"failed to create app-id {app_id} in target org: {target_org}")

@oauth.command('delete', help='delete an oauth-app in CSP', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.option('-a', '--app-id', 'app_id', help="provide oauth-app ID", type=str, required=False, default=None)
@click.pass_context
def delete_oauth_app(ctx, target_org, app_id):
    raw = False
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    if app_id:
       Log.info(f"deleting oauth-app {app_id} now, please wait...")
       OUTPUT = CSP.delete_oauth_app(target_org, app_id, ctx.obj['auth'], ctx.obj['profile'])
       if 'not found' in OUTPUT['message']:
           Log.critical(f"app-id deletion failed from {target_org}: " + str(OUTPUT['statusCode']))
       if OUTPUT['succeeded']:
           Log.info(f"app-id {app_id} deleted from {target_org}")
       else:
           Log.critical(f"app-id deletion failed from {target_org}: " + OUTPUT.status_code)
       sys.exit(0)
    OUTPUT = CSP.show_oauth_apps(target_org, ctx.obj['auth'], ctx.obj['profile'], raw)
    DATA = []
    for ITEM in OUTPUT:
       for I in ITEM:
           ID = I['id']
           DATA.append(ID)
    INPUT = 'oauth-app manager'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        app_id = CHOICE.split('\t')[0]
    if app_id:
       Log.info(f"deleting oauth-app {app_id} now, please wait...")
       OUTPUT = CSP.delete_oauth_app(target_org, app_id, ctx.obj['auth'], ctx.obj['profile'])
       if OUTPUT['succeeded'] is not None:
           Log.info(f"app-id {app_id} deleted from {target_org}")
       else:
           Log.critical(f"app-id deletion failed from {target_org}: " + OUTPUT.status_code)
    else:
        Log.critical("please select an oauth-app to continue...")

oauth.add_command(oauth_show, name='show')

def check_alt_options(optionA, optionB, Both, Neither=False):
    if optionA is None and optionB is None:
        return Neither
    if optionA is not None and optionB is None:
        return True
    if optionA is None and optionB is not None:
        return True
    if optionA is not None and optionB is not None:
        return Both

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
                Log.info(f"gathering {DISPLAY_NAME} details now, please wait...")
            else:
                Log.critical("please select an Org to continue...")
        except:
            Log.critical("please select an Org to continue...")
    return target_org, DISPLAY_NAME

