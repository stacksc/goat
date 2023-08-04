import os, click, json
from .cspclient import CSPclient
from .csp_user import user
from .csp_show import org as org_show
from toolbox.logger import Log
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu

CSP = CSPclient()
CONFIG = Config('csptools')

@click.group(help="manage CSP orgs for VMC",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def org(ctx, debug, menu):
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

@org.command(name="type", help='set org type', context_settings={'help_option_names':['-h','--help']})
@click.argument('org_type', required=True)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def org_set_type(ctx, org_type, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.org_set_type(target_org, org_type, AUTH, PROFILE)
    if OUTPUT is not None:
        Log.info('default properties added')
        Log.json(json.dumps(OUTPUT, indent=2))
    else:
        Log.critical('failed to add org properties')

@org.command(name="create", help='create an org in CSP', context_settings={'help_option_names':['-h','--help']})
@click.argument('new_org_name', required=True, default=None)
@click.pass_context
def create_org(ctx, new_org_name):
    AUTH, PROFILE = get_operator_context(ctx)
    ORG_ID = CSP.create_org(new_org_name, AUTH, PROFILE)
    Log.info(f'New org id: {ORG_ID}')

    raw = False
    OUTPUT = CSP.show_oauth_service_definition_id(ORG_ID, AUTH, PROFILE, raw)
    for ITEM in OUTPUT:
        for I in ITEM:
            SERVICE_ID = I['serviceDefinitionId']
            Log.info(f'{SERVICE_ID}')

    # switch to platform user to add to service-id
    AUTH, PROFILE = get_platform_context(ctx)
    RESULT = CSP.add_to_service_id(ORG_ID, SERVICE_ID, AUTH, PROFILE)

@org.command('rename', help='change the display name of a given org', context_settings={'help_option_names':['-h','--help']})
@click.argument('new_org_name', required=True, default=None)
@click.argument('target_org', required=False, default=None)
@click.pass_context
def rename_org(ctx, new_org_name, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.rename_org(target_org, new_org_name, AUTH, PROFILE)
    if OUTPUT:
        Log.json(json.dumps(OUTPUT, indent=2))
    else:
        Log.critical('failed to rename the org')

@org.command('delete', help='delete org - remember to double check the org_id!', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org_id', required=False, default=None)
@click.pass_context
def delete_org(ctx, target_org_id):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org_id is None or ctx.obj['menu'] is True:
        target_org_id, name = MenuResults(ctx)
    OUTPUT = CSP.delete_org(target_org_id, AUTH, PROFILE)
    try:
        if OUTPUT.status_code == 200:
            Log.info('org deleted')
        else:
            Log.critical('failed to delete the org')
    except:
        Log.critical('failed to delete the org')

@org.group(help="manage org properties", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def property(ctx):
    pass

@property.command(name="delete", help='delete a property from an org config | BROKEN', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.argument('property_name', required=True)
@click.pass_context
def org_property_delete(ctx, target_org, property_name):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.org_property_delete(target_org, property_name, AUTH, PROFILE)
    if 'status_code' in OUTPUT:
        if OUTPUT.status_code == 200:
            Log.info('org property deleted')
    else:
        Log.critical('failed to delete org property')

@property.command(name="set", help='add a property to an org config', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.argument('property_name', required=True)
@click.argument('property_value', required=True)
@click.pass_context
def org_property_add(ctx, target_org, property_name, property_value):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.org_property_add(target_org, property_name, property_value, AUTH, PROFILE)
    if 'status_code' in OUTPUT:
        if OUTPUT.status_code == 200:
            Log.info('org property added')
    else:
        Log.critical('failed to add org property')

@property.command(name="default", help='add default set of properties to an org', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False)
@click.pass_context
def org_property_default(ctx, target_org):
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None or ctx.obj['menu'] is True:
        target_org, name = MenuResults(ctx)
    OUTPUT = CSP.org_default_properties(target_org, AUTH, PROFILE)
    if OUTPUT.status_code == 200:
        Log.info('default properties added')
    else:
        Log.critical('failed to add org properties')

org.add_command(user)
org.add_command(org_show, name='show')

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

