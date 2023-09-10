import datetime, time, os, json, re
from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from . import iam_nongc
from .aws_config import AWSconfig
from botocore.exceptions import ClientError
from tabulate import tabulate
from pathlib import Path
try:
    import importlib_resources as resources
except:
    from importlib import resources

CONFIGSTORE = Config('awstools')

class S3client():

    def __init__(self, aws_profile_name, aws_region='us-east-1', in_boundary=True, cache_only=False):
        self.CONFIG = AWSconfig()
        self.CONFIGSTORE = Config('awstools')
        self.size_table={0: 'Bs', 1: 'KBs', 2: 'MBs', 3: 'GBs', 4: 'TBs', 5: 'PBs', 6: 'EBs'}
        self.CACHE_UPDATE_INTERVAL = 60*60*24*7 # update cache every week
        self.AWS_PROFILE = aws_profile_name
        self.AWS_REGION = aws_region
        self.INB = in_boundary
        self.CACHE_ONLY = cache_only
        if not self.CACHE_ONLY:
            self.get_session()

    def get_session(self):
        if detect_environment() == 'non-gc':
            if self.CONFIG.profile_or_role(self.AWS_PROFILE):
                self.SESSION = iam_nongc._authenticate(self.AWS_PROFILE, self.AWS_REGION)
            else:
                self.SESSION = iam_nongc._assume_role(aws_profile_name=self.AWS_PROFILE)[0]
        return self.SESSION

    def create_bucket(self, bucket_name, aws_region):
        CLIENT = self.SESSION.client('s3')
        try:
            CLIENT.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': aws_region})
            return True
        except ClientError:
            Log.warn('insufficient permissions to create a bucket')
            return False
        except:
            Log.warn('unknown error encountered')
            return False

    def check_policy_status(self, bucket_name):
        CLIENT = self.SESSION.client('s3')
        try:
            RESULT = CLIENT.get_bucket_policy_status(Bucket=bucket_name)
            return RESULT["PolicyStatus"]
        except ClientError:
            Log.warn('insufficient permissions or policy does not exist for this bucket')
            return False
        except:
            Log.warn('unknown error encountered')
            return False

    def get_bucket_policy(self, bucket_name):
        CLIENT = self.SESSION.client('s3')
        try:
            RESULT = CLIENT.get_bucket_policy(Bucket=bucket_name)
            if RESULT:
                return RESULT
            else:
                Log.critical(f"unable to find an attached policy to bucket {bucket_name}")
                return False
        except ClientError: 
            Log.warn("no policy attached to this bucket or insufficient privileges")
            return False
        except:
            Log.warn('unknown error encountered')
            return False

    def show_bucket_content(self, bucket_name, total=0):
        TIMEOUT = time.time() + 90
        ITEMS = []
        LASTMOD = ''
        TOTAL = total
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
            self.get_session()
        CLIENT = self.SESSION.client('s3')
        GET_LAST_MODIFIED = lambda obj: int(obj['LastModified'].strftime('%Y%m%d%H%M%S'))
        try:
            RESPONSE = CLIENT.list_objects(Bucket=bucket_name)
            if 'Contents' in RESPONSE:
                OBJECTS = RESPONSE['Contents']
                FILES = sorted(OBJECTS, key=GET_LAST_MODIFIED, reverse=False)
                for KEY in FILES:
                    if time.time() > TIMEOUT:
                        break
                    FILE = KEY['Key']
                    DATE_MODIFIED = str(KEY["LastModified"])
                    SIZE = KEY['Size']
                    CALC_SIZE = self.calculate_object_size(SIZE)
                    TOTAL = TOTAL + SIZE
                    if 'None' not in FILE:
                        new_dictionary={
                            "file":FILE,
                            "lastModified":DATE_MODIFIED,
                            "size":CALC_SIZE
                        }
                        ITEMS.append(new_dictionary) 
        except:
            return False, False, False
        try:
            LASTMOD = list(ITEMS)[-1]["lastModified"]
        except:
            DATE_LIST = []
            try:
                RESPONSE = CLIENT.list_buckets(Bucket=bucket_name)
                for INDEX in RESPONSE['Buckets']:
                    DATE_LIST.append(INDEX['CreationDate'])
                LASTMOD = list(DATE_LIST)[-1]
            except:
                pass
        return ITEMS, TOTAL, LASTMOD

    def delete_bucket(self, bucket_name, aws_profile_name, aws_region):
        CLIENT = self.SESSION.client('s3')
        try:
            OBJECTS = CLIENT.list_objects_v2(Bucket=bucket_name)
            COUNT = OBJECTS['KeyCount'] 
        except:
            Log.critical(f"unable to find bucket {bucket_name}")
        if COUNT == 0:
            try:
                RESPONSE = CLIENT.delete_bucket(Bucket=bucket_name)
                Log.info(f"bucket {bucket_name} deleted")
            except:
                self.nuke_bucket(bucket_name, CLIENT, aws_region)
        else:
            self.nuke_bucket(bucket_name, CLIENT, aws_region)
        return True

    def get_region_from_profile(self, aws_profile_name):
        AWS_REGION = self.CONFIG.get_from_config('creds', 'region', profile_name=aws_profile_name)
        if AWS_REGION is None: # this is for when the user wants to use a profile which sources another profile for IAM creds
            CREDS_PROFILE = self.CONFIG.get_from_config('creds', 'source_profile', profile_name=aws_profile_name)
            AWS_REGION = self.CONFIG.get_from_config('config', 'region', profile_name=CREDS_PROFILE)
        if AWS_REGION is None:
            Log.critical("Please run goat aws iam assume-role for the target profile before using the s3 module")
        return AWS_REGION

    def nuke_bucket(self, bucket_name, aws_client, aws_region):
        TIMEOUT = time.time() + 600
        SIZE_TABLE = {0: 'Bs', 1: 'KBs', 2: 'MBs', 3: 'GBs', 4: 'TBs', 5: 'PBs', 6: 'EBs'} # appears to be redundant
        # https://wasabi-support.zendesk.com/hc/en-us/articles/360058028992-How-do-I-mass-delete-non-current-versions-inside-a-bucket-
        # include latest verions too so we can nuke the bucket
        PAGINATOR = aws_client.get_paginator('list_object_versions')
        PARAMETERS = {'Bucket': bucket_name}
        DELETE_MARKER_COUNT = 0
        VERSIONED_OBJECT_COUNT = 0
        VERSIONED_OBECT_SIZE = 0
        CURRENT_OBJECT_COUNT = 0
        CURRENT_OBJECT_SIZE = 0
        DELETE_MARKER_LIST = []
        VERSION_LIST = []
        CURRENT_LIST = []
        Log.info("calculating, please wait... this may take a while")
        for ITERATOR in PAGINATOR.paginate(**PARAMETERS):
            if time.time() > TIMEOUT:
                Log.critical(f"unable to delete bucket because time to execute exceeded 10 minutes: {bucket_name}")
            if 'DeleteMarkers' in ITERATOR:
                for DELETE_MARKER in ITERATOR['DeleteMarkers']:
                    DELETE_MARKER_LIST.append({'Key': DELETE_MARKER['Key'], 'VersionId': DELETE_MARKER['VersionId']})
                    DELETE_MARKER_COUNT += 1
                    if 'Versions' in ITERATOR:
                        for VERSION in ITERATOR['Versions']:
                            if VERSION['IsLatest'] is False:
                                VERSIONED_OBJECT_COUNT += 1
                                VERSIONED_OBECT_SIZE += VERSION['Size']
                                VERSION_LIST.append({'Key': VERSION['Key'], 'VersionId': VERSION['VersionId']})
                            elif VERSION['IsLatest'] is True:
                                CURRENT_OBJECT_COUNT += 1
                                CURRENT_OBJECT_SIZE += VERSION['Size']
                                CURRENT_LIST.append({'Key': VERSION['Key'], 'VersionId': VERSION['VersionId']})
            elif 'Versions' in ITERATOR:
                for DELETE_MARKER in ITERATOR['Versions']:
                    DELETE_MARKER_LIST.append({'Key': DELETE_MARKER['Key'], 'VersionId': DELETE_MARKER['VersionId']})
                    DELETE_MARKER_COUNT += 1
                    if 'Versions' in ITERATOR:
                        for VERSION in ITERATOR['Versions']:
                            if VERSION['IsLatest'] is False:
                                VERSIONED_OBJECT_COUNT += 1
                                VERSIONED_OBECT_SIZE += VERSION['Size']
                                VERSION_LIST.append({'Key': VERSION['Key'], 'VersionId': VERSION['VersionId']})
                            elif VERSION['IsLatest'] is True:
                                CURRENT_OBJECT_COUNT += 1
                                CURRENT_OBJECT_SIZE += VERSION['Size']
                                CURRENT_LIST.append({'Key': VERSION['Key'], 'VersionId': VERSION['VersionId']})
        print("-" * 10)
        Log.info(f"total delete markers: {str(DELETE_MARKER_COUNT)}")
        Log.info(f"number of current objects: {str(CURRENT_OBJECT_COUNT)}")
        Log.info(f"current objects size: {self.calculate_object_size(CURRENT_OBJECT_SIZE)}")
        Log.info(f"number of non-current objects: {str(VERSIONED_OBJECT_COUNT)}")
        Log.info(f"non-current objects size: {self.calculate_object_size(VERSIONED_OBECT_SIZE)}")
        Log.info(f"total size of current + non current objects: {self.calculate_object_size(VERSIONED_OBECT_SIZE + CURRENT_OBJECT_SIZE)}")
        print("-" * 10)
        DELETE_FLAG = False
        while not DELETE_FLAG:
            CHOICE = 'y'
            if CHOICE.strip().lower() == 'y':
                DELETE_FLAG = True
                Log.info("starting deletes now...")
                Log.info("removing delete markers 1000 at a time")
                for INDEX in range(0, len(DELETE_MARKER_LIST), 1000):
                    RESPONSE = aws_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={
                            'Objects': DELETE_MARKER_LIST[INDEX:INDEX + 1000],
                            'Quiet': True
                        }
                    )
                Log.info("removing oldest versioned objects 1000 at a time")
                for INDEX in range(0, len(VERSION_LIST), 1000):
                    RESPONSE = aws_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={
                            'Objects': VERSION_LIST[INDEX:INDEX + 1000],
                            'Quiet': True
                        }
                    )
                Log.info("process completed successfully, deleting remaining objects if anything exists")
                try:
                    if self.finish_nuke_bucket(aws_client, bucket_name):
                        try:
                            RESPONSE = aws_client.delete_bucket(Bucket=bucket_name)
                            Log.info(f"bucket: {bucket_name} deleted in region: {aws_region} successfully.")
                        except:
                            Log.critical(f"unable to delete bucket: {bucket_name}")
                    else:
                        Log.critical(f"unable to delete bucket: {bucket_name}")                    
                except:
                    Log.critical(f"unable to delete bucket: {bucket_name}")
        return True

    def finish_nuke_bucket(self, client, bucket_name):
        bucket = client.Bucket(bucket_name)
        try:
            bucket.object_versions.delete()
            return True
        except:
            return False

    def calculate_object_size(self, size):
        count = 0
        while size // 1024 > 0:
            size = size / 1024
            count += 1
        return str(round(size, 2)) + ' ' + self.size_table[count]

    def s3_to_local(self, bucket_name, local_folder, filename):
        CLIENT = self.SESSION.resource('s3')
        BUCKET = CLIENT.Bucket(bucket_name)
        for OBJECT in BUCKET.objects.all():
            s3_path, s3_filename = self.get_s3_path_filename(OBJECT.key)
            base = os.path.basename(filename)
            if filename is not None and base == s3_filename:
                local_folder_path = os.path.join(*[local_folder, s3_path])
                local_fullpath = os.path.join(local_folder_path, s3_filename)
                self.mkdir_p(local_folder_path)
                try:
                    BUCKET.download_file(OBJECT.key, local_fullpath)
                    Log.info(f"finished downloading {OBJECT.key}")
                except:
                    Log.warn(f"problem downloading {OBJECT.key}")
                    pass
            elif filename is None:
                local_folder_path = os.path.join(*[local_folder, s3_path])
                local_fullpath = os.path.join(*[local_folder_path, s3_filename])
                self.mkdir_p(local_folder_path)
                try:
                    BUCKET.download_file(OBJECT.key, local_fullpath)
                    Log.info(f"finished downloading {OBJECT.key}")
                except:
                    Log.warn(f"problem downloading {OBJECT.key}")
                    pass

    def local_to_s3(self, bucket_name, local_path):
        CURRENT_TIME = datetime.datetime.now()
        CLIENT = self.SESSION.client('s3')
        if os.path.isdir(local_path):
            for ROOT, DIRS, FILES in os.walk(local_path):
                for NAME in FILES:
                    FILE_PATH = os.path.join(ROOT, NAME)
                    try:
                        KEY = NAME
                        CLIENT.upload_file(FILE_PATH, bucket_name, KEY)
                        Log.info(f"finished uploading {NAME} to {bucket_name}")
                    except FileExistsError:
                        Log.warn(f"problem uploading {NAME} to {bucket_name}")
                        pass
        else:
            try:
                KEY = local_path
                CLIENT.upload_file(local_path, bucket_name, KEY)
                Log.info(f"finished uploading {local_path} to {bucket_name}")
            except FileExistsError:
                Log.warn(f"problem uploading {local_path} to {bucket_name}")
                pass

    def get_s3_path_filename(self, key):
        key = str(key)
        return key.replace(key.split('/')[-1],""), key.split('/')[-1]

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            pass

    def auto_refresh(self, aws_profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:    
            BUCKETS_TS = self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_buckets']['last_cache_update']
        except KeyError:
            BUCKETS_TS = 0    
        if TIME_NOW - float(BUCKETS_TS) > self.CACHE_UPDATE_INTERVAL:
            self.cache_buckets(aws_profile_name)
        self.CONFIGSTORE = Config('awstools')

    def refresh(self, aws_profile_name='default'):
        self.cache_buckets(aws_profile_name)
        
    def cache_buckets(self, aws_profile_name='default'):
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(aws_profile_name)
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
            self.get_session()
        RESOURCE = self.SESSION.resource('s3')
        Log.info('caching S3 buckets...')
        BUCKETS = [BUCKET.name for BUCKET in RESOURCE.buckets.all()]
        BUCKETS_CACHE = {}
        for BUCKET in BUCKETS:
            BUCKETS_CACHE[BUCKET] = {
                'name': BUCKET
            }
        BUCKETS_CACHE['last_cache_update'] = TIMESTAMP
        DICT = {}
        DICT[self.AWS_REGION] = BUCKETS_CACHE
        self.CONFIGSTORE.update_metadata(DICT, 'cached_buckets', aws_profile_name, False)

    def get_cache(self, type, aws_profile_name, subtype=None):
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            return None
        if type not in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']:
            return None
        if subtype is None:
            return self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type]
        else:
            if subtype in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type]:
                return self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type][subtype]
            else:
                return None

    def show_cache(self, type, aws_profile_name):
        self.auto_refresh(aws_profile_name)
        DATA = []
        for ENTRY in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type][self.AWS_REGION]:
            DATA_ENTRY = {}
            if ENTRY != 'last_cache_update' and ENTRY != 'lastmod' and ENTRY != 'total':
                DATA_ENTRY['Name'] = ENTRY
                DATA.append(DATA_ENTRY)
        Log.info(f"{type}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")

    def get_object_tagging(self, bucket_name, key):
        CLIENT = self.SESSION.client('s3')
        RESPONSE = CLIENT.get_object_tagging(Bucket=bucket_name, Key=key)
        return RESPONSE
