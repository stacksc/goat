import click, boto3, string, random, subprocess
from .aws_config import AWSconfig
from .accounts import get_accounts
from toolbox.logger import Log
from os import environ, chmod, stat
from configstore.configstore import Config
from toolbox.misc import set_terminal_width

CONFIG = AWSconfig()

@click.command(help='login using existing IAM creds or add new creds to config', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-r', '--region', 'aws_region', help='aws region to connect to', required=False, default='us-east-1')
@click.option('-o', '--output', 'aws_output', help='output type for awscli', required=False, default='json')
@click.pass_context
def authenticate(ctx, aws_region, aws_output):
    profile_name = ctx.obj['PROFILE']
    RESULT = _authenticate(profile_name, aws_region, aws_output)
    if RESULT is None:
        MSG = 'setup failed. please verify supplied credentials and try again. settings were not saved'
        LINK = 'https://github.com/stacksc/goat'
        CMD = None
        SUBTITLE = 'CRITICAL'
        TITLE = 'GOAT'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    else:
        Log.info("credentials saved successfully")
        cache_all_hack(profile_name, aws_region)
        Log.info(f"you can now use your new profile with 'aws --profile {profile_name}")
        update_latest_profile(profile_name)
        MSG = f'{profile_name} credentials saved successfully!'
        LINK = None
        CMD = None
        SUBTITLE = 'INFO'
        TITLE = 'GOAT'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)

# worker function to make the method portable
def _authenticate(profile_name, aws_region='us-east-1', aws_output='json'):
    CONFIG.unset_aws_profile()
    AWS_REGION = CONFIG.get_from_config('config', 'region', 'string', 'us-east-1', profile_name, aws_region)
    AWS_OUTPUT = CONFIG.get_from_config('config', 'output', 'string', 'json', profile_name, aws_output)
    AWS_KEY_ID, AWS_SECRET_ACCESS_KEY = get_env_variables()
    if AWS_KEY_ID is None or AWS_SECRET_ACCESS_KEY is None:
        AWS_KEY_ID = CONFIG.get_from_config('creds', 'aws_access_key_id', 'input', 'Please enter AWS_KEY_ID: ', profile_name)
        AWS_SECRET_ACCESS_KEY = CONFIG.get_from_config('creds', 'AWS_SECRET_ACCESS_KEY', 'secure', 'Please enter AWS_SECRET_ACCESS_KEY: ', profile_name)
    SESSION = get_aws_session(AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    if SESSION is not None:
        CONFIG.add_aws_profile(AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_OUTPUT, profile_name)
    return SESSION

def update_latest_profile(aws_profile_name):
    BASICS = Config('awstools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(aws_profile_name, 'role', 'latest')
    else:
        BASICS.update_config(aws_profile_name, 'role', 'latest')

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "")

def get_aws_session(aws_key_id, aws_secret_access_key, aws_region):
    CONFIG.unset_aws_profile()
    try:
        SESSION = boto3.Session(
            aws_access_key_id=aws_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
    except:
        return None
    return SESSION

def get_role_session(aws_key_id, aws_secret_access_key, aws_session_token):
    CONFIG.unset_aws_profile()
    try:
        SESSION = boto3.Session(
            aws_access_key_id=aws_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
    except:
        return None
    return SESSION

def get_env_variables():
    try:
       aws_access_key_id = environ['AWS_ACCESS_KEY_ID']
       aws_secret_access_key = environ['AWS_SECRET_ACCESS_KEY']
       return aws_access_key_id, aws_secret_access_key
    except:
        return None, None

def get_aws_roles(aws_session):
    CLIENT = aws_session.client('iam')
    RESULT = []
    for ROLE in CLIENT.list_roles()['Roles']:
        RESULT.append(ROLE['Arn'])
    return RESULT

def print_role_info(KEY_ID, ACCESS_TOKEN, SESSION_TOKEN):
    EXPORT_CMDS = f"\nexport AWS_ACCESS_KEY_ID={KEY_ID}\nexport AWS_SECRET_ACCESS_KEY={ACCESS_TOKEN}\nexport AWS_SESSION_TOKEN={SESSION_TOKEN}"
    SCRIPT = f"#!/bin/bash\n\n{EXPORT_CMDS}"
    HOME = environ['HOME']
    with open(f"{HOME}/goatrole.sh", 'w') as SCRIPT_FILE:
        SCRIPT_FILE.write(SCRIPT)
        MODE = stat(f"{HOME}/goatrole.sh").st_mode
        MODE |= (MODE & 0o444) >> 2
        chmod(f"{HOME}/goatrole.sh", MODE)
    Log.info("run source ~/goatrole.sh")

def force_cache(aws_profile_name, aws_region_name):
    CONFIG = Config('awstools')
    Log.info('aws profile caching initialized')
    MODULES = ['s3', 'ec2', 'rds']
    for MODULE in MODULES:
        Log.info(f'caching {MODULE} data...')
        run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')

def cache_all_hack(aws_profile_name, aws_region_name):
    CONFIG = Config('awstools')
    Log.info('aws profile caching initialized')
    MODULES = ['s3', 'ec2', 'rds']
    for MODULE in MODULES:
        if MODULE == 's3':
            CACHED = {}
            FOUND = False
            try:
                CACHED.update(CONFIG.get_metadata('cached_buckets', aws_profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')
            elif CACHED:
                for REGION in CACHED:
                    if aws_region_name == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')
        elif MODULE == 'ec2':
            CACHED = {}
            FOUND = False
            try:
                CACHED.update(CONFIG.get_metadata('cached_instances', aws_profile_name))
            except:
                pass
            if not CACHED:
                Log.info(f'caching {MODULE} data...')
                run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')
            elif CACHED:
                for REGION in CACHED:
                    if aws_region_name == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')
        elif MODULE == 'rds':
            CACHED = {}
            FOUND = False
            try:
                CACHED.update(CONFIG.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'])
            except:
                pass
            if not CACHED:
                Log.info(f'caching {MODULE} data...')
                run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')
            elif CACHED:
                for REGION in CACHED:
                    if aws_region_name == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat aws -r {aws_region_name} -p {aws_profile_name} {MODULE} show')

def run_command(command):
    PROC = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
