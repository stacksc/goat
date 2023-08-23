import click, os, json
from toolbox.logger import Log
from .iamclient import IAMclient
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from toolbox.menumaker import Menu
from datetime import datetime
from datetime import timedelta

CONFIG = Config('ocitools')
IGNORE = ['latest']

@click.group('compartment', invoke_without_command=True, help='module to manage compartments for tenant', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform compartment actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def compartment(ctx, menu):
    profile_name = ctx.obj['PROFILE']
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@compartment.command(help='manually refresh comparments stored in cache', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _refresh('cached_compartments', oci_region, profile_name)

def _refresh(cache_type, oci_region, profile_name):
    try:
        if cache_type == 'cached_compartments':
            IAM = get_IAMclient(profile_name, oci_region, auto_refresh=False, cache_only=False)
            RESULT = IAM.refresh('cached_compartments', profile_name)
        return True
    except:
        False

@compartment.command(help='create OCI compartment for region and tenant', context_settings={'help_option_names':['-h','--help']})
@click.argument('compartment', required=True)
@click.option('-d', '--description', help='provide a short description for the new compartment', required=False, type=str, default=None)
@click.pass_context
def create(ctx, compartment, description):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _create(ctx, profile_name, oci_region, compartment, description)

def _create(ctx, profile_name, oci_region, compartment,  description):
    IAM = get_IAMclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    for PROFILE in CONFIG.PROFILES:
        if PROFILE in IGNORE:
            continue
        CACHED_COMPARTMENTS = IAM.get_compartments()
        DATA = []
        for COMPARTMENT in CACHED_COMPARTMENTS:
            if COMPARTMENT.lifecycle_state != 'ACTIVE':
                continue
            COMP_NAME = str(COMPARTMENT.name).ljust(50)
            COMP_OCID = str(COMPARTMENT.id).ljust(100)
            STR = COMP_OCID + '\t' + COMP_NAME
            DATA.append(STR)
    INPUT = f'Compartments => {profile_name}'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        OCID = CHOICE.split('\t')[0].strip()
        NAME = CHOICE.split('\t')[1].strip()
    else:
        Log.critical('please choose a compartment')

    Log.info(f'creating compartment {compartment} in compartment {NAME}')
    if description is None: description = compartment
    RESPONSE = IAM.create_compartment(OCID, compartment, description)
    if RESPONSE:
        Log.info(f'{compartment} has been created in compartment level {NAME}')
    else:
        Log.critical(f'problem while creating compartment {compartment}')
    
@compartment.command(help='menu-guided solution to delete OCI compartment\'s for region and tenant', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def delete(ctx):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _delete(ctx, profile_name, oci_region)

def _delete(ctx, profile_name, oci_region):
    IAM = get_IAMclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    for PROFILE in CONFIG.PROFILES:
        if PROFILE in IGNORE:
            continue
        CACHED_COMPARTMENTS = IAM.get_compartments()
        DATA = []
        for COMPARTMENT in CACHED_COMPARTMENTS:
            if COMPARTMENT.lifecycle_state != 'ACTIVE':
                continue
            COMP_NAME = str(COMPARTMENT.name).ljust(50)
            COMP_OCID = str(COMPARTMENT.id).ljust(100)
            STR = COMP_OCID + '\t' + COMP_NAME
            DATA.append(STR)
    INPUT = f'Compartments => {profile_name}'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        OCID = CHOICE.split('\t')[0].strip()
        NAME = CHOICE.split('\t')[1].strip()
    else:
        Log.critical('please choose a compartment for deletion')
    Log.info(f'deleting compartment {NAME}')
    RESPONSE = IAM.delete_compartment(OCID)
    if RESPONSE:
        Log.info(f'{NAME} has been deleted with response:')
        print(RESPONSE)
    else:
        Log.critical(f'problem while deleting compartment {NAME}; response is: {RESPONSE}')

@compartment.command(help='show the data stored in cached compartments', context_settings={'help_option_names':['-h','--help']})
@click.argument('compartment', required=False)
@click.pass_context
def show(ctx, compartment):
    profile_name = ctx.obj['PROFILE']
    _show(ctx, profile_name, compartment)

def _show(ctx, profile_name, compartment):
    if not compartment:
        if ctx.obj["MENU"]:
            DATA = []
            DICT = {}
            IAM = get_IAMclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = IAM.get_cached_compartments(profile_name)
            for I in RESPONSE:
                if I not in 'last_cache_update':
                    NAME = RESPONSE[I]['name'].ljust(50)
                    DATA.append(I.ljust(100) + '\t' + NAME)
            INPUT = 'Compartment Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE)
                OCID = CHOICE.split('\t')[0].strip()
            except:
                Log.critical("please select a compartment to continue...")
            Log.info(f"describing {OCID}:")
            RESPONSE = IAM.describe(OCID, profile_name)
            for I in RESPONSE:
                print(RESPONSE[I])
        else:
            IAM = get_IAMclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = IAM.get_cached_compartments(profile_name)
            show_as_table(RESPONSE)
    else:
        IAM = get_IAMclient(profile_name, auto_refresh=False, cache_only=True)
        RESPONSE = IAM.describe(compartment)
        Log.info(f"describing {compartment}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data):
    IGNORE = ['last_cache_update']
    DATADICT = {}
    DATA = []
    try:
        for I in source_data:
            if I not in IGNORE:
                DATA.append(source_data[I])
                if DATA:
                    DATADICT = DATA
        if DATADICT != []:
            Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}\n")
    except:
        return None

def get_IAMclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = IAMclient(profile_name, region, cache_only)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Compartment Menu: {INPUT}'
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

def get_region(ctx, profile_name):
    OCI_REGION = ctx.obj['REGION']
    if not OCI_REGION:
        IAM = get_IAMclient(profile_name)
        OCI_REGION = IAM.get_region_from_profile(profile_name)
    return OCI_REGION
