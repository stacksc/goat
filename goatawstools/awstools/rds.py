import click, os, json
from toolbox.logger import Log
from .rdsclient import RDSclient
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from toolbox.menumaker import Menu

CONFIG = Config('awstools')

@click.group('rds', invoke_without_command=True, help='rds to manage the DB instances and related configuration', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform EC2 actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def rds(ctx, menu):
    aws_profile_name = ctx.obj['PROFILE']
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@rds.command(help='manually refresh ec2 cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region = get_region(ctx, aws_profile_name)
    _refresh('cached_rds_instances', aws_profile_name, aws_region)

def _refresh(cache_type, aws_profile_name, aws_region):
    try:
        if cache_type == 'cached_rds_instances':
            RDS = get_RDSclient(aws_profile_name, aws_region, auto_refresh=False)
            RESULT = RDS.refresh('cached_rds_instances', aws_profile_name)
        return True
    except:
        False
    
@rds.command(help='show the data stored in rds cache', context_settings={'help_option_names':['-h','--help']})
@click.argument('database', required=False)
@click.pass_context
def show(ctx, database):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region = get_region(ctx, aws_profile_name)
    _show(ctx, aws_profile_name, aws_region, database)

def _show(ctx, aws_profile_name, aws_region, database):
    if not database:
        if ctx.obj["MENU"]:
            DATA = []
            RDS = get_RDSclient(aws_profile_name, aws_region, auto_refresh=False, cache_only=True)
            RESPONSE = RDS.get_rds_instances()
            for data in RESPONSE:
                ID = data
                DATA.append(ID)
            INPUT = 'RDS Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE) 
            except:
                Log.critical("please select a DB Identifier to continue...")
            RESPONSE = RDS.describe(CHOICE)
            Log.info(f"describing {CHOICE}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))
        else:
            RDS = get_RDSclient(aws_profile_name, aws_region, auto_refresh=False, cache_only=True)
            RESPONSE = RDS.get_rds_instances()
            show_as_table(RESPONSE, name='RDS TABLE')
    else:
        RDS = get_RDSclient(aws_profile_name, aws_region, auto_refresh=False, cache_only=True)
        RESPONSE = RDS.describe(database)
        Log.info(f"describing {database}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data, name=None):
    DATA = []
    for ENTRY in source_data:
        DATA_ENTRY = {}
        if ENTRY != 'last_cache_update':
            DATA_ENTRY['DBInstanceIdentifier'] = ENTRY
            for PROPERTY in source_data[ENTRY]:
                DATA_ENTRY[PROPERTY] = source_data[ENTRY][PROPERTY]
            DATA.append(DATA_ENTRY)
    if DATA != []:
        Log.info(f"{name}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")

def get_RDSclient(aws_profile_name, aws_region='us-east-1', auto_refresh=False, cache_only=True):
    CLIENT = RDSclient(aws_profile_name, aws_region, False, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(aws_profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'RDS Menu: {INPUT}'
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

def get_region(ctx, aws_profile_name):
    AWS_REGION = ctx.obj['REGION']
    if not AWS_REGION:
        RDS = get_RDSclient(aws_profile_name, auto_refresh=False)
        AWS_REGION = RDS.get_region_from_profile(aws_profile_name)
    return AWS_REGION
