import click, json
from .sddcclient import sddc
from toolbox.logger import Log
from toolbox.menumaker import Menu
from csptools.cspclient import CSPclient
from .vmcclient import vmc
from .vmc_misc import get_operator_context
from toolbox.misc import SddcMenuResults as MenuResults

CSP = CSPclient()

@click.group('vcenter', help='manage vCenter servers in a SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def vcenter(ctx):
    pass

@vcenter.command('ui', help='gain UI access to the vCenter server within an SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('ticket_or_reason', required=True, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-u', '--user', help="username to use for vCenter authentication", type=str, required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def vcenter_ui(ctx, sddc_id, ticket_or_reason, user, raw):
    aws_ready = False
    version_only = False
    AUTH, PROFILE = get_operator_context(ctx)
    VMC = vmc(AUTH, PROFILE)
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
                Log.info(f"gathering vcenter details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.vcenter_ui(ticket_or_reason, user, target_org)
    Log.info(json.dumps(RESULT, indent=2))

@vcenter.command('ssh-toggle', help='enable or disable SSH on an a vCenter server in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('action', required=True, default=None, type=click.Choice(['enable', 'disable']))
@click.argument('ticket_or_reason', required=True, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_ssh_toggle(ctx, action, ticket_or_reason, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    VMC = vmc(AUTH, PROFILE)
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
                Log.info(f"running ssh-toggle for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.vcenter_ssh_toggle(action, ticket_or_reason, raw)
    Log.info(json.dumps(RESULT, indent=2))

@vcenter.command('ssh-verify', help='verify SSH connectivity to the vCenter server', context_settings={'help_option_names':['-h','--help']})
@click.argument('ticket_or_reason', required=True, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_ssh_verify(ctx, sddc_id, ticket_or_reason, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    VMC = vmc(AUTH, PROFILE)
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
                Log.info(f"gathering vcenter details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.vcenter_ssh_verify(ticket_or_reason, raw)
    Log.info(json.dumps(RESULT, indent=2))

@vcenter.group('show', help='show data about the vCenter server in a SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def vcenter_show(ctx):
    pass

@vcenter_show.command('credentials', help='show login credentials for the vCenter server in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def vcenter_show_credentials(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    VMC = vmc(AUTH, PROFILE)
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
                Log.info(f"gathering vcenter details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.vcenter_show_credentials()
    Log.json(json.dumps(RESULT, indent=2))

@vcenter_show.command('url', help='show URLs for the vCenter server in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def vcenter_show_url(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    VMC = vmc(AUTH, PROFILE)
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
                Log.info(f"gathering vcenter details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.vcenter_show_url()
    Log.json(json.dumps(RESULT, indent=2))

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

