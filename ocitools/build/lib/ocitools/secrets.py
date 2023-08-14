import click, os, json
from toolbox.logger import Log
from .secretsclient import SECRETclient
from tabulate import tabulate
from configstore.configstore import Config
from toolbox.misc import set_terminal_width, decode_string
from .iam import get_latest_profile
from toolbox.menumaker import Menu

CONFIG = Config('ocitools')

class my_dict(dict):
    def subdict(self, keywords, fragile=False):
        d = {}
        for k in keywords:
            try:
                d[k] = self[k]
            except KeyError:
                if fragile:
                    raise
        return d

@click.group('secret', invoke_without_command=True, help='module to manage secrets', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform DBS actions', is_flag=True, show_default=True, default=False, required=False)
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
                    ID = RESPONSE[I]['id'].ljust(50)
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
        SECRETS = get_SECRDTclient(profile_name, auto_refresh=False, cache_only=True)
        RESPONSE = SECRETS.describe(secret, profile_name)
        Log.info(f"describing {secret}:\n" + json.dumps(RESPONSE, indent=2, sort_keys=True, default=str))

def show_as_table(source_data, decrypt):
    IGNORE = ['last_cache_update']
    DATADICT = {}
    DATA = []
    try:
        for I in source_data:
            if I not in IGNORE:
                SECRET = source_data[I]['content']
                if decrypt:
                    SECRET = decode_string(SECRET)
                    source_data[I]['content'] = SECRET
                DATA.append(source_data[I])
                if DATA:
                    DATADICT = DATA
        if DATADICT != []:
            Log.info(f"\n{tabulate(DATADICT, headers='keys', tablefmt='rst')}\n")
    except:
        return None

def get_SECRETclient(profile_name, region='us-ashburn-1', auto_refresh=True, cache_only=False):
    CLIENT = SECRETclient(profile_name, region, cache_only)
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
