import click, json, sys, os, oci
from toolbox.logger import Log
from .ossclient import OSSclient, setup_config_file
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import set_terminal_width
from .iam import get_latest_profile
from pprint import pprint

CONFIG = Config('ocitools')
ignore = ['latest']

@click.group('oss', invoke_without_command=True, help='object storage functions to sync buckets and filesystems', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-m', '--menu', help='use the menu to perform OCI OSS actions', is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def oss(ctx, menu):
    if menu:
        ctx.obj['MENU'] = True
    else:
        ctx.obj['MENU'] = False

@oss.command(help='create a new bucket', context_settings={'help_option_names':['-h','--help']})
@click.argument('bucket_name', required=True)
@click.pass_context
def create(ctx, bucket_name):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    OSS = get_OSSclient(profile_name, oci_region)
    for PROFILE in CONFIG.PROFILES:
        if PROFILE in ignore:
            continue
        CACHED_COMPARTMENTS = OSS.get_compartments()
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
        ocid = CHOICE.split('\t')[0].strip()
    else:
        Log.critical('please choose a compartment')
    _create(profile_name, bucket_name, ocid, oci_region)
    Log.info('refreshing cache now for buckets after creation')
    _refresh(profile_name, oci_region)

def _create(profile_name, bucket_name, ocid, oci_region):
    MYOSS = get_OSSclient(profile_name, oci_region)
    config = setup_config_file(profile_name, oci_region)
    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace(compartment_id=ocid).data
    RESULT = MYOSS.create_bucket(ocid, namespace, bucket_name, profile_name)
    if RESULT:
        Log.info(f"bucket: {bucket_name} created in region: {oci_region} successfully.")
        return RESULT
    else:
        Log.critical("failed to create the bucket")

@oss.command(help='download from OSS to local storage', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('source', required=False, default=None)
@click.option('--destination', help="provide a local destination for download", type=str, required=False, default=os.environ["HOME"], show_default=True)
def download(ctx, source, destination):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    if ctx.obj["MENU"] or source is None:
        if source is None:
            CACHED_BUCKETS = {}
            CACHED_CONTENTS = []
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if PROFILE == profile_name:
                    try:
                        CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region))
                        CACHED_BUCKETS.pop('last_cache_update', None)
                    except:
                        Log.critical(f'there are 0 buckets cached for {oci_region} and profile {PROFILE}')
            INPUT = f'Downloads => {profile_name}'
            CHOICE = runMenu(CACHED_BUCKETS, INPUT)
            if CHOICE:
                source = ''.join(CHOICE)
                for PROFILE in CONFIG.PROFILES:
                    if PROFILE in ignore:
                        continue
                    if CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region) and source in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                        profile_name = PROFILE
                        OSS = get_OSSclient(PROFILE, oci_region)
                        CONTENTS = OSS.show_bucket_content(source, profile_name)
                        if type(CONTENTS) is not bool:
                            CACHED_CONTENTS = CONTENTS
                            INPUT = f'Bucket Contents => {profile_name}'
                            CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                            if CHOICE:
                                CHOICE = ''.join(CHOICE)
                                if _download(profile_name, oci_region, source, destination, CHOICE):
                                    Log.info(f"downloading {CHOICE} from bucket {source} completed")
                                else:
                                    Log.critical(f"failed to download {CHOICE} from OSS bucket {source} to {destination}")
                            else:
                                Log.critical(f"please select a valid choice to download, exiting.")
                        break
        else:
            CACHED_CONTENTS = []
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region) and source in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                    profile_name = PROFILE
                    OSS = get_OSSclient(PROFILE, oci_region)
                    CONTENTS = OSS.show_bucket_content(source, profile_name)
                    if type(CONTENTS) is not bool:
                        CACHED_CONTENTS = CONTENTS
                        INPUT = f'Bucket Contents => {profile_name}'
                        CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                        if CHOICE:
                            CHOICE = ''.join(CHOICE)
                            if _download(profile_name, oci_region, source, destination, CHOICE):
                                Log.info(f"downloading {CHOICE} from bucket {source} completed")
                            else:
                                Log.critical(f"failed to download {CHOICE} from OSS bucket {source} to {destination}")
                        else:
                            Log.critical(f"please select a valid choice to download, exiting.")
                    break
    else:
        for profile_name in CONFIG.PROFILES:
            if profile_name in ignore:
                continue
            PROFILE = profile_name
            if CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region) and source in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                OSS = get_OSSclient(PROFILE, oci_region)
                CONTENTS = OSS.show_bucket_content(source, profile_name)
                if type(CONTENTS) is not bool:
                    CACHED_CONTENTS = CONTENTS
                    INPUT = f'Bucket Contents => {profile_name}'
                    CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        if _download(profile_name, oci_region, source, destination, CHOICE):
                            Log.info(f"downloading {CHOICE} from bucket {source} completed")
                        else:
                            Log.critical(f"failed to download {CHOICE} from OSS bucket {source} to {destination}")
                    else:
                        Log.critical(f"please select a valid choice to download, exiting.")
                break

