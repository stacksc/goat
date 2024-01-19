import click, os, json
from toolbox.logger import Log
from .keysclient import KEYclient
from .vaultclient import VAULTclient
from tabulate import tabulate
from .misc import get_random_password
from configstore.configstore import Config
from toolbox.misc import set_terminal_width, decode_string
from .iam import get_latest_profile
from toolbox.menumaker import Menu
from datetime import datetime
from datetime import timedelta

CONFIG = Config('ocitools')
IGNORE = ['latest']

@click.group('keys', invoke_without_command=True, help='module to manage vault keys', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform key actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def keys(ctx, menu):
    profile_name = ctx.obj['PROFILE']
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@keys.command(help='manually refresh keys stored in cache', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    _refresh('cached_keys', profile_name)

def _refresh(cache_type, profile_name):
    try:
        if cache_type == 'cached_keys':
            KEYS = get_KEYclient(profile_name, auto_refresh=False)
            RESULT = KEYS.refresh('cached_keys', profile_name)
        return True
    except:
        False

@keys.command(help='create OCI keys for region and tenant', context_settings={'help_option_names':['-h','--help']})
@click.option('-n', '--name', help='secret name', default=None, required=True, type=str)
@click.option('-d', '--description', help='short description for the secret; default uses the name of the secret as the description', default=None, required=False, type=str)
@click.pass_context
def create(ctx, name, description):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _create(ctx, profile_name, oci_region, name, description)

def _create(ctx, profile_name, oci_region, name, description):
    if description is None:
        description = name
    VAULT = get_VAULTclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    KEYS = get_KEYclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    for PROFILE in CONFIG.PROFILES:
        if PROFILE in IGNORE:
            continue
        CACHED_COMPARTMENTS = VAULT.get_compartments()
        DATA = []
        for COMPARTMENT in CACHED_COMPARTMENTS:
            COMP_NAME = str(COMPARTMENT.name).ljust(50)
            COMP_OCID = str(COMPARTMENT.id).ljust(100)
            STR = COMP_OCID + '\t' + COMP_NAME
            DATA.append(STR)
    INPUT = f'Compartments => {profile_name}'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        COMP_OCID = CHOICE.split('\t')[0].strip()
        COMP_NAME = CHOICE.split('\t')[1].strip()
    else:
        Log.critical('please choose a compartment')
    VAULTS = VAULT.get_vaults(COMP_OCID)
    DATA = []
    for MYVAULT in VAULTS:
        if MYVAULT.lifecycle_state not in 'ACTIVE':
            continue
        VAULT_NAME = MYVAULT.display_name.ljust(25)
        VAULT_OCID = MYVAULT.id.ljust(50)
        ENDPOINT = MYVAULT.management_endpoint
        DATA.append(VAULT_OCID + '\t' + VAULT_NAME + '\t' + ENDPOINT)
    INPUT = f'Vaults => {profile_name}'
    CHOICE = runMenu(DATA, INPUT) 
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        VAULT_OCID = CHOICE.split('\t')[0].strip()
        VAULT_NAME = CHOICE.split('\t')[1].strip()
        ENDPOINT = CHOICE.split('\t')[2].strip()
    else:
        Log.critical('please choose a vault to create a key')
    DATA = []
    Log.info(f'creating AES encrypted key, please wait...')
    RESPONSE = KEYS.create_key(name, COMP_OCID, ENDPOINT)
    if RESPONSE:
        print(RESPONSE)
    else:
        Log.critical(f'problem while creating key {name}')

@keys.command(help='menu-guided solution to delete OCI keys for region and tenant', context_settings={'help_option_names':['-h','--help']})
@click.option('-a', '--all', help='delete all keys found', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def delete(ctx, all):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _delete(ctx, profile_name, oci_region, all)

def _delete(ctx, profile_name, oci_region, all):
    VAULT = get_VAULTclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    KEYS = get_KEYclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    for PROFILE in CONFIG.PROFILES:
        if PROFILE in IGNORE:
            continue
        CACHED_COMPARTMENTS = VAULT.get_compartments()
        DATA = []
        for COMPARTMENT in CACHED_COMPARTMENTS:
            COMP_NAME = str(COMPARTMENT.name).ljust(50)
            COMP_OCID = str(COMPARTMENT.id).ljust(100)
            STR = COMP_OCID + '\t' + COMP_NAME
            DATA.append(STR)
    INPUT = f'Compartments => {profile_name}'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        COMP_OCID = CHOICE.split('\t')[0].strip()
        COMP_NAME = CHOICE.split('\t')[1].strip()
    else:
        Log.critical('please choose a compartment')
    VAULTS = VAULT.get_vaults(COMP_OCID)
    DATA = []
    for MYVAULT in VAULTS:
        if MYVAULT.lifecycle_state not in 'ACTIVE':
            continue
        VAULT_NAME = MYVAULT.display_name.ljust(25)
        VAULT_OCID = MYVAULT.id.ljust(50)
        ENDPOINT = MYVAULT.management_endpoint
        DATA.append(VAULT_OCID + '\t' + VAULT_NAME + '\t' + ENDPOINT)
    INPUT = f'Vaults => {profile_name}'
    CHOICE = runMenu(DATA, INPUT) 
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        VAULT_OCID = CHOICE.split('\t')[0].strip()
        VAULT_NAME = CHOICE.split('\t')[1].strip()
        ENDPOINT = CHOICE.split('\t')[2].strip()
    else:
        Log.critical('please choose a vault to search for keys')
    
    DAYS = datetime.now() + timedelta(days=15)
    RESULT = KEYS.list_keys(COMP_OCID, ENDPOINT)
    if all is not True:
        DATA = []
        for D in RESULT:
            ID = D.id.ljust(50)
            NAME = D.display_name.ljust(20)
            STATE = D.lifecycle_state
            DATA.append(ID + '\t' + NAME + '\t' + STATE)
        INPUT = f'Keys => {profile_name}'
        CHOICE = runMenu(DATA, INPUT) 
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            KEY_OCID = CHOICE.split('\t')[0].strip()
            KEY_NAME = CHOICE.split('\t')[1].strip()
            STATE = CHOICE.split('\t')[2].strip()
        else:
            Log.critical('please choose a key to delete')
        Log.info(f'scheduling deletion of key {KEY_NAME} in compartment {COMP_NAME} for vault {VAULT_NAME}')
        RESPONSE = KEYS.schedule_deletion_key(DAYS, KEY_OCID, ENDPOINT)
        if RESPONSE:
            Log.info(f'{KEY_NAME} is now pending deletion on {DAYS}')
        else:
            Log.critical(f'problem while scheduling the deletion of {KEY_NAME}')
    else:
        for D in RESULT:
            ID = D.id
            NAME = D.display_name
            STATE = D.lifecycle_state
            if STATE != 'PENDING_DELETION':
                Log.info(f'scheduling deletion of key {NAME} in compartment {COMP_NAME} for vault {VAULT_NAME}')
                RESPONSE = KEYS.schedule_deletion_key(DAYS, ID, ENDPOINT)
                if RESPONSE:
                    Log.info(f'{NAME} is now pending deletion on {DAYS}')
                else:
                    Log.critical(f'problem while scheduling the deletion of {NAME}')

@keys.command(help='show the keys stored in cache', context_settings={'help_option_names':['-h','--help']})
@click.argument('key', required=False)
@click.pass_context
def show(ctx, key):
    profile_name = ctx.obj['PROFILE']
    _show(ctx, profile_name, key)

def _show(ctx, profile_name, key):
    if not key:
        if ctx.obj["MENU"]:
            DATA = []
            DICT = {}
            KEYS = get_KEYclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = KEYS.get_cached_keys(profile_name)
            for I in RESPONSE:
                if I not in 'last_cache_update':
                    NAME = RESPONSE[I]['secret_name']
                    ID = I.ljust(50)
                    DATA.append(ID + '\t' + NAME)
            INPUT = 'Key Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE)
                OCID = CHOICE.split('\t')[0].strip()
            except:
                Log.critical("please select a key to continue...")
            RESPONSE = KEYS.describe(OCID, profile_name)
            DATA = {}
            Log.info(f"describing {OCID}:")
            for I in RESPONSE:
                print(RESPONSE[I])
        else:
            KEYS = get_KEYclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = KEYS.get_cached_keys(profile_name)
            show_as_table(RESPONSE)
    else:
        KEYS = get_KEYclient(profile_name, auto_refresh=False, cache_only=True)
        RESPONSE = KEYS.describe(key, profile_name)
        Log.info(f"describing {key}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

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

def get_KEYclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = KEYclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def get_VAULTclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = VAULTclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Key Menu: {INPUT}'
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
        VAULT = get_VAULTclient(profile_name)
        OCI_REGION = VAULT.get_region_from_profile(profile_name)
    return OCI_REGION
