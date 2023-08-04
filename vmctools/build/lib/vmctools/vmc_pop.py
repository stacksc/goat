import click, json, os
from .vmcclient import vmc
from .vmc_misc import get_operator_context
from toolbox.logger import Log
from csptools.cspclient import CSPclient
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import SddcMenuResults as MenuResults

CSP = CSPclient()

@click.group(help="connect to, manage and view info about SDDC's POP instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def pop(ctx):
    pass

@pop.command('request', help='request access to POP for an SDDC')
@click.argument('target_org', required=True)
@click.argument('sddc_id', required=True)
@click.option('-r', '--reason', help='supply a reason for POP access (required in prod)', default=None, required=False)
@click.option('-t', '--token_access', help='use a token to request access to POP and ESX', default=False, is_flag=True, required=False)
@click.pass_context
def pop_request(ctx, sddc_id, target_org, reason, token_access):
    if reason is None:
        if detect_environment() == 'gc-prod':
            Log.critical('reason is required in production environment')
        else:
            reason = 'testing. please ignore'
    auth, user_profile = get_operator_context(ctx)
    ORG_ID = lookup_org(user_profile, target_org)
    VMC = vmc(auth, user_profile)
    RESULT = VMC.pop_request(sddc_id, target_org, reason, token_access)
    if RESULT.status_code == 200:
        Log.info(RESULT)
    elif RESULT.status_code == 400:
        Log.critical(f'{sddc_id} SDDC in {target_org} is not in a healthy state')
    elif RESULT.status_code == 403:
        Log.critical(f'you are missing permissions for POP for {sddc_id} SDDC in {target_org}')

@pop.command('connect', help='connect to POP associated with a specific SDDC')
@click.argument('sddc_id', required=True)
@click.pass_context
def pop_connect(ctx, sddc_id):
    auth, user_profile = get_operator_context(ctx)
    VMC = vmc(auth, user_profile)
    pass

@pop.group('show', help='show info about POP')
def pop_show():
    pass

@pop_show.command('details', help='show details about a POP instance for a given SDDC in a specific org')
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def pop_show_all(ctx, target_org, sddc_id, raw):
    aws_ready = False
    version_only = False
    auth, user_profile = get_operator_context(ctx)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, auth, user_profile, raw)
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
                Log.info(f"gathering sddc details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    VMC = vmc(auth, user_profile)
    RESULT = VMC.pop_show_all(sddc_id, target_org)
    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
    if RESULT.status_code == 200:
        Log.info(json.loads(RESULT.json, ident=4))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    elif RESULT.status_code == 401 or RESULT.status_code == 403:
        Log.critical('operator is not authorised to use this POP instance')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')
    
def detect_environment():
    try:
        DOMAIN = os.getenv('USER').split('@')[1]
        ENVS = {
            "vmwarefed.com": 'gc-prod',
            "vmwarefedstg.com": 'gc-stg',
            "vmware.smil.mil": 'ohio-sim'
        }
        RESULT = ENVS[DOMAIN]
    except:
        Log.debug('Unable to get user domain; assuming non-gc environment (ie VMware issued macbook)')
        return 'non-gc'
    return RESULT

def lookup_org(user_profile, target_org):
    ORG_ID = CSP.get_org_ids(user_profile, target_org)
    return ORG_ID

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

