import click, json
from .sddcclient import sddc
from .vmc_misc import get_operator_context
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from csptools.cspclient import CSPclient
from toolbox.misc import SddcMenuResults as MenuResults

CSP = CSPclient()

@click.group('esx', help='manage ESXi hosts making up the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def esx(ctx):
    pass

@esx.command('ssh-toggle', help='enable or disable SSH on an ESXi host in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('action', required=True, default=None, type=click.Choice(['enable', 'disable']))
@click.argument('sddc_id', required=False, default=None)
@click.argument('esx_name', required=False, default=None)
@click.option('-t', '--ticket', 'ticket', help="CSSD or CSCM ticket asssociated with the RTS task", type=str, required=False, default='CSSD-1234', show_default=True)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_ssh_toggle(ctx, sddc_id, esx_name, action, ticket, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
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
                Log.info(f"gathering esx details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    if esx_name is None:
        RESULT = SDDC.esx_show_names()
        HOSTS = []
        for HOST in RESULT:
            HOSTS.append(HOST['name'])
        INPUT = 'esx manager'
        CHOICE = runMenu(HOSTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            esx_name = CHOICE
            if esx_name:
                Log.info(f"toggling ssh for {esx_name} now, please wait...")
            else:
                Log.critical("please select an esx-name to continue...")
        else:
            Log.critical("please select an esx-name to continue...")

    RESULT = SDDC.esx_ssh_toggle(esx_name, action, ticket, raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        if RESULT['status'] != "FAILED":
            Log.info(RESULT['status'])
            for I in RESULT['data'].replace(",","\n").split('\n'):
                line = listToStringWithoutBrackets(I).replace('"','').split(':')
                if line[0] == "output":
                    Log.info(line[1].strip() + " => " + str(line[2:]))
                else:
                    Log.info(line[0].strip() + " => " + str(line[1:]))
        else:
            Log.json(json.dumps(RESULT, indent=2))
            Log.critical(f"esx ssh toggle to {action} on {esx_name} FAILED")

@esx.group('show', help='show data about the ESXi hosts in a SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def esx_show(ctx):
    pass

@esx_show.command('all', help='list ESXi hosts running under a given SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_show_all(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
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
                Log.info(f"gathering sddc details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")
 
    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.esx_show_all(raw)
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.info(json.dumps(RESULT, indent=2))

@esx_show.command('details', help='show details about a specific ESXi host in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('esx_name', required=False, default=None)
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_show_details(ctx, esx_name, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
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
                Log.info(f"gathering esx details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    if esx_name is None:
        RESULT = SDDC.esx_show_names()
        HOSTS = []
        for HOST in RESULT:
            HOSTS.append(HOST['name'])
        INPUT = 'esx manager'
        CHOICE = runMenu(HOSTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            esx_name = CHOICE
            if esx_name:
                Log.info(f"gathering esx details for {esx_name} now, please wait...")
            else:
                Log.critical("please select an esx-name to continue...")
        else:
            Log.critical("please select an esx-name to continue...")
    RESULT = SDDC.esx_show_details(esx_name, raw)
    Log.info(json.dumps(RESULT, indent=2))

@esx_show.command('credentials', help='show login credentials for ESXi in a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_show_credentials(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
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
                Log.info(f"gathering esx details for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.esx_show_credentials()
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.json(json.dumps(RESULT, indent=2))

@esx_show.command('witness', help='show VSAN witness host IP in a specific SDDC (use raw for all fields)', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def esx_show_witness(ctx, sddc_id, raw):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
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
                Log.info(f"gathering sddc information for {SDDC_NAME} now, please wait...")
            else:
                Log.critical("please select an sddc-name to continue...")
        else:
            Log.critical("please select an sddc-name to continue...")

    SDDC = sddc(sddc_id, AUTH, PROFILE, None)
    RESULT = SDDC.esx_show_witness()
    if RESULT == []:
        Log.critical('something went wrong when connecting to the SDDC')
    else:
        Log.info(json.dumps(RESULT, indent=2))

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

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace("{","").replace("}","")
