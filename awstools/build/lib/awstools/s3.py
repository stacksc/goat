import click, json, os
from toolbox.logger import Log
from .s3client import S3client
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from pprint import pprint

CONFIG = Config('awstools')
ignore = ['IDP','latest']

@click.group('s3', invoke_without_command=True, help='s3 functions to sync buckets and filesystems', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform S3 actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def s3(ctx, menu):
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False

@s3.command(help='create a new bucket', context_settings={'help_option_names':['-h','--help']})
@click.argument('bucket_name', required=True)
@click.pass_context
def create(ctx, bucket_name):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    _create(aws_profile_name, aws_region_name, bucket_name)

def _create(aws_profile_name, aws_region_name, bucket_name):
    S3 = get_S3client(aws_profile_name, aws_region_name)
    RESULT = S3.create_bucket(bucket_name, aws_region_name)
    if RESULT:
        Log.info(f"bucket: {bucket_name} created in region: {aws_region_name} successfully.")
        return RESULT
    else:
        Log.critical("failed to create the bucket")

@s3.command(help='download from s3 to local storage', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('source', required=False, default=None)
@click.option('--destination', help="provide a local destination for download", type=str, required=False, default=os.environ["HOME"], show_default=True)
def download(ctx, source, destination):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    if ctx.obj["MENU"] or source is None:
        if source is None:
            CACHED_BUCKETS = {}
            CACHED_CONTENTS = []
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if PROFILE == aws_profile_name:
                    CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name))
                    CACHED_BUCKETS.pop('last_cache_update', None)
            INPUT = f'Downloads => {aws_profile_name}'
            CHOICE = runMenu(CACHED_BUCKETS, INPUT)
            if CHOICE:
                source = ''.join(CHOICE)
                for PROFILE in CONFIG.PROFILES:
                    if PROFILE in ignore:
                        continue
                    if CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name) and source in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                        aws_profile_name = PROFILE
                        S3 = get_S3client(PROFILE, aws_region_name)
                        CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(source)
                        if type(CONTENTS) is not bool:
                            for content in CONTENTS:
                                CACHED_CONTENTS.append(content['file'])
                            INPUT = f'Bucket Contents => {aws_profile_name}'
                            CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                            if CHOICE:
                                CHOICE = ''.join(CHOICE)
                                if _download(aws_profile_name, aws_region_name, source, destination, CHOICE):
                                    Log.info(f"downloading {CHOICE} from bucket {source} completed")
                                else:
                                    Log.critical(f"failed to download {CHOICE} from s3 bucket {source} to {destination}")
                            else:
                                Log.critical(f"please select a valid choice to download, exiting.")
                        break
        else:
            CACHED_CONTENTS = []
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name) and source in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                    S3 = get_S3client(PROFILE, aws_region_name)
                    CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(source)
                    if type(CONTENTS) is not bool:
                        for content in CONTENTS:
                            CACHED_CONTENTS.append(content['file'])
                        INPUT = f'Bucket Contents => {aws_profile_name}'
                        CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                        if CHOICE:
                            CHOICE = ''.join(CHOICE)
                            if _download(aws_profile_name, aws_region_name, source, destination, CHOICE):
                                Log.info(f"downloading {CHOICE} from bucket {source} completed")
                            else:
                                Log.critical(f"failed to download {CHOICE} from s3 bucket {source} to {destination}")
                        else:
                            Log.critical(f"please select a valid choice to download, exiting.")
                    break
    else:
        for aws_profile_name in CONFIG.PROFILES:
            if aws_profile_name in ignore:
                continue
            PROFILE = aws_profile_name
            if CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name) and source in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                S3 = get_S3client(PROFILE, aws_region_name)
                CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(source)
                if type(CONTENTS) is not bool:
                    for content in CONTENTS:
                        CACHED_CONTENTS.append(content['file'])
                    INPUT = f'Bucket Contents => {aws_profile_name}'
                    CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        if _download(aws_profile_name, aws_region_name, source, destination, CHOICE):
                            Log.info(f"downloading {CHOICE} from bucket {source} completed")
                        else:
                            Log.critical(f"failed to download {CHOICE} from s3 bucket {source} to {destination}")
                    else:
                        Log.critical(f"please select a valid choice to download, exiting.")
                break

def _download(aws_profile_name, aws_region_name, source, destination, filename):
    S3 = get_S3client(aws_profile_name, aws_region_name)
    try:
        S3.s3_to_local(source, destination, filename)
        return True
    except:
        return False

@s3.command(help='upload from local storage to s3 bucket', context_settings={'help_option_names':['-h','--help']})
@click.option('--source', help="provide a local source for upload", type=str, required=True)
@click.argument('destination', required=False, default=None)
@click.pass_context
def upload(ctx, source, destination):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    CACHED_BUCKETS = {}
    if ctx.obj["MENU"] or destination is None:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE == aws_profile_name:
                CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name))
                CACHED_BUCKETS.pop('last_cache_update', None)
        INPUT = f'Uploads => {aws_profile_name}'
        CHOICE = runMenu(CACHED_BUCKETS, INPUT)
        if CHOICE:
            destination = ''.join(CHOICE)
            for aws_profile_name in CONFIG.PROFILES:
                if aws_profile_name in ignore:
                    continue
                if destination in CONFIG.get_metadata_aws('cached_buckets', aws_profile_name, aws_region_name):
                    if _upload(aws_profile_name, aws_region_name, source, destination):
                        Log.info(f"uploading local files from {source} to s3 bucket {destination} completed")
                    else:
                        Log.critical(f"failed to upload local files from {source} to s3 bucket {destination}")
                    break
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if destination in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                aws_profile_name = PROFILE
                if _upload(aws_profile_name, aws_region_name, source, destination):
                    Log.info(f"uploading local files from {source} to s3 bucket {destination} completed")
                else:
                    Log.critical(f"failed to upload local files from {source} to s3 bucket {destination}")
                break

