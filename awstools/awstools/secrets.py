import click, json, os
from toolbox.logger import Log
from .s3client import S3client
from toolbox.click_complete import complete_profile_names, complete_bucket_names
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from pprint import pprint
from jenkinstools.jenkinsclient import JenkinsClient
from toolbox.passwords import PasswordstateLookup
from toolbox.getpass import getOtherToken

JENKINS = JenkinsClient()

CONFIG = Config('awstools')
ignore = ['default','IDP','latest']

@click.group('secrets', invoke_without_command=True, help='functions to pull and set secrets in S3', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform secrets actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def secrets(ctx, menu):
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False

@secrets.command(help='get the secrets bucket policy to verify accessibility', context_settings={'help_option_names':['-h','--help']})
@click.argument('bucket', required=False, default='com.vmw.vmc.govcloud.us-gov-west-1.prd.secrets')
@click.pass_context
def get_policy(ctx, bucket):
    aws_profile_name = ctx.obj['PROFILE']
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
def set_policy(ctx, mode):
    aws_profile_name = ctx.obj['PROFILE']
    _set_policy(mode, aws_profile_name)

def _set_policy(mode, aws_profile_name):
    S3 = get_S3client(aws_profile_name)
    RESULT = S3.set_bucket_policy(mode)
    if RESULT:
        Log.info(f"bucket policy set successfully.")
    else:
        Log.critical("failed to set the bucket policy.")

@secrets.command(help='upload secrets from local filepath to S3 using Jenkins API', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('credential', required=False, default=None)
@click.option('--source', help="provide a local filepath for upload", type=str, required=True)
def upload(ctx, credential, source):
    bucket_name = 'com.vmw.vmc.govcloud.us-gov-west-1.prd.secrets'
    aws_profile_name = ctx.obj['PROFILE']
    _set_policy('off', aws_profile_name)
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
                        if _upload(source, credential):
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
                            if _upload(source, credential):
                                Log.info(f"uploading local files from {source} to s3 bucket {bucket_name} completed")
                            else:
                                Log.critical(f"failed to upload local files from {source} to s3 bucket {bucket_name}")
                            break
    _set_policy('on', aws_profile_name)

def _upload(source, credential):

    JOB = 'skylab-s3-secrets-updater-govcloud-prd'
    JSONDICT = {'SERVICE_CREDENTIALS': credential}
    FILES = {'SECRETS_FILE': open(source, 'rb')}
    MYURL = JENKINS.build_url(JOB, merge(JSONDICT,FILES), user_profile='delta')
    RESULT = JENKINS.launch_job(JOB, JSONDICT, FILES, wait=True, interval=30, time_out=7200, sleep=15, user_profile='delta')
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
@click.pass_context
@click.argument('source', required=False, default=None)
@click.option('--destination', help="provide a local destination for download", type=str, required=True)
def download(ctx, source, destination):
    bucket_name = 'com.vmw.vmc.govcloud.us-gov-west-1.prd.secrets'
    aws_profile_name = ctx.obj['PROFILE']
    _set_policy('off', aws_profile_name)
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
    _set_policy('on', aws_profile_name)

def _download(aws_profile_name, bucket_name, destination, filename):
    S3 = get_S3client(aws_profile_name)
    try:
        S3.s3_to_local(bucket_name, destination, filename)
        return True
    except:
        return False

@secrets.command(help='show secrets for a specific service from s3 secrets bucket', context_settings={'help_option_names':['-h','--help']})
@click.argument('source', required=False, default=None)
@click.pass_context
def show(ctx, source):
    bucket_name = 'com.vmw.vmc.govcloud.us-gov-west-1.prd.secrets'
    destination = os.environ['HOME']
    aws_profile_name = ctx.obj['PROFILE']
    _set_policy('off', aws_profile_name)
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
                                print()
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
                                    print()
                                os.remove(destination + "/" + source) if os.path.exists(destination + "/" + source) else None
                                break
                            else:
                                Log.critical(f"failed to show {source} from s3 bucket {bucket_name}")
    _set_policy('on', aws_profile_name)

def get_S3client(aws_profile_name, aws_region='us-gov-west-1', auto_refresh=True, cache_only=False):
    CLIENT = S3client(aws_profile_name, aws_region, False, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(aws_profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'S3 Bucket Menu: {INPUT}'
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
