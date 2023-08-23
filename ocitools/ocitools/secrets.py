import click, os, json
from toolbox.logger import Log
from .secretsclient import SECRETclient
from .vaultclient import VAULTclient
from tabulate import tabulate
from .misc import get_random_password
from configstore.configstore import Config
from toolbox.misc import set_terminal_width, decode_string
from .iam import get_latest_profile
from toolbox.menumaker import Menu

CONFIG = Config('ocitools')
IGNORE = ['latest']

@click.group('secrets', invoke_without_command=True, help='module to manage secrets', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform secret actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def secrets(ctx, menu):
    profile_name = ctx.obj['PROFILE']
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    pass

@secrets.command(help='manually refresh secrets stored in cache', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    _refresh('cached_secrets', profile_name)

def _refresh(cache_type, profile_name):
    try:
        if cache_type == 'cached_secrets':
            SECRETS = get_SECRETclient(profile_name, auto_refresh=False)
            RESULT = SECRETS.refresh('cached_secrets', profile_name)
        return True
    except:
        False

@secrets.command(help='create OCI secrets for region and tenant', context_settings={'help_option_names':['-h','--help']})
@click.option('-n', '--name', help='secret name', default=None, required=True, type=str)
@click.option('-d', '--description', help='short description for the secret; default uses the name of the secret as the description', default=None, required=False, type=str)
@click.option('-c', '--content', help='secret content; default creates a random 16 character password', default=None, required=False, type=str)
@click.pass_context
def create(ctx, name, description, content):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    if content is None:
        import base64
        content = get_random_password(12)
        content_bytes = content.encode('ascii')
        base64_bytes = base64.b64encode(content_bytes)
        content = base64_bytes.decode("ascii")
    else:
        import base64
        content_bytes = content.strip().encode('ascii')
        base64_bytes = base64.b64encode(content_bytes)
        content = base64_bytes.decode("ascii")
    _create(ctx, profile_name, oci_region, name, description, content)

def _create(ctx, profile_name, oci_region, name, description, content):
    if description is None:
        description = name
    VAULT = get_VAULTclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    SECRET = get_SECRETclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
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
    DATA = []
    VAULTS = VAULT.get_vaults(COMP_OCID)
    for V in VAULTS:
        if V.lifecycle_state not in 'ACTIVE':
            continue
        VAULT_NAME = V.display_name.ljust(25)
        VAULT_OCID = V.id.ljust(50)
        ENDPOINT = V.management_endpoint
        DATA.append(VAULT_OCID + '\t' + VAULT_NAME + '\t' + ENDPOINT)
    INPUT = f'Vaults => {profile_name}'
    CHOICE = runMenu(DATA, INPUT)
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        VAULT_OCID = CHOICE.split('\t')[0].strip()
        VAULT_NAME = CHOICE.split('\t')[1].strip()
        ENDPOINT = CHOICE.split('\t')[2].strip()
    else:
        Log.critical('please choose a vault for secret creation')
    DATA = []
    Log.info(f'creating related AES encrypted key, please wait...')
    RESPONSE = SECRET.create_key(name, COMP_OCID, ENDPOINT)
    KEY_NAME = RESPONSE.display_name.ljust(25)
    KEY_OCID = RESPONSE.id.ljust(50)
    Log.info(f'creating the base64 secret now, please wait...')
    if KEY_OCID:
        RESPONSE = SECRET.create_secret(COMP_OCID, content, name, VAULT_OCID, KEY_OCID, description)
        if RESPONSE:
            Log.info(f'completed the creation of secret name {name}')
            print(RESPONSE)

@secrets.command(help='menu-guided solution to delete OCI secrets for region and tenant', context_settings={'help_option_names':['-h','--help']})
@click.option('-a', '--all', help='delete all secrets found', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def delete(ctx, all):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _delete(ctx, profile_name, oci_region, all)

def _delete(ctx, profile_name, oci_region, all):
    VAULT = get_VAULTclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
    SECRET = get_SECRETclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
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
        OCID = CHOICE.split('\t')[0].strip()
        NAME = CHOICE.split('\t')[1].strip()
    else:
        Log.critical('please choose a compartment')
    SECRETS = SECRET.list_secrets(OCID)
    DATA = []
    for S in SECRETS:
        if S.lifecycle_state not in 'ACTIVE':
            continue
        SECRET_NAME = S.secret_name.ljust(50)
        OCID = S.id.ljust(100)
        DATA.append(OCID + '\t' + SECRET_NAME)
    if all is not True:
        INPUT = f'Secrets => {profile_name}'
        CHOICE = runMenu(DATA, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            OCID = CHOICE.split('\t')[0].strip()
            SECRET_NAME = CHOICE.split('\t')[1].strip()
        else:
            Log.critical('please choose a secret for deletion')
        Log.info(f'deleting secret {SECRET_NAME} in compartment {NAME}')
        RESPONSE = SECRET.delete_secret(OCID).data
    else:
        for S in SECRETS:
            if S.lifecycle_state not in 'ACTIVE':
                continue
            SECRET_NAME = S.secret_name.ljust(50)
            OCID = S.id.ljust(100)
            DATA.append(OCID + '\t' + SECRET_NAME)
            Log.info(f'deleting secret {SECRET_NAME} in compartment {NAME}')
            RESPONSE = SECRET.delete_secret(OCID).data

@secrets.command(help='show the secrets stored in cache', context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--decrypt', help='decrypt secret content of type base64', is_flag=True, show_default=True, default=False, required=False)
@click.argument('secret', required=False)
@click.pass_context
def show(ctx, decrypt, secret):
    profile_name = ctx.obj['PROFILE']
    _show(ctx, profile_name, secret, decrypt)

def _show(ctx, profile_name, secret, decrypt):
    if not secret:
        if ctx.obj["MENU"]:
            DATA = []
            DICT = {}
            SECRETS = get_SECRETclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = SECRETS.get_cached_secrets(profile_name)
            for I in RESPONSE:
                if I not in 'last_cache_update':
                    NAME = RESPONSE[I]['secret_name']
                    ID = I.ljust(50)
                    DATA.append(ID + '\t' + NAME)
            INPUT = 'Secrets Manager'
            CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE)
                OCID = CHOICE.split('\t')[0].strip()
            except:
                Log.critical("please select a secret to continue...")
            RESPONSE = SECRETS.describe(OCID, profile_name)
            DATA = {}
            Log.info(f"describing {OCID}:")
            for I in RESPONSE:
                if 'content' in I:
                    SECRET = RESPONSE[I]
                    continue
                print(RESPONSE[I])
            print("************************************************************")
            print(f"INFO: secret content is: {SECRET}")
            if decrypt:
                SECRET = decode_string(SECRET)
                print(f"INFO: decoded secret is: {SECRET}")
            print("************************************************************")
        else:
            SECRETS = get_SECRETclient(profile_name, auto_refresh=False, cache_only=True)
            RESPONSE = SECRETS.get_cached_secrets(profile_name)
            show_as_table(RESPONSE, decrypt)
    else:
        SECRETS = get_SECRETclient(profile_name, auto_refresh=False, cache_only=True)
        RESPONSE = SECRETS.describe(secret, profile_name)
        Log.info(f"describing {secret}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data, decrypt):
    IGNORE = ['last_cache_update']
    DATADICT = {}
    DATA = []
    try:
        for I in source_data:
            if I not in IGNORE:
                if decrypt:
                    try:
                        SECRET = decode_string(source_data[I]['content'])
                        source_data[I]['content'] = SECRET
                    except:
                        pass
                DATA.append(source_data[I])
                if DATA:
                    DATADICT = DATA
        if DATADICT != []:
            Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}\n")
    except:
        return None

def get_SECRETclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = SECRETclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def get_VAULTclient(profile_name, region='us-ashburn-1', auto_refresh=True, cache_only=False):
    CLIENT = VAULTclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Secrets Menu: {INPUT}'
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
