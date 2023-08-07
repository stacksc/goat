import click, boto3, string, random, subprocess
from .aws_config import AWSconfig
from .accounts import get_accounts
from toolbox.logger import Log
from os import environ, chmod, stat
from configstore.configstore import Config
from toolbox.misc import set_terminal_width

CONFIG = AWSconfig()

@click.command(help='login using existing IAM creds or add new creds to config', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-r', '--region', 'aws_region', help='aws region to connect to', required=False, default='us-gov-west-1')
@click.option('-o', '--output', 'aws_output', help='output type for awscli', required=False, default='json')
@click.pass_context
def authenticate(ctx, aws_region, aws_output):
    profile_name = ctx.obj['PROFILE']
    RESULT = _authenticate(profile_name, aws_region, aws_output)
    if RESULT is None:
        MSG = 'setup failed. please verify supplied credentials and try again. settings were not saved'
        LINK = 'https://gitlab.eng.vmware.com/govcloud-ops/govcloud-devops-python/-/blob/main/awstools/README.md'
        CMD = None
        SUBTITLE = 'CRITICAL'
        TITLE = 'PYPS'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    else:
        Log.info("credentials saved successfully")
        cache_all_hack(profile_name)
        Log.info(f"you can now use your new profile with 'aws --profile {profile_name}")
        update_latest_profile(profile_name)
        MSG = f'{profile_name} credentials saved successfully!'
        LINK = None
        CMD = None
        SUBTITLE = 'INFO'
        TITLE = 'PYPS'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)

# worker function to make the method portable
def _authenticate(profile_name, aws_region='us-gov-west-1', aws_output='json'):
    CONFIG.unset_aws_profile()
    AWS_REGION = CONFIG.get_from_config('config', 'region', 'string', 'us-gov-west-1', profile_name, aws_region)
    AWS_OUTPUT = CONFIG.get_from_config('config', 'output', 'string', 'json', profile_name, aws_output)
    AWS_KEY_ID, AWS_SECRET_ACCESS_KEY = get_env_variables()
    if AWS_KEY_ID is None or AWS_SECRET_ACCESS_KEY is None:
        AWS_KEY_ID = CONFIG.get_from_config('creds', 'aws_access_key_id', 'input', 'Please enter AWS_KEY_ID: ', profile_name)
        AWS_SECRET_ACCESS_KEY = CONFIG.get_from_config('creds', 'AWS_SECRET_ACCESS_KEY', 'secure', 'Please enter AWS_SECRET_ACCESS_KEY: ', profile_name)
    SESSION = get_aws_session(AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    if SESSION is not None:
        CONFIG.add_aws_profile(AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_OUTPUT, profile_name)
    return SESSION

@click.command('assume-role', help='login using existing IAM creds or add new creds to config', context_settings={'help_option_names':['-h','--help']})
@click.argument('aws_profile_name', nargs=-1, type=str)
@click.option('-r', '--role', 'aws_role_name', help='name of the role to assume; i.e. PowerUser', required=False, default='PowerUser')
@click.option('-c', '--creds', 'creds_profile_name', help='aws credential file to source for the IAM credentials', required=False, default=None)
@click.option('-a', '--account', 'aws_account_number', help='aws account number to register new IAM credentials', required=False, default=None)
def assume_role(aws_profile_name, aws_role_name, creds_profile_name, aws_account_number):
    CONFIG.unset_aws_profile()
    aws_profile_name = ''.join(aws_profile_name)
    SESSION, KEY_ID, ACCESS_TOKEN, SESSION_TOKEN = _assume_role(aws_account_number, aws_profile_name, creds_profile_name, aws_role_name)
    if SESSION_TOKEN is None:
        Log.critical("failed to assume the role. most likely you supplied incorrect profile to source for IAM authentication")
        MSG = f'failed to assume the role; {aws_profile_name} is an incorrect profile to source'
        LINK = None
        CMD = None
        SUBTITLE = 'CRITICAL'
        TITLE = 'PYPS'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
    else:
        Log.info("successfully assumed the role")
        cache_all_hack(aws_profile_name)
        print_role_info(KEY_ID, ACCESS_TOKEN, SESSION_TOKEN)
        update_latest_profile(aws_profile_name)
        MSG = f'{aws_profile_name} has been assumed successfully!'
        LINK = None
        CMD = None
        SUBTITLE = 'INFO'
        TITLE = 'PYPS'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)

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

