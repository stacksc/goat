import click, json
from tempfile import NamedTemporaryFile
from .sddcclient import sddc
from .vmc_misc import get_operator_context
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import SddcMenuResults as MenuResults
from csptools.cspclient import CSPclient

CSP = CSPclient()

@click.group('backup', help='manage SDDC backups', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc_backup(ctx):
    pass

@sddc_backup.command('check', help='verify backup of the SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('backup_result_file', required=True, default=None)
@click.option('-d', '--delete', help='', required=False, is_flag=True, default=False)
@click.pass_context
def sddc_backup_check(ctx, backup_result_file, delete):
    Log.critical('not yet implemented')

@sddc_backup.command('create', help='take a backup of a single or all VMC SDDCs', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=True, default=None)
@click.option('-a', '--auth', 'auth_org', help="org id/name to use for authentication", type=str, required=False, default='operator')
@click.pass_context
def sddc_backup_create(ctx, sddc_id, auth_org):
    if sddc_id is None:
        RESULT = []
        SDDCS = SDDC.VMC.show_sddc_all(True)
        for SDDC in SDDCS:
            SDDCclient = sddc(sddc_id, None, ctx['profile'], auth_org)
            OUTPUT = SDDCclient.backup()
            RESULT.append(OUTPUT)        
    else:
        SDDCclient = sddc(sddc_id, None, ctx['profile'], auth_org)
        RESULT = [ SDDCclient.backup() ]
    RESULT_FILE = NamedTemporaryFile()
    RESULT_FILE_NAME = RESULT_FILE.name
    with open(RESULT_FILE_NAME, 'w') as FILE:
        for ENTRY in RESULT:
            FILE.write(ENTRY)
    Log.info(f"use 'sddc backup check {RESULT_FILE_NAME}' to check the status of this backup request")

@sddc_backup.command('show', help='show all backups for a specific SDDC', context_settings={'help_option_names':['-h','--help']})
@click.argument('sddc_id', required=False, default=None)
@click.option('-n', '--name-only', 'name', help='only show backup names', required=False, default=False, is_flag=True)
@click.pass_context
def sddc_backup_show(ctx, sddc_id, name):
    AUTH, PROFILE = get_operator_context(ctx)
    aws_ready = False
    version_only = False
    raw = False
    if sddc_id is None:
        DATA = []
        target_org, myname = MenuResults(ctx)
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
    RESULT = SDDC.backup_show(name)
    Log.info(json.dumps(RESULT,indent=2))

@click.group('restore', help='restore vCenter or NSX-T from backup', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc_restore(ctx):
    pass

@sddc_restore.command('start', help='restore vCenter or NSX-T from backup', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc_restore_start(ctx):
    Log.critical('not yet implemented')

@sddc_restore.command('status', help='check progress on an active SDDC restore', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc_restore_status(ctx):
    Log.critical('not yet implemented')

@sddc_restore.command('reconciliation-start', help='reconcile past restore of an SDDC', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc_restore_reconciliation(ctx):
    Log.critical('not yet implemented')

@sddc_restore.command('reconciliation-task', help='check progress on an active SDDC reconciliation', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def sddc_restore_reconciliation_task(ctx):
    Log.critical('not yet implemented')

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

