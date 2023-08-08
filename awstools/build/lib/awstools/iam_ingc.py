import os, boto3, click, json, base64, random, string, getpass, requests, importlib_resources, subprocess, datetime
from configstore.configstore import Config
from toolbox import misc
from toolbox.logger import Log
from toolbox.menumaker import Menu
from .aws_config import AWSconfig
from requests_ntlm import HttpNtlmAuth
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from toolbox.getpass import getIDPCreds
from toolbox.getpass import password_prompt

CONFIG = AWSconfig()
CONFIGSTORE = Config('awstools')
    
@click.command(help='login using existing IAM creds or add new creds to config with IDP only', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--region', 'aws_region', help='aws region to connect to', required=False, default='us-gov-west-1', show_default=True)
@click.option('-o', '--output', 'aws_output', help='output type for awscli', required=False, default='json', show_default=True)
@click.option('-i', '--idp_url', 'idp_url', help='idp url if different from default', required=False, default='https://adfs.vmwarefed.com/adfs/ls/IdpInitiatedSignOn.aspx?loginToRp=urn:amazon:webservices:govcloud')
@click.pass_context
def authenticate(ctx, aws_region, aws_output, idp_url):
    aws_profile_name = ctx.obj['PROFILE']
    ACCOUNT = None
    MINS = check_time(aws_profile_name)
    if MINS is not False:
        Log.info(f"it has been {MINS} minutes since last profile consumption from: {aws_profile_name}")
    if whoami() != aws_profile_name:
        if MINS >= 30 or MINS is False:
            if MINS is False:
                RESULT, aws_profile_name = _authenticate(idp_url, aws_region=aws_region, aws_output=aws_output, aws_profile_name=aws_profile_name, menu=True)
            else:
                RESULT, aws_profile_name = _authenticate(idp_url, aws_region=aws_region, aws_output=aws_output, aws_profile_name=aws_profile_name, menu=False)
            if RESULT is None:
                Log.critical("setup failed. please verify supplied credentials and try again. settings were not saved")
            else: 
                Log.info("credentials saved successfully")
                cache_all_hack(aws_profile_name)
                update_latest_profile(aws_profile_name)
                Log.info(f"you can now use your profile with 'aws --profile {aws_profile_name} --region {aws_region}")
        else:
            Log.info("credentials saved successfully from a previous session")
            cache_all_hack(aws_profile_name)
            update_latest_profile(aws_profile_name)
            Log.info(f"you can now use your profile with 'aws --profile {aws_profile_name} --region {aws_region}")
    else:
        Log.info(f"assuming role now using menu authentication")
        RESULT, aws_profile_name = _authenticate(idp_url, aws_region=aws_region, aws_output=aws_output, aws_profile_name=aws_profile_name, menu=True)
        if RESULT is None:
            Log.critical("setup failed. please verify supplied credentials and try again. settings were not saved")
        else: 
            Log.info("credentials saved successfully")
            cache_all_hack(aws_profile_name)
            update_latest_profile(aws_profile_name)
            Log.info(f"you can now use your profile with 'aws --profile {aws_profile_name} --region {aws_region}")

def whoami():
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        return None
    else:
        LATEST = LATEST['config']['role']
    return LATEST

def update_latest_profile(aws_profile_name):
    BASICS = Config('awstools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(aws_profile_name, 'role', 'latest')
    else:
        BASICS.update_config(aws_profile_name, 'role', 'latest')

def _authenticate(idp_url, aws_region=None, aws_output=None, aws_profile_name='default', menu=False):
    CONFIG.unset_aws_profile()
    if 'IDP' not in CONFIGSTORE.PROFILES:
        CONFIGSTORE.create_profile('IDP')
    if aws_profile_name not in CONFIGSTORE.PROFILES:
        CONFIGSTORE.create_profile(aws_profile_name)
    if idp_url is None:
        IDP_URL = CONFIGSTORE.get_config('IDP_URL', 'IDP')
        if IDP_URL is None:
           IDP_URL = CONFIG.get_from_config('config', 'IDP_URL', 'input', 'Enter IDP URL: ', 'IDP')
           IDP_URL = IDP_URL.strip()
           CONFIGSTORE.update_config(IDP_URL, 'IDP_URL', 'IDP')
    else:
        IDP_URL = idp_url
        CONFIGSTORE.update_config(IDP_URL, 'IDP_URL', 'IDP')
    AWS_REGION = CONFIG.get_from_config('config', 'region', 'string', 'us-gov-west-1', aws_profile_name, aws_region)
    AWS_OUTPUT = CONFIG.get_from_config('config', 'output', 'string', 'json', aws_profile_name, aws_output)
    STAMP = create_timestamp()
    SAML_ASSERTION = idp_login(IDP_URL, aws_profile_name)
    AWS_ROLES = get_aws_roles(SAML_ASSERTION)
    if menu is True:
        if len(AWS_ROLES) > 1:
            INPUT = f"Please choose the role you'd like to assume: "
            CHOICE = runMenu(AWS_ROLES, INPUT)
            if CHOICE:
                AWS_ROLE = ''.join(CHOICE)
                ROLE_ARN = AWS_ROLE.split('\t')[0].strip()
                PRINCIPAL_ARN = AWS_ROLE.split('\t')[1].strip()
                aws_profile_name = ROLE_ARN.split('/')[1]
                ACCOUNT = find_account_number(ROLE_ARN)
            else:
                Log.critical("please choose a valid role for assumption")
        else:
            ROLE_ARN = AWS_ROLES[0].split(',')[0]
            PRINCIPAL_ARN = AWS_ROLES[0].split(',')[1]
            ACCOUNTS, DICT = get_prod_roles()
            if ACCOUNTS:
                INPUT = f"Please choose the role you'd like to assume: "
                CHOICE = runMenu(ACCOUNTS, INPUT)
                if CHOICE:
                    LIST = ''.join(CHOICE)
                    ROLENAME = LIST.split('\t')[0].strip()
                    ACCOUNT = DICT[ROLENAME]
                    aws_profile_name = ROLENAME.split('/')[1]
                else:
                    Log.critical("please choose a valid role for assumption")
    else:
        ROLE_ARN = CONFIGSTORE.get_config('role', f'{aws_profile_name}')
        PRINCIPAL_ARN = CONFIGSTORE.get_config('principal', f'{aws_profile_name}')
        ACCOUNT = find_account_number(ROLE_ARN)
    if aws_profile_name not in CONFIGSTORE.PROFILES:
        CONFIGSTORE.create_profile(aws_profile_name)
    ACCESS_KEY, SECRET_KEY, TOKEN = get_aws_client_saml('sts', SAML_ASSERTION, ROLE_ARN, PRINCIPAL_ARN, AWS_REGION)
    if ACCESS_KEY is not None and TOKEN is not None:
        CONFIG.add_aws_profile_saml(ACCESS_KEY, SECRET_KEY, TOKEN, AWS_REGION, AWS_OUTPUT, aws_profile_name)
        CONFIG.set_aws_profile(TOKEN, AWS_REGION, AWS_OUTPUT)
        CONFIGSTORE.update_config(ROLE_ARN, 'role', f'{aws_profile_name}')
        CONFIGSTORE.update_config(PRINCIPAL_ARN, 'principal', f'{aws_profile_name}')
        CONFIGSTORE.update_config(STAMP, 'updated_at', f'{aws_profile_name}')
    SESSION_NAME = os.environ["LOGNAME"] + '-PowerUser'
    if ACCOUNT is None:
        Log.info("unable to find a mapped shadow account. you will need to provide that now.")
        ACCOUNT = CONFIG.get_from_config('creds', 'account_number', 'input', 'Enter account number for assumption: ', aws_profile_name)
    CONFIGSTORE.update_config(ACCOUNT, 'power_account', f'{aws_profile_name}')
    ROLE_ARN = f'arn:aws-us-gov:iam::{ACCOUNT}:role/PowerUser'
    CONFIGSTORE.update_config(ROLE_ARN, 'power_role', f'{aws_profile_name}')
    CLIENT = get_aws_session(aws_profile_name, ROLE_ARN, SESSION_NAME, aws_region, aws_output)
    return CLIENT, aws_profile_name
  
def create_timestamp():

    NOW = datetime.datetime.now()
    FMT = '%Y-%m-%d %H:%M:%S'
    STAMP = NOW.strftime(FMT)
    return STAMP

def check_time(aws_profile_name):
    NOW = datetime.datetime.now()
    FMT = '%Y-%m-%d %H:%M:%S'
    UPDATED = CONFIGSTORE.get_config('updated_at', f'{aws_profile_name}')
    try:
        UPDATED_OBJ = datetime.datetime.strptime(UPDATED, FMT)
        TD = NOW - UPDATED_OBJ
        TD_MINS = int(round(TD.total_seconds() / 60))
        return TD_MINS
    except:
        return False

def idp_login(idp_url, aws_profile_name):

    IDP_USER = CONFIGSTORE.get_config('IDP_USER', 'IDP')
    IDP_PASS = CONFIGSTORE.get_config('IDP_PASS', 'IDP')

    if IDP_USER is None or IDP_PASS is None:
        while True:
            IDP_USER, IDP_PASS = getIDPCreds()
            if IDP_USER != '' and IDP_PASS != '':
                CONFIGSTORE.update_config(IDP_PASS, 'IDP_PASS', 'IDP')
                CONFIGSTORE.update_config(IDP_USER, 'IDP_USER', 'IDP')
                break
    SESSION = requests.session()
    SESSION.auth = HttpNtlmAuth(IDP_USER, IDP_PASS, SESSION)
    RESPONSE = SESSION.get(idp_url, verify=True)
    SOUP = BeautifulSoup(RESPONSE.text, features="html.parser")
    PAYLOAD = {}
    for TAG in SOUP.find_all('input'):
        NAME = TAG.get('name','')
        VALUE = TAG.get('value','')
        if "user" in NAME.lower():
            PAYLOAD[NAME] = IDP_USER
        elif "email" in NAME.lower():
            PAYLOAD[NAME] = IDP_USER
        elif "pass" in NAME.lower():
            PAYLOAD[NAME] = IDP_PASS
        else:
            PAYLOAD[NAME] = VALUE
    for TAG in SOUP.find_all('form'):
        ACTION = TAG.get('action')
        LOGIN_ID = TAG.get('id')
        if (ACTION and LOGIN_ID == "loginForm"):
            PARSED_URL = urlparse(idp_url)
            SUBMIT_URL = PARSED_URL.scheme + "://" + PARSED_URL.netloc + ACTION
    RESPONSE = SESSION.post(
        SUBMIT_URL, data=PAYLOAD, verify=True)
    SOUP = BeautifulSoup(RESPONSE.text, features="html.parser")
    SAML_ASSERTION = ''
    for TAG in SOUP.find_all('input'):
        if(TAG.get('name') == 'SAMLResponse'):
            SAML_ASSERTION = TAG.get('value')
    if (SAML_ASSERTION == ''):
        Log.critical('Response did not contain a valid SAML assertion')
    return SAML_ASSERTION
    
def get_aws_client_saml(type, saml_assertion, role_arn, principal_arn, aws_region):
    try:
        CLIENT = boto3.client(type, region_name=aws_region)
        CREDS = CLIENT.assume_role_with_saml(RoleArn=role_arn, PrincipalArn=principal_arn, SAMLAssertion=saml_assertion)
        return CREDS['Credentials']['AccessKeyId'], CREDS['Credentials']['SecretAccessKey'], CREDS['Credentials']['SessionToken']
    except:
        Log.critical('Failed to retrieve AWS IAM credentials')
        return None, None, None

def get_aws_roles(saml_assertion):
    AWS_ROLES = []
    ROOT = ElementTree.fromstring(base64.b64decode(saml_assertion))
    for ATTRIBUTE in ROOT.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
        if (ATTRIBUTE.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
            for ATTRIBUTE_VALUE in ATTRIBUTE.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                AWS_ROLES.append(ATTRIBUTE_VALUE.text)
    for ROLE in AWS_ROLES:
        BITS = ROLE.split(',')
        if 'saml-provider' in BITS[0]:
            AWS_ROLE = BITS[1] + ',' + BITS[0]
            INDEX = AWS_ROLES.index(ROLE)
            AWS_ROLES.insert(INDEX, AWS_ROLE)
            AWS_ROLES.remove(ROLE)
    return AWS_ROLES

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
        elif MODULE == 'ec2':
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_instances', aws_profile_name))
            except:
                pass
        elif MODULE == 'rds':
            CACHED = {}
            try:
                CACHED.update(CONFIG.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'])
            except:
                pass
        if not CACHED:
            Log.info(f'caching {MODULE} data...')
            run_command(f'goat aws -p {aws_profile_name} {MODULE} show')

def run_command(command):
    PROC = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'AWS Auth Menu: {INPUT}'
    for data in DATA:
        COUNT = COUNT + 1
        RESULTS = []
        role = data.split(',')[0].ljust(75)
        principal =  data.split(',')[1]
        RESULTS.append(role + "\t" + principal)
        FINAL.append(RESULTS)
    SUBTITLE = f'showing {COUNT} available object(s)'
    JOINER = '\t\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, SUBTITLE)
    CHOICE = FINAL_MENU.display()
    return CHOICE

def get_aws_session(aws_profile_name, role_arn, session_name, aws_region, aws_output):

    SESSION = boto3.Session(profile_name=aws_profile_name)
    STS = SESSION.client('sts')
    try:
        RESPONSE = STS.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name
        )
    except:
        Log.critical(f'unable to assume role: {role_arn}')

    SESSION = boto3.Session(aws_access_key_id=RESPONSE['Credentials']['AccessKeyId'],
                        aws_secret_access_key=RESPONSE['Credentials']['SecretAccessKey'],
                        aws_session_token=RESPONSE['Credentials']['SessionToken']
    )
    CONFIG.add_aws_profile_saml(RESPONSE['Credentials']['AccessKeyId'], 
                                RESPONSE['Credentials']['SecretAccessKey'],
                                RESPONSE['Credentials']['SessionToken'],
                                aws_region, aws_output, aws_profile_name
    )
    CONFIG.set_aws_profile(RESPONSE['Credentials']['SessionToken'], aws_region, aws_output)
    return SESSION

def find_account_number(role):
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "prod_accounts.lst")
    with open(DATA) as f:
        CONTENTS = f.read()
        for line in CONTENTS.split('\n'):
            if role in line:
                return line.split(",")[1]
    return None

def get_prod_roles():
    NAMES = []
    DICT = {}
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "prod_accounts.lst")
    with open(DATA) as f:
        CONTENTS = f.read()
        for line in CONTENTS.split('\n'):
            if line:
                ALIAS = line.split(",")[0]
                ACCOUNT = line.split(",")[1]
                ARN = line.split(",")[2]
                NAMES.append(ARN + "," + ALIAS)
                DICT[ARN] = ACCOUNT
    return NAMES, DICT

def get_role_session(aws_key_id, aws_secret_access_key, aws_session_token):
    try:
        SESSION = boto3.Session(
            aws_access_key_id=aws_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )
    except:
        return None
    return SESSION

@click.command('reset-password', help='reset and update IDP credentials in the configstore', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def reset_password(ctx):
    IDP_USER = CONFIGSTORE.get_config('IDP_USER', 'IDP')
    if IDP_USER is None:
        return False
    while True:
        IDP_PASS = password_prompt()
        if IDP_PASS != '':
            CONFIGSTORE.update_config(IDP_PASS, 'IDP_PASS', 'IDP')
            break

def get_latest_profile_data(ctx):

    AWS_PROFILE = ctx.obj['PROFILE']
    LATEST = CONFIGSTORE.get_profile('latest')

    if not AWS_PROFILE and LATEST is None:
        AWS_PROFILE = 'default'
    elif not AWS_PROFILE and LATEST is not None:
        AWS_PROFILE = LATEST['config']['role']

    if AWS_PROFILE != 'default':
        print('\n' + misc.GREEN + misc.UNDERLINE + AWS_PROFILE + misc.RESET)
        IDP_URL = CONFIGSTORE.get_config('IDP_URL', 'IDP')
        IDP_USER = CONFIGSTORE.get_config('IDP_USER', 'IDP')
        ROLE_ARN = CONFIGSTORE.get_config('role', f'{AWS_PROFILE}')
        PRINCIPAL_ARN = CONFIGSTORE.get_config('principal', f'{AWS_PROFILE}')
        POWER_ACCOUNT = CONFIGSTORE.get_config('power_account', f'{AWS_PROFILE}')
        POWER_ROLE = CONFIGSTORE.get_config('power_role', f'{AWS_PROFILE}')
        AWS_REGION = CONFIG.get_from_config('config', 'region', 'string', 'us-gov-west-1', AWS_PROFILE, None)
        AWS_OUTPUT = CONFIG.get_from_config('config', 'output', 'string', 'json', AWS_PROFILE, None)
        MINS = check_time(AWS_PROFILE)
        print(f'IDP URL:    {IDP_URL}')
        print(f'IDP USER:   {IDP_USER}')
        print(f'ROLE ARN:   {ROLE_ARN}')
        print(f'PRINCIPAL:  {PRINCIPAL_ARN}')
        print(f'POWER_ROLE: {POWER_ROLE}')
        print(f'AWS REGION: {AWS_REGION}')
        print(f'AWS OUTPUT: {AWS_OUTPUT}')
        print(f'ASSUMED:    {MINS} minutes ago')
    else:
        Log.critical('please authenticate before showing profile details')
    return

def print_role_info(KEY_ID, ACCESS_TOKEN, SESSION_TOKEN):
    EXPORT_CMDS = f"\nexport AWS_ACCESS_KEY_ID={KEY_ID}\nexport AWS_SECRET_ACCESS_KEY={ACCESS_TOKEN}\nexport AWS_SESSION_TOKEN={SESSION_TOKEN}\nexport AWS_DEFAULT_REGION=us-gov-west-1"
    SCRIPT = f"#!/bin/bash\n\n{EXPORT_CMDS}"
    HOME = os.environ['HOME']
    with open(f"{HOME}/goatrole.sh", 'w') as SCRIPT_FILE:
        SCRIPT_FILE.write(SCRIPT)
        MODE = os.stat(f"{HOME}/goatrole.sh").st_mode
        MODE |= (MODE & 0o444) >> 2
        os.chmod(f"{HOME}/goatrole.sh", MODE)
    Log.info("run source ~/goatrole.sh")