def _assume_role(aws_account_number=None, aws_profile_name=None, creds_profile=None, aws_role=None):
    if aws_account_number is None:
        AWS_ROLE_ARN = CONFIG.get_from_config('creds', 'role_arn', 'string', "", aws_profile_name)
        if AWS_ROLE_ARN == "":
            try:
                aws_account_number = listToStringWithoutBrackets(get_accounts(aws_profile_name))
                AWS_ROLE_ARN = f"arn:aws-us-gov:sts::{aws_account_number}:role/{aws_role}"
            except:
                MSG = 'Please supply an AWS account number when assuming a role for the first time'
                LINK = 'https://gitlab.eng.vmware.com/govcloud-ops/govcloud-devops-python/-/blob/main/awstools/README.md'
                Log.notify(MSG, LINK)
                Log.critical(MSG)
    else:
        AWS_ROLE_ARN = f"arn:aws-us-gov:sts::{aws_account_number}:role/{aws_role}"
    if aws_profile_name == 'default':
        Log.critical(f'{aws_profile_name} is not allowed for this method; please choose a different name')
    CREDS_PROFILE = CONFIG.get_from_config('creds', 'source_profile', 'string', 'default', aws_profile_name, creds_profile)
    CREDS_SESSION = _authenticate(CREDS_PROFILE)
    AWS_REGION = CONFIG.get_from_config('config', 'region', 'string', 'us-gov-west-1', aws_profile_name)
    AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN = get_role_iam(CREDS_SESSION, AWS_ROLE_ARN, AWS_REGION)
    if AWS_SECRET_ACCESS_KEY is not None:
        CONFIG.unset_aws_profile()
        CONFIG.config_add_role(aws_profile_name, AWS_ROLE_ARN, CREDS_PROFILE)
    SESSION = get_role_session(AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
    return SESSION, AWS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

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

def get_role_iam(session, role_arn, aws_region):
    try:
        RANDOM_NAME = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        CLIENT = session.client('sts', region_name=aws_region)
        CREDS = CLIENT.assume_role(
            RoleArn=role_arn,
            RoleSessionName=RANDOM_NAME)
        return CREDS['Credentials']['AccessKeyId'], CREDS['Credentials']['SecretAccessKey'], CREDS['Credentials']['SessionToken']
    except:
        Log.critical('failed to retrieve AWS IAM credentials')

def print_role_info(KEY_ID, ACCESS_TOKEN, SESSION_TOKEN):
    EXPORT_CMDS = f"\nexport AWS_ACCESS_KEY_ID={KEY_ID}\nexport AWS_SECRET_ACCESS_KEY={ACCESS_TOKEN}\nexport AWS_SESSION_TOKEN={SESSION_TOKEN}"
    SCRIPT = f"#!/bin/bash\n\n{EXPORT_CMDS}"
    HOME = environ['HOME']
    with open(f"{HOME}/pypsrole.sh", 'w') as SCRIPT_FILE:
        SCRIPT_FILE.write(SCRIPT)
        MODE = stat(f"{HOME}/pypsrole.sh").st_mode
        MODE |= (MODE & 0o444) >> 2
        chmod(f"{HOME}/pypsrole.sh", MODE)
    Log.info("run source ~/pypsrole.sh")

def cache_all_hack(aws_profile_name):
    CONFIG = Config('awstools')
    Log.info('aws profile caching initialized')
    MODULES = ['s3', 'ec2', 'rds']
    for MODULE in MODULES:
        if MODULE == 's3':
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_buckets', aws_profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                run_command(f'pyps aws -p {aws_profile_name} {MODULE} show')
        elif MODULE == 'ec2':
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_instances', aws_profile_name))
            except:
                pass
            if not CACHED:
                Log.info(f'caching {MODULE} data...')
                run_command(f'pyps aws -p {aws_profile_name} {MODULE} show')
        elif MODULE == 'rds':
            CACHED = {}
            try:
                CACHED.update(CONFIG.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'])
            except:
                pass
            if not CACHED:
                Log.info(f'caching {MODULE} data...')
                run_command(f'pyps aws -p {aws_profile_name} {MODULE} show')

def run_command(command):
    PROC = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