def _upload(aws_profile_name, aws_region_name, source, destination):
    S3 = get_S3client(aws_profile_name, aws_region_name)
    try:
        S3.local_to_s3(destination, source)
        return True
    except:
        return False

@s3.command(help='delete a specified bucket', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('bucket', required=False, default=None)
def delete(ctx, bucket):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    if ctx.obj["MENU"] or bucket is None:
        if bucket is None:
            CACHED_BUCKETS = {}
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if PROFILE == aws_profile_name:
                    CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name))
                    CACHED_BUCKETS.pop('last_cache_update', None)
            INPUT = f'Deletion => {aws_profile_name}'
            CHOICE = runMenu(CACHED_BUCKETS, INPUT)
            if CHOICE:
                bucket = ''.join(CHOICE)
                for PROFILE in CONFIG.PROFILES:
                    if PROFILE in ignore:
                        continue
                    if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                        aws_profile_name = PROFILE
                        _delete(bucket, aws_profile_name, aws_region_name)
                        break
        else:
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                    aws_profile_name = PROFILE
                    _delete(bucket, aws_profile_name, aws_region_name)
                    break
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                aws_profile_name = PROFILE
                _delete(bucket, aws_profile_name, aws_region_name)
                break

def _delete(bucket, aws_profile_name, aws_region_name):
    S3 = get_S3client(aws_profile_name, aws_region_name)
    RESULT = S3.delete_bucket(bucket, aws_profile_name, aws_region_name)
    if RESULT:
        Log.info(f"bucket: {bucket} deleted in region: {aws_region_name} successfully.")
        return True
    else:
        Log.critical("failed to delete the bucket")

@s3.command(help='manually refresh s3 cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    _refresh(aws_profile_name, aws_region_name)

def _refresh(aws_profile_name, aws_region_name):
    try:
        S3 = get_S3client(aws_profile_name, aws_region_name, auto_refresh=False)
        S3.cache_buckets(aws_profile_name)
        return True
    except:
        return False

@s3.command(help='show the data stored in s3 cache', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('bucket', required=False, default=None)
def show(ctx, bucket):
    aws_profile_name = ctx.obj['PROFILE']
    aws_region_name = get_region(ctx, aws_profile_name)
    if ctx.obj["MENU"]:
        if bucket is None:
            CACHED_BUCKETS = {}
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                   continue
                if PROFILE == aws_profile_name:
                    try:
                        CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name))
                        CACHED_BUCKETS.pop('last_cache_update', None)
                    except:
                        Log.critical(f"there are 0 cached buckets for {PROFILE}")
            INPUT = f'Bucket List => {aws_profile_name}'
            CHOICE = runMenu(CACHED_BUCKETS, INPUT)
            if CHOICE:
                CACHED_CONTENTS = []
                for PROFILE in CONFIG.PROFILES:
                    if PROFILE in ignore:
                        continue
                    if CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name) and ''.join(CHOICE) in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                        S3 = get_S3client(PROFILE, aws_region_name)
                        CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(''.join(CHOICE))
                        if type(CONTENTS) is not bool:
                            for content in CONTENTS:
                                CACHED_CONTENTS.append(content['file'])
                            INPUT = f'Bucket Contents => {aws_profile_name}'
                            CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                        break
        else:
            CACHED_CONTENTS = []
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, aws_region_name):
                    S3 = get_S3client(PROFILE, aws_region_name)
                    CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket)
                    if type(CONTENTS) is not bool:
                        for content in CONTENTS:
                            CACHED_CONTENTS.append(content['file'])
                        INPUT = f'Bucket Contents => {aws_profile_name}'
                        CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    break
    else:
        if bucket is None:
            _show('buckets', aws_profile_name, aws_region_name)
        else:
            _show('bucket_files', aws_profile_name, aws_region_name, bucket)

def _show(target, aws_profile_name, aws_region_name, bucket=None):
    try:
        if target == 'buckets':
            S3 = get_S3client(aws_profile_name, aws_region_name, cache_only=True)
            S3.show_cache('cached_buckets', aws_profile_name)
        if target == 'bucket_files':
            S3 = get_S3client(aws_profile_name, aws_region_name)
            CONTENTS, TOTAL, LASTMOD = S3.show_bucket_content(bucket)
            if type(CONTENTS) is not bool:
                print(json.dumps(CONTENTS, indent=4, sort_keys=True))
                Log.info(f"bucket: {bucket}, total size: {S3.calculate_object_size(TOTAL)}, and last modified on: {str(LASTMOD)}")
            else:
                Log.critical(f"credentials not available to access s3 bucket {bucket} permission denied, or bucket does not exist")
        return True
    except:
        return False

def get_S3client(aws_profile_name, aws_region='us-east-1', auto_refresh=False, cache_only=False):
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

def get_region(ctx, aws_profile_name):
    AWS_REGION = ctx.obj['REGION']
    if not AWS_REGION:
        S3 = get_S3client(aws_profile_name, 'us-east-1')
        AWS_REGION = S3.get_region_from_profile(aws_profile_name)
    return AWS_REGION
