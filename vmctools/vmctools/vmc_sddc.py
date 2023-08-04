import sys, os, click, json, datetime
from toolbox.logger import Log
from .vmcclient import vmc
from .vmc_esx import esx, esx_show
from .vmc_nsx import nsx, nsx_show
from .vmc_vcenter import vcenter, vcenter_show
from .vmc_sddc_backup import sddc_restore, sddc_backup
from .vmc_pop import pop, pop_show
from .vmc_draas import draas, draas_show
from .vmc_misc import get_operator_context, get_platform_context
from configstore.configstore import Config
from toolbox.menumaker import Menu
from csptools.cspclient import CSPclient
from toolbox.misc import SddcMenuResults as MenuResults

CSP = CSPclient()

@click.group(help="manage and view info about SDDCs", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@sddc.command('create', help='deploy a new SDDC in VMC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_name', required=True)
@click.option('-n', '--number-of-hosts', 'host_num', help='number of ESXi hosts to deploy in SDDC', required=False, default='1', show_default=True)
@click.option('-p', '--provider', help='cloud provider to use', type=click.Choice(['AWS', 'ZEROCLOUD']), default='AWS', show_default=True)
@click.option('-a', '--account', help='AWS account to use for the deployment', type=str, required=False, default='b02c82ee-8818-3f1e-a176-8624cbaa7996', show_default=True)
@click.option('-m', '--customer-cidr', 'net_cus', help='subnet to use for management network', default='subnet-d7a09691', required=False, show_default=True)
@click.option('-v', '--vpc-cidr', 'net_vpc', help='subnet to use for VPC network', required=False, default='10.2.0.0/16', show_default=True)
@click.option('-t', '--sddc-type', 'sddc_type', help='type of SDDC to deploy', required=False, default='1NODE', show_default=True)
@click.option('-d', '--deployment-type', 'deployment_type', help='single-region or multi-region (stretched) deployment', required=False, type=click.Choice(['SingleAZ', 'MultiAZ']), default='SingleAZ', show_default=True)
@click.option('-s', '--size', 'sddc_size', help='size of the appliances (vCenter, NSX) to deploy', required=False, type=click.Choice(['MEDIUM', 'LARGE']), default='MEDIUM', show_default=True)
@click.option('-i', '--instance-type', 'host_type', help='type of AWS hardware instance to use for deploying ESXi', required=False, default='i3.metal', show_default=True)
@click.option('-r', '--region', 'region', help='target cloud provider region to deploy the SDDC to', required=False, type=click.Choice(['west', 'east']), default='west', show_default=True)
@click.option('-o', '--org', 'org', help='target org to deploy the SDDC to', required=False, default='c16a593b-c32d-4f63-91ae-70abe613fb3a', type=str, show_default=True)
@click.pass_context
def sddc_create(ctx, sddc_name, host_num, provider, account, net_cus, net_vpc, sddc_type, deployment_type, sddc_size, host_type, region, org):
    AUTH, PROFILE = get_operator_context(ctx)
    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.sddc_create(org, sddc_name, host_num, provider, account, net_cus, net_vpc, sddc_type, deployment_type, sddc_size, host_type, region)
    Log.info(json.dumps(RESULT, indent=2))

@sddc.command('delete', help='delete a specific SDDC in a given org', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-f', '--force', help='force the deleton (if its stuck)', is_flag=True, default=False)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.option('-o', '--org', 'org', help='target org to delete the SDDC from', required=False, default=None, type=str)
@click.pass_context
def sddc_delete(ctx, sddc_id, force, raw, org):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    VMC = vmc(AUTH, PROFILE)
    if sddc_id is None or org is None:
        DATA = []
        org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(org, aws_ready, version_only, AUTH, PROFILE, raw)
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
                Log.info(f"deleting {SDDC_NAME} in {name} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    AUTH, PROFILE = get_operator_context(ctx)
    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.org_sddc_delete(org, sddc_id, force, raw)
    Log.info(json.dumps(RESULT, indent=2))

@sddc.command('notify', help='trigger a console notification for the Target Org and SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('target_org', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.pass_context
def console_notify(ctx, target_org, sddc_id):
    raw = False
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
                Log.info(f"triggering console notification for {SDDC_NAME} and {name} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    username = os.environ["LOGNAME"].split("@")[0]
    CURRENT = datetime.datetime.now()
    FORMAT = CURRENT + datetime.timedelta(hours=2)
    expire_date = FORMAT.strftime('%FT%T.%f'"Z")
    RESULT = VMC.console_notification(expire_date, sddc_id, target_org, username)
    if RESULT:
        Log.info(f"triggered console notification with task ID: {RESULT}")
        RESULT = VMC.console_notify_task_verify(RESULT)
        Log.json(json.dumps(RESULT, indent=2))

@sddc.group('show', help='show info about VMC SDDC(s)')
@click.pass_context
def sddc_show(ctx):
    pass

@sddc_show.command('details', help='describe a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-s', '--state', 'state', help="optional state  to search", required=False, type=click.Choice(['DEPLOYING','READY']), default='READY', show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def sddc_show_details(ctx, sddc_id, state, raw=False):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    VMC = vmc(AUTH, PROFILE)
    if sddc_id is None:
        DATA = []
        target_org, name = MenuResults(ctx)
        OUTPUT = CSP.org_show_sddcs(target_org, aws_ready, version_only, AUTH, PROFILE, raw)
        for I in OUTPUT:
            if I['sddc_state'] != state:
                continue
            ID = I['id']
            NAME = I['name'].rjust(50)
            STRING = ID + '\t' + NAME
            DATA.append(STRING)
        INPUT = 'sddc manager'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            SDDC_NAME = CHOICE.split('\t')[1].strip()
            SDDC_ID = CHOICE.split('\t')[0]
            if SDDC_NAME:
                Log.info(f"gathering sddc details for {SDDC_NAME} now, please wait...")
                RESULT = VMC.show_sddc_details(SDDC_ID, raw)
                if RESULT is not None:
                    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
    else:
        RESULT = VMC.show_sddc_details(sddc_id, raw)
        Log.info(json.dumps(RESULT, indent=2))

@sddc_show.command('all', help='show all SDDCs deployed in VMC on AWS', context_settings={'help_option_names':['-h','--help']})
@click.option('-a', '--auth', 'auth_org', help="org id/name to use for authentication", type=str, required=False, default='operator')
@click.option('-o', '--only-aws-ready', 'aws_ready',  help='only show SDDCs in AWS and in READY state', default=False, is_flag=True, required=False)
@click.option('-p', '--pattern', 'pattern', help="find SDDCs using the optional pattern filter", type=str, required=False, default=None)
@click.option('-s', '--state', 'state', help="optional state  to search", required=False, type=click.Choice(['DEPLOYING','READY']), default='READY', show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def sddc_show_all(ctx, auth_org, aws_ready, pattern, state, raw=False):
    AUTH, PROFILE = get_operator_context(ctx)
    VMC = vmc(AUTH, PROFILE)
    RESULT = VMC.show_sddc_all(pattern, state, aws_ready, raw)
    Log.info(json.dumps(RESULT, indent=2))

sddc.add_command(pop)
sddc_show.add_command(pop_show, name='pop')

sddc.add_command(esx)
sddc_show.add_command(esx_show, name='esx')

sddc.add_command(nsx)
sddc_show.add_command(nsx_show, name='nsx')

sddc.add_command(vcenter)
sddc_show.add_command(vcenter_show, name='vcenter')

sddc.add_command(draas)
sddc_show.add_command(draas_show, name='draas')

sddc.add_command(sddc_backup)
sddc.add_command(sddc_restore)

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

