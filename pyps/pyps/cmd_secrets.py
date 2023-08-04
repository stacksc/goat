import sys, click, json, os, datetime, re, time
from toolbox.logger import Log
from awstools.s3client import S3client
from awstools.iam_ingc import authenticate
from awstools.iam import get_latest_profile
from toolbox.click_complete import complete_profile_names, complete_bucket_names
from configstore.configstore import Config
from toolbox.menumaker import Menu
from jenkinstools.jenkinsclient import JenkinsClient
from toolbox.passwords import PasswordstateLookup
from toolbox.getpass import getOtherToken
from idptools.idpclient import IDPclient
from csptools.idpclient import idpc
from csptools.csp_idp import _get_tenants as get_tenants
from csptools.cspclient import CSPclient
from jiratools.issue import create_issue, get_user_profile_based_on_key
from pprint import pprint
from toolbox import misc

JENKINS = JenkinsClient()
CONFIG = Config('awstools')
ignore = ['default','IDP','latest']
MESSAGE="VMware Secrets Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group('secrets', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-m', '--menu', help='use the menu to perform secrets actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def secrets(ctx, menu):
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False
    aws_profile_name = get_latest_profile()
    ctx.obj['PROFILE'] = aws_profile_name

@secrets.command(help='get the secrets bucket policy to verify accessibility', context_settings={'help_option_names':['-h','--help']})
@click.argument('bucket', required=False, default='com.vmw.vmc.govcloud.us-gov-west-1.prd.secrets')
@click.pass_context
def get_policy(ctx, bucket):
    aws_profile_name = ctx.obj['PROFILE']
    CHK = chk_for_profile(aws_profile_name)
    if not CHK:
        Log.info("please authenticate to AWS with the SKS or ATLAS profile to access secrets")
        time.sleep(3)
        os.system('pyps aws iam authenticate')
        aws_profile_name = get_latest_profile()
    if ctx.obj["MENU"] or bucket is None:
        CACHED_BUCKETS = {}
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if PROFILE == aws_profile_name:
                CACHED_BUCKETS.update(CONFIG.get_metadata('cached_buckets', PROFILE))
        INPUT = f'Policy => {aws_profile_name}'
        CHOICE = runMenu(CACHED_BUCKETS, INPUT)
        if CHOICE:
            bucket = ''.join(CHOICE)
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if bucket in CONFIG.get_metadata('cached_buckets', PROFILE):
                    aws_profile_name = PROFILE
                    _get_policy(aws_profile_name, bucket)
                    break
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if bucket in CONFIG.get_metadata('cached_buckets', PROFILE):
                aws_profile_name = PROFILE
                _get_policy(aws_profile_name, bucket)
                break

def _get_policy(aws_profile_name, bucket_name):
    S3 = get_S3client(aws_profile_name)
    RESULT = S3.get_bucket_policy(bucket_name)
    if RESULT:
        Log.info(f"bucket: {bucket_name} policy found successfully.")
        DATA = json.loads(RESULT["Policy"])
        Log.json(json.dumps(DATA, indent=2))
    else:
        Log.critical("failed to find the bucket policy.")

@secrets.command(help='enable or disable VPC access to secrets using policies', context_settings={'help_option_names':['-h','--help']})
@click.argument('mode', required=False, default='on', type=click.Choice(['off', 'on']))
@click.pass_context
def set_policy(ctx, mode, bucket_name):
    aws_profile_name = ctx.obj['PROFILE']
    CHK = chk_for_profile(aws_profile_name)
    if not CHK:
        Log.info("please authenticate to AWS with the SKS or ATLAS profile to access secrets")
        time.sleep(3)
        os.system('pyps aws iam authenticate')
        aws_profile_name = get_latest_profile()
    bucket_name = set_bucket_name(aws_profile_name)
    _set_policy(mode, aws_profile_name, bucket_name)

def _set_policy(mode, aws_profile_name, bucket_name):
    S3 = get_S3client(aws_profile_name)
    RESULT = S3.set_bucket_policy(mode, bucket_name, aws_profile_name)
    if RESULT:
        Log.info(f"bucket policy set successfully on {bucket_name}.")
    else:
        Log.critical(f"failed to set the bucket policy on {bucket_name}.")

