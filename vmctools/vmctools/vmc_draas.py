import click, json
from toolbox.logger import Log
from .vmcclient import vmc
from .vmc_misc import get_operator_context
from configstore.configstore import Config
from toolbox.menumaker import Menu
from csptools.cspclient import CSPclient
from toolbox.misc import SddcMenuResults as MenuResults

CSP = CSPclient()
CONFIG = Config('csptools')

@click.group(help="manage and view info about draas", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def draas(ctx):
    pass

@draas.group('manage', help='manage VMC DraaS')
@click.pass_context
def draas_manage(ctx):
    pass

@draas_manage.command('activate', help='activate site-recovery')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.pass_context
def draas_deactivate(ctx, target_org, sddc_id):
    raw = False
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_activate(target_org, sddc_id)
    if RESULT == 200 or RESULT == 202:
        Log.info(f"activation in process for SDDC: {sddc_id}")
    elif RESULT == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_manage.command('deactivate', help='deactivate site-recovery')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-t', '--ticket', required=True, default=None)
@click.pass_context
def draas_deactivate(ctx, target_org, sddc_id, ticket):
    raw = False
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_prepare_deactivate(target_org, sddc_id)
    if RESULT == 200 or RESULT == 202:
        Log.info(f"deactivation in process for SDDC: {sddc_id}")
    elif RESULT == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')
    RESULT = VMC.draas_show_details(sddc_id, target_org)
    DICT = RESULT.json
    try:
        DEL_CONFIRM_CODE = DICT["custom_properties"]["prepareDeleteConfirmCode"]
        if DEL_CONFIRM_CODE:
            RESULT = VMC.draas_deactivate(target_org, sddc_id, DEL_CONFIRM_CODE, ticket=ticket)
            if RESULT == 200 or RESULT == 202:
                Log.info(f"deactivation is running now; please wait and poll DRaaS details until completion.")
            elif RESULT == 204:
                Log.critical('no active access exists for the operator')
            else:
                Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT}')
        else:
            Log.critical(f"unable to deactivate DRaaS for SDDC: {sddc_id} and org: {target_org}")
    except:
        Log.critical(f"unable to deactivate DRaaS for SDDC: {sddc_id} and org: {target_org}")

@draas.group('show', help='show info about VMC DRaaS')
@click.pass_context
def draas_show(ctx):
    pass

@draas_show.command('pairings', help='show details about draas SRM/VR pairings')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_pairings(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas pairings for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_pairings(target_org, sddc_id)
    if RESULT.status_code == 200 or RESULT.status_code == 202:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('permissions', help='show details about draas permissions')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_permissions(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas permissions for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_permissions(sddc_id, target_org)
    if RESULT.status_code == 200 or RESULT.status_code == 202:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('hms', help='retrieve draas hms tasks information for the specified SDDC')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_plan(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering HMS tasks information for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_hms_tasks_info(target_org, sddc_id)
    if RESULT.status_code == 200:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('plan', help='retrieve draas site-recovery plans for the specified SDDC')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_plan(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas plans for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_plan(target_org, sddc_id)
    if RESULT.status_code == 200:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('bundle', help='download the support bundle for a specific task-id')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.argument('task_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_get_bundle(ctx, target_org, sddc_id, task_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas support-bundle for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_tasks(target_org)
    DATA = []
    if RESULT.status_code == 200:
        for I in RESULT.json:
            STATUS = I['status'].rjust(10)
            ID = I['id'].ljust(30)
            TYPE = I['task_type'].rjust(40)
            STR = ID + '\t' + STATUS + '\t' + TYPE
            DATA.append(STR)
        DATA.sort()
        INPUT = 'draas task manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            task_id = CHOICE.split('\t')[0].strip()
            if not task_id:
                Log.critical("please select a task-id to continue")
        OUTPUT = VMC.draas_get_support_bundle(target_org, task_id)
        if OUTPUT.status_code == 200:
            Log.json(json.dumps(OUTPUT.json, indent=2, sort_keys=True))
        elif OUTPUT.status_code == 204:
            Log.critical('no active access exists for the operator')
        else:
            Log.critical(f'unexpected result while calling the API: HTTPS response: {OUTPUT.status_code}')
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('versions', help='show details about draas versions')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_versions(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas versions for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_versions(sddc_id, target_org)
    if RESULT.status_code == 200 or RESULT.status_code == 202:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('task', help='show details about a specific draas task-id')
@click.argument('target_org', required=False, default=None)
@click.argument('task_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_task_details(ctx, target_org, task_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None:
        target_org, name = MenuResults(ctx)

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_tasks(target_org)
    DATA = []
    if RESULT.status_code == 200:
        for I in RESULT.json:
            STATUS = I['status'].rjust(10)
            ID = I['id'].ljust(30)
            TYPE = I['task_type'].rjust(40)
            STR = ID + '\t' + STATUS + '\t' + TYPE
            DATA.append(STR)
        DATA.sort()
        INPUT = 'draas task manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            task_id = CHOICE.split('\t')[0].strip()
            if not task_id:
                Log.critical("please select a task-id to continue")
        else:
            Log.critical("please select a task-id to continue")
        OUTPUT = VMC.draas_show_task_details(target_org, task_id.strip())
        if OUTPUT:
            if OUTPUT.status_code == 200:
                Log.json(json.dumps(OUTPUT.json, indent=2, sort_keys=True))
            elif OUTPUT.status_code == 204:
                Log.critical('no active access exists for the operator')
            else:
                Log.critical(f'unexpected result while calling the API: HTTPS response: {OUTPUT.status_code}')
        else:
            Log.critical(f'unexpected result while calling the API')
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('tasks', help='show details about draas tasks')
@click.argument('target_org', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_tasks(ctx, target_org, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if target_org is None:
        target_org, name = MenuResults(ctx)

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_tasks(target_org)
    if RESULT.status_code == 200 or RESULT.status_code == 202:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

@draas_show.command('details', help='show details about draas')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def draas_show_details(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            sddc_id = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering draas details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.draas_show_details(sddc_id, target_org)
    if RESULT.status_code == 200 or RESULT.status_code == 202:
        Log.json(json.dumps(RESULT.json, indent=2, sort_keys=True))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'VMC Menu: {INPUT}'
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