def _download(profile_name, oci_region, source, destination, filename):
    OSS = get_OSSclient(profile_name, oci_region)
    BUCKETS = CONFIG.PROFILES[profile_name]['metadata']['cached_buckets'][oci_region]
    for BUCKETNAME in BUCKETS:
        if BUCKETNAME == source:
            NAMESPACE = BUCKETS[BUCKETNAME]['namespace']
    try:
        OSS.oss_to_local(source, destination, filename, NAMESPACE)
        return True
    except:
        return False

@oss.command(help='upload from local storage to OSS bucket', context_settings={'help_option_names':['-h','--help']})
@click.option('--source', help="provide a local source for upload", type=str, required=True)
@click.argument('destination', required=False, default=None)
@click.pass_context
def upload(ctx, source, destination):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    CACHED_BUCKETS = {}
    if destination is None:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE == profile_name:
                try:
                    CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region))
                    CACHED_BUCKETS.pop('last_cache_update', None)
                except:
                    Log.critical(f'there are 0 buckets cached for {oci_region} and profile {PROFILE}')
        INPUT = f'Uploads => {profile_name}'
        CHOICE = runMenu(CACHED_BUCKETS, INPUT)
        if CHOICE:
            destination = ''.join(CHOICE)
            for profile_name in CONFIG.PROFILES:
                if profile_name in ignore:
                    continue
                if destination in CONFIG.get_metadata_aws('cached_buckets', profile_name, oci_region):
                    if _upload(profile_name, oci_region, source, destination):
                        Log.info(f"uploading local files from {source} to OSS bucket {destination} completed")
                    else:
                        Log.critical(f"failed to upload local files from {source} to OSS bucket {destination}")
                    break
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if destination in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                profile_name = PROFILE
                if _upload(profile_name, oci_region, source, destination):
                    Log.info(f"uploading local files from {source} to OSS bucket {destination} completed")
                else:
                    Log.critical(f"failed to upload local files from {source} to OSS bucket {destination}")
                break

def _upload(profile_name, oci_region, source, destination):
    OSS = get_OSSclient(profile_name, oci_region)
    BUCKETS = CONFIG.PROFILES[profile_name]['metadata']['cached_buckets'][oci_region]
    for BUCKETNAME in BUCKETS:
        if BUCKETNAME == destination:
            NAMESPACE = BUCKETS[BUCKETNAME]['namespace']
    try:
        OSS.local_to_oss(destination, source, NAMESPACE)
        return True
    except:
        return False

@oss.command(help='delete a specified bucket', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('bucket', required=False, default=None)
def delete(ctx, bucket):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    if bucket is None:
        if bucket is None:
            CACHED_BUCKETS = {}
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if PROFILE == profile_name:
                    try:
                        CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region))
                        CACHED_BUCKETS.pop('last_cache_update', None)
                    except:
                        Log.warn(f'there are 0 buckets in {oci_region} and profile {PROFILE}')
                        sys.exit()
            INPUT = f'Deletion => {profile_name}'
            CHOICE = runMenu(CACHED_BUCKETS, INPUT)
            if CHOICE:
                bucket = ''.join(CHOICE)
                for PROFILE in CONFIG.PROFILES:
                    if PROFILE in ignore:
                        continue
                    if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                        profile_name = PROFILE
                        _delete(bucket, profile_name, oci_region)
                        Log.info('refreshing cache now for buckets after deletion')
                        _refresh(profile_name, oci_region)
                        break
        else:
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                    profile_name = PROFILE
                    _delete(bucket, profile_name, oci_region)
                    Log.info('refreshing cache now for buckets after deletion')
                    _refresh(profile_name, oci_region)
                    break
    else:
        for PROFILE in CONFIG.PROFILES:
            if PROFILE in ignore:
                continue
            if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                profile_name = PROFILE
                _delete(ctx, bucket, profile_name, oci_region)
                Log.info('refreshing cache now for buckets after deletion')
                _refresh(profile_name, oci_region)
                break