@secrets.command(help='generate password function to get a random password', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def generate(ctx):
    ctx.obj['profile'] = ctx.obj['PROFILE']
    IDP = IDPclient(ctx)
    RESULT = IDP.generate_password()
    if RESULT:
        Log.info(RESULT)

@secrets.command(help='rotate tokens for a specific service/username', context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--ticket', help='create a JIRA ticket prior to rolling restart of services', is_flag=True, show_default=True, default=False, required=False)
@click.option('-r', '--restart', help='perform a rolling restart of services', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def token_rotation(ctx, ticket, restart):
    aws_profile_name = ctx.obj['PROFILE']
    REPORT = {}
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    TENANTS = get_tenants()
    TENANTS.sort()
    INPUT = 'Tenant Manager'
    CHOICE = runMenu(TENANTS, INPUT)
    destination = os.environ['HOME']
    if CHOICE:
        CHOICE = ''.join(CHOICE)
        TENANT = CHOICE.split('\t')[1].strip()
        if 'VMwareFed' in TENANT:
            TENANT = 'vmc-prod'
        elif 'customer.local' in TENANT:
            TENANT = 'customer-local'
        elif 'CSP User Local' in TENANT:
            TENANT = 'csp-user-local'
        URL = CHOICE.split('\t')[0].strip()
        REPORT["tenant"] = { 'url': URL }
        Log.info(f'gathering users belonging to tenant {TENANT} => {URL}')
    else:
        Log.critical("please select a tenancy to gather users")

    ctx.obj['profile'] = TENANT
    IDP = IDPclient(ctx)
    username, user = MenuResults(ctx)
    if user is None:
        Log.critical('please select a username to continue')
    Log.info(f'running passsword reset on user ID: {user}')
    password = IDP.generate_password()
    IDP.set_password(user, password)

    print()
    Log.info("log into https://passwordstate.vmwarefed.com and update the password for the account with the one generated")
    Log.info("log into https://console.cloud-us-gov.vmware.com and generate a token manually for the account")
    print("      credentials when logging into the console are:")
    print(f"      username: {username}")
    print(f"      password: {password}")
    print()
    REPORT["creds"] = { 'username': username, 'password': password }

    CHK = chk_for_profile(aws_profile_name)
    if not CHK:
        Log.info("please authenticate to AWS with the SKS or ATLAS profile to access secrets")
        time.sleep(3)
        os.system('pyps aws iam authenticate')
        aws_profile_name = get_latest_profile()

    bucket_name = set_bucket_name(aws_profile_name)
    ANS = input('INFO: press ENTER to continue: ')
    print()
    _set_policy('off', aws_profile_name, bucket_name)
    CACHED_CONTENTS = []
    for PROFILE in CONFIG.PROFILES:
        if PROFILE in ignore:
            continue
        if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
            S3 = get_S3client(PROFILE)
            CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
            if type(CONTENTS) is not bool:
                for content in CONTENTS:
                    CACHED_CONTENTS.append(content['file'])
                CACHED_CONTENTS.sort()
                INPUT = f'Bucket Contents => {aws_profile_name}'
                CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                if CHOICE:
                    CHOICE = ''.join(CHOICE)
                    source = CHOICE
                    if _download(aws_profile_name, bucket_name, destination, source):
                        Log.info(f"downloading {CHOICE} from bucket {bucket_name} completed")
                        break
                    else:
                        Log.critical(f"failed to download {CHOICE} from s3 bucket {source} to {destination}")
                else:
                    Log.critical(f"please select a valid choice to download, exiting.")
    
    if not source or not os.path.exists(destination + "/" + source):
        Log.critical(f"unable to find the secrets file after download in {destination}")

    DICT = {}
    d = destination + "/" + source
    AUTH, PROFILE = get_platform_context(ctx)
    CSP = CSPclient()
    with open(d) as f:
        print()
        for LINE in f:
            if '=' in LINE:
                VAR = LINE.split('=')[0]
                VAL = LINE.split('=')[1]
                if 'TOKEN' in VAR or 'SECRET' in VAR:
                    ANS = input(f'INFO: would you like to modify {VAR} with a new token (y/n)? ')
                    if ANS == 'y' or ANS == 'Y':
                        TOKEN = getOtherToken(f'{VAR}')
                        if TOKEN is None:
                            Log.critical(f"failed to retrieve new token for {VAR}, or token cannot be empty")
                        RESULT = CSP.generate_access_token(TOKEN, PROFILE)
                        if RESULT:
                            Log.info(f"access token:\n{RESULT['token']}")
                            print()
                            # token expire time in hours = 6 months
                            EXPIRE_TIME = set_expire_time(4380)
                            REPORT[VAR] = { 'expiry-timestamp': EXPIRE_TIME, 'refresh-token': TOKEN }
                        VAL = TOKEN
                DICT[VAR] = VAL.strip()

    os.remove(d) if os.path.exists(d) else None
    with open(d, 'a') as f:
        for I in DICT:
            f.write(I + "=" + DICT[I] + '\n')

    with open(d) as f:
        print("\n*************************************************************")
        print(f"{source}")
        print("*************************************************************")
        print(f.read())

    RESULT = input(f"INFO: would you like to upload {source} to {bucket_name}? (y/n): ")
    if 'n' in RESULT or 'N' in RESULT:
        sys.exit()
    print()

    if _upload(d, source, aws_profile_name):
        Log.info(f"uploading local file from {d} to s3 bucket {bucket_name} completed")
    else:
        Log.critical(f"failed to upload local file from {d} to s3 bucket {bucket_name}")

    if ticket is True:
        Log.info("creating a CSSD ticket prior to rolling restart of services now.")
        DESC = 'The PubSecSRE team will be performing a rolling restart of {source} services to prepare for credential rotation.'
        SUMMARY = f'DEPLOYMENT: {source} - rolling restart for new credentials'
        PROJECT = 'CSSD'
        PROFILE = get_user_profile_based_on_key(PROJECT)
        RESULT = create_issue(PROJECT, SUMMARY, DESC, PROFILE)
        if RESULT:
            Log.info("ticket created successfully")
    _set_policy('on', aws_profile_name, bucket_name)
    Log.json(json.dumps(REPORT, indent=2))

@secrets.command(help='upload credential file to S3 secret bucket using a local filepath as the source', context_settings={'help_option_names':['-h','--help']})
@click.argument('credential', required=False, default=None)
@click.option('--source', help="provide a local filepath for upload", type=str, required=True)
@click.pass_context
def upload(ctx, credential, source):
    aws_profile_name = ctx.obj['PROFILE']
    CHK = chk_for_profile(aws_profile_name)
    if not CHK:
        Log.info("please authenticate to AWS with the SKS or ATLAS profile to access secrets")
        time.sleep(3)
        os.system('pyps aws iam authenticate')
        aws_profile_name = get_latest_profile()
    bucket_name = set_bucket_name(aws_profile_name)
    _set_policy('off', aws_profile_name, bucket_name)
    CACHED_CONTENTS = []
    if credential is None:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
                S3 = get_S3client(PROFILE)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS:
                        CACHED_CONTENTS.append(content['file'])
                    CACHED_CONTENTS.sort()
                    INPUT = f'Credentials => {aws_profile_name}'
                    CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        credential = CHOICE
                        if _upload(source, credential, aws_profile_name):
                            Log.info(f"uploading local files from {source} to s3 bucket {bucket_name} completed")
                        else:
                            Log.critical(f"failed to upload local files from {source} to s3 bucket {bucket_name}")
                        break
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
                S3 = get_S3client(PROFILE)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS:
                        if content['file'] == credential:
                            if _upload(source, credential, aws_profile_name):
                                Log.info(f"uploading local files from {source} to s3 bucket {bucket_name} completed")
                            else:
                                Log.critical(f"failed to upload local files from {source} to s3 bucket {bucket_name}")
                            break
    _set_policy('on', aws_profile_name, bucket_name)

def _upload(source, credential, aws_profile_name):

    if (re.search('ATLAS', aws_profile_name, re.IGNORECASE)):
        JOB = 'skylab-s3-secrets-updater-govcloud-atlas-prd'
        user_profile = 'atlas'
        sleeper = 60
    else:
        JOB = 'skylab-s3-secrets-updater-govcloud-prd'
        user_profile = 'delta'
        sleeper = 15

    JSONDICT = {'SERVICE_CREDENTIALS': credential}
    FILES = {'SECRETS_FILE': open(source, 'rb')}
    MYURL = JENKINS.build_url(JOB, merge(JSONDICT,FILES), user_profile=user_profile)
    RESULT = JENKINS.launch_job(JOB, JSONDICT, FILES, wait=True, interval=30, time_out=7200, sleep=sleeper, user_profile=user_profile)
    if RESULT:
        Log.json(json.dumps(RESULT, indent=2))
        return True
    else:
        Log.critical(f"the jenkins job returned an empty result; please look into the job manually:\n{MYURL}.")
        return False
    return True

def merge(dict1, dict2):
    RES = {**dict1, **dict2}
    return RES

@secrets.command(help='download secrets from s3 to local storage', context_settings={'help_option_names':['-h','--help']})
@click.argument('source', required=False, default=None)
@click.option('--destination', help="provide a local destination for download", type=str, required=False, default=os.environ['HOME'], show_default=True)
@click.pass_context
def download(ctx, source, destination):
    aws_profile_name = ctx.obj['PROFILE']
    CHK = chk_for_profile(aws_profile_name)
    if not CHK:
        Log.info("please authenticate to AWS with the SKS or ATLAS profile to access secrets")
        time.sleep(3)
        os.system('pyps aws iam authenticate')
        aws_profile_name = get_latest_profile()
    bucket_name = set_bucket_name(aws_profile_name)
    _set_policy('off', aws_profile_name, bucket_name)
    CACHED_CONTENTS = []
    if source is None:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
                S3 = get_S3client(PROFILE)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS:
                        CACHED_CONTENTS.append(content['file'])
                    CACHED_CONTENTS.sort()
                    INPUT = f'Bucket Contents => {aws_profile_name}'
                    CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        source = CHOICE
                        if _download(aws_profile_name, bucket_name, destination, source):
                            Log.info(f"downloading {CHOICE} from bucket {bucket_name} completed")
                            break
                        else:
                           Log.critical(f"failed to download {CHOICE} from s3 bucket {source} to {destination}")
                    else:
                        Log.critical(f"please select a valid choice to download, exiting.")
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
                S3 = get_S3client(PROFILE)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS:
                        if content['file'] == source:
                            CACHED_CONTENTS.append(content['file'])
                            if _download(aws_profile_name, bucket_name, destination, source):
                                Log.info(f"downloading {source} from bucket {bucket_name} completed")
                                break
                            else:
                                Log.critical(f"failed to download {source} from s3 bucket {bucket_name} to {destination}")
    _set_policy('on', aws_profile_name, bucket_name)

def _download(aws_profile_name, bucket_name, destination, filename):
    S3 = get_S3client(aws_profile_name)
    os.remove(destination + "/" + filename) if os.path.exists(destination + "/" + filename) else None
    try:
        S3.s3_to_local(bucket_name, destination, filename)
        return True
    except:
        return False

@secrets.command(help='show secrets for a specific service from s3 secrets bucket', context_settings={'help_option_names':['-h','--help']})
@click.argument('source', required=False, default=None)
@click.pass_context
def show(ctx, source):
    aws_profile_name = ctx.obj['PROFILE']
    CHK = chk_for_profile(aws_profile_name)
    if not CHK:
        Log.info("please authenticate to AWS with the SKS or ATLAS profile to access secrets")
        time.sleep(3)
        os.system('pyps aws iam authenticate')
        aws_profile_name = get_latest_profile()
    bucket_name = set_bucket_name(aws_profile_name)
    destination = os.environ['HOME']
    _set_policy('off', aws_profile_name, bucket_name)
    CACHED_CONTENTS = []
    if source is None:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
                S3 = get_S3client(PROFILE)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS:
                        CACHED_CONTENTS.append(content['file'])
                    CACHED_CONTENTS.sort()
                    INPUT = f'Bucket Contents => {aws_profile_name}'
                    CACHED_CONTENTS.sort()
                    CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        source = CHOICE
                        if _download(aws_profile_name, bucket_name, destination, source):
                            Log.info(f"showing {source} from bucket {bucket_name}")
                            with open(destination + "/" + source) as f:
                                print("\n*************************************************************")
                                print(f"{source}")
                                print("*************************************************************")
                                print(f.read())
                            os.remove(destination + "/" + source) if os.path.exists(destination + "/" + source) else None
                            break
                        else:
                            Log.critical(f"failed to show {source} from s3 bucket {bucket_name}")
                    else:
                        Log.critical(f"please select a valid choice to download, exiting.")
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if CONFIG.get_metadata('cached_buckets', PROFILE) and bucket_name in CONFIG.get_metadata('cached_buckets', PROFILE):
                S3 = get_S3client(PROFILE)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket_name)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS: 
                        if content['file'] == source:
                            CACHED_CONTENTS.append(content['file'])
                            if _download(aws_profile_name, bucket_name, destination, source):
                                Log.info(f"showing {source} from bucket {bucket_name}")
                                with open(destination + "/" + source) as f:
                                    print("\n*************************************************************")
                                    print(f"{source}")
                                    print("*************************************************************")
                                    print(f.read())
                                os.remove(destination + "/" + source) if os.path.exists(destination + "/" + source) else None
                                break
                            else:
                                Log.critical(f"failed to show {source} from s3 bucket {bucket_name}")
    _set_policy('on', aws_profile_name, bucket_name)

def get_S3client(aws_profile_name, aws_region='us-gov-west-1', auto_refresh=True, cache_only=False):
    try:
        DOMAIN = os.getenv('USER').split('@')[1]
        ENVS = {
            "admins.vmwarefed.com": 'gc-prod',
            "vmwarefedstg.com": 'gc-stg',
            "vmware.smil.mil": 'ohio-sim'
        }
        RESULT = ENVS[DOMAIN]
        CLIENT = S3client(aws_profile_name, aws_region, True, cache_only)
    except:
        CLIENT = S3client(aws_profile_name, aws_region, False, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(aws_profile_name)
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

def MenuResults(ctx):

    DATA = []
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    OUTPUT = IDP.list_users()

    if OUTPUT == []:
        Log.critical(f'unable to find any users for tenant {user_profile}')
    else:
        for i in OUTPUT:
            ID = i['id']
            USERNAME = i['username'].ljust(50)
            STR = USERNAME + "\t" + ID
            DATA.append(STR)
        DATA.sort()
        INPUT = 'IDP User Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            USERNAME = CHOICE.split('\t')[0].strip()
            USER_ID = CHOICE.split('\t')[1].strip()
            if USERNAME:
                Log.info(f"gathering {USERNAME} details now, please wait...")
            else:
                Log.critical("please select a username to continue...")
        except:
            Log.critical("please select a username to continue...")
    return USERNAME, USER_ID

def get_operator_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'operator'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def get_platform_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'platform'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def chk_for_profile(aws_profile_name):
    if re.search('ATLAS', aws_profile_name, re.IGNORECASE) or re.search('SKS', aws_profile_name, re.IGNORECASE):
        CONFIG = Config('awstools')
        for PROFILE in CONFIG.PROFILES:
            if aws_profile_name == PROFILE:
                return True
    else:
        return False
    return False

def set_expire_time(myhours):
    CURRENT = datetime.datetime.now()
    FORMAT = CURRENT + datetime.timedelta(hours=myhours)
    expire_date = FORMAT.strftime('%FT%T.%f'"Z")
    return expire_date

def set_bucket_name(aws_profile_name):
    if re.search('ATLAS', aws_profile_name, re.IGNORECASE):
        bucket_name = 'com.vmw.vmc.govcloud-atlas.us-gov-west-1.prd.secrets'
    elif re.search('SKS', aws_profile_name, re.IGNORECASE):
        bucket_name = 'com.vmw.vmc.govcloud.us-gov-west-1.prd.secrets'
    else:
        Log.critical(f"please re-run this script after authenticating with either SKS or ATLAS, and caching bucket information")
    return bucket_name