def _delete(bucket, profile_name, oci_region):
    OSS = get_OSSclient(profile_name, oci_region)
    BUCKETS = CONFIG.PROFILES[profile_name]['metadata']['cached_buckets'][oci_region]
    for BUCKETNAME in BUCKETS:
        if BUCKETNAME == bucket:
            NAMESPACE = BUCKETS[BUCKETNAME]['namespace']
    RESULT = OSS.delete_bucket(NAMESPACE, bucket, profile_name)
    if RESULT:
        Log.info(f"bucket: {bucket} deleted in region: {oci_region} successfully.")
        return True
    else:
        Log.critical("failed to delete the bucket")

@oss.command(help='manually refresh OSS cached data', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def refresh(ctx):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    _refresh(profile_name, oci_region)

def _refresh(profile_name, oci_region):
    try:
        OSS = get_OSSclient(profile_name, oci_region, auto_refresh=False)
        OSS.cache_buckets(profile_name)
        return True
    except:
        return False

@oss.command(help='show the data stored in OSS cache', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
@click.argument('bucket', required=False, default=None)
def show(ctx, bucket):
    profile_name = ctx.obj['PROFILE']
    oci_region = get_region(ctx, profile_name)
    if ctx.obj["MENU"]:
        if bucket is None:
            CACHED_BUCKETS = {}
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                   continue
                if PROFILE == profile_name:
                    try:
                        CACHED_BUCKETS.update(CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region))
                        CACHED_BUCKETS.pop('last_cache_update', None)
                    except:
                        Log.critical(f"there are 0 cached buckets for {PROFILE}")
            INPUT = f'Bucket List => {profile_name}'
            CHOICE = runMenu(CACHED_BUCKETS, INPUT)
            if CHOICE:
                CACHED_CONTENTS = []
                for PROFILE in CONFIG.PROFILES:
                    if PROFILE in ignore:
                        continue
                    if CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region) and ''.join(CHOICE) in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                        OSS = get_OSSclient(PROFILE, oci_region)
                        CONTENTS = OSS.show_bucket_content(''.join(CHOICE), profile_name)
                        if type(CONTENTS) is not bool:
                            CACHED_CONTENTS = CONTENTS
                            INPUT = f'Bucket Contents => {profile_name}'
                            CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                        break
        else:
            CACHED_CONTENTS = []
            for PROFILE in CONFIG.PROFILES:
                if PROFILE in ignore:
                    continue
                if bucket in CONFIG.get_metadata_aws('cached_buckets', PROFILE, oci_region):
                    OSS = get_OSSclient(PROFILE, oci_region)
                    CONTENTS, TOTAL, LASTMOD = OSS.show_bucket_content(bucket, PROFILE)
                    if type(CONTENTS) is not bool:
                        CACHED_CONTENTS = CONTENTS
                        INPUT = f'Bucket Contents => {profile_name}'
                        CHOICE = runMenu(CACHED_CONTENTS, INPUT)
                    break
    else:
        if bucket is None:
            _show('buckets', oci_region, profile_name)
        else:
            _show('bucket_files', oci_region, profile_name, bucket)

def _show(target, oci_region, profile_name, bucket=None):
    try:
        if target == 'buckets':
            OSS = get_OSSclient(profile_name, oci_region, auto_refresh=False, cache_only=True)
            OSS.show_cache('cached_buckets', profile_name, oci_region)
        if target == 'bucket_files':
            OSS = get_OSSclient(profile_name, oci_region)
            CONTENTS, TOTAL, LASTMOD = OSS.show_bucket_content(bucket, profile_name)
            if type(CONTENTS) is not bool:
                print(json.dumps(CONTENTS, indent=4, sort_keys=True))
                Log.info(f"bucket: {bucket}, total size: {OSS.calculate_object_size(TOTAL)}, and last modified on: {str(LASTMOD)}")
            else:
                Log.critical(f"credentials not available to access OSS bucket {bucket} permission denied, or bucket does not exist")
        return True
    except:
        return False

def get_OSSclient(profile_name, region='us-ashburn-1', auto_refresh=False, cache_only=False):
    CLIENT = OSSclient(profile_name, region, cache_only)
    if auto_refresh:
        CLIENT.auto_refresh(profile_name)
    return CLIENT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'OSS Bucket Menu: {INPUT}'
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
        OSS = get_OSSclient(profile_name)
        OCI_REGION = OSS.get_region_from_profile(profile_name)
    return OCI_REGION
