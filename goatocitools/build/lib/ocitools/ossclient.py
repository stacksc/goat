import datetime, time, os, json, re, oci
from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from . import iam_nongc
from .oci_config import OCIconfig
from tabulate import tabulate
from pathlib import Path
from tqdm.auto import tqdm
from oci.object_storage.models import CreateBucketDetails
try:
    import importlib_resources as resources
except:
    from importlib import resources

CONFIGSTORE = Config('ocitools')

class OSSclient():

    def __init__(self, profile_name, region='us-ashburn-1', cache_only=False):
        CONFIGSTORE = Config('ocitools')
        self.CONFIG = OCIconfig()
        self.CONFIGSTORE = Config('ocitools')
        self.size_table={0: 'Bs', 1: 'KBs', 2: 'MBs', 3: 'GBs', 4: 'TBs', 5: 'PBs', 6: 'EBs'}
        self.CACHE_UPDATE_INTERVAL = 60*60*24*7 # update cache every week
        self.OCI_PROFILE = profile_name
        self.OCI_REGION = region
        self.CACHE_ONLY = cache_only
        self.OCID = CONFIGSTORE.get_metadata('tenancy', profile_name)
        self.CONFIG_FROM_FILE = {
                'tenancy': CONFIGSTORE.get_metadata('tenancy', profile_name),
                'user': CONFIGSTORE.get_metadata('user', profile_name),
                'fingerprint': CONFIGSTORE.get_metadata('fingerprint', profile_name),
                'key_file': CONFIGSTORE.get_metadata('key_file', profile_name),
                'region': self.OCI_REGION
        }
        try:
            oci.config.validate_config(self.CONFIG_FROM_FILE)
        except:
            Log.critical('unable to setup a proper oci configuration file')

        if not self.CACHE_ONLY:
            self.get_connections()

    def get_connections(self):
        self.OSS = oci.object_storage.ObjectStorageClient(self.CONFIG_FROM_FILE)
        self.CLIENT = oci.identity.IdentityClient(self.CONFIG_FROM_FILE)
        self.NAMESPACE = self.OSS.get_namespace(compartment_id=self.OCID).data
        self.TENANTNAME = self.CLIENT.get_tenancy(tenancy_id=self.OCID).data.name
        return self.OSS, self.CLIENT, self.NAMESPACE, self.TENANTNAME

    def get_region_from_profile(self, profile_name):
        REGION = self.CONFIG.get_from_config('config', 'region', profile_name=profile_name)
        if REGION is None:
            Log.critical("Please run goat oci iam authenticate for the target profile before using the oss module")
        return REGION

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            pass

    def auto_refresh(self, profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:    
            BUCKETS_TS = self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_buckets']['last_cache_update']
        except KeyError:
            BUCKETS_TS = 0    
        if TIME_NOW - float(BUCKETS_TS) > self.CACHE_UPDATE_INTERVAL:
            self.cache_buckets(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def refresh(self, profile_name='default'):
        self.cache_buckets(profile_name)

    def oss_to_local(self, bucket_name, local_folder, filename, namespace):
        GET_OBJ = self.OSS.get_object(namespace, bucket_name, filename)
        TOTAL = int(GET_OBJ.headers.get('content-length', 0))
        OSS_PATH, OSS_FILENAME = self.get_oss_path_filename(filename)
        BASE = os.path.basename(filename)
        if filename is not None and BASE == OSS_FILENAME:
            LOCAL_FOLDER_PATH = os.path.join(*[local_folder, OSS_PATH])
            LOCAL_FULLPATH = os.path.join(LOCAL_FOLDER_PATH, OSS_FILENAME)
            self.mkdir_p(LOCAL_FOLDER_PATH)
        os.makedirs((local_folder), exist_ok=True)
        print()
        try:
            with open(LOCAL_FULLPATH, 'wb', buffering = 2 ** 24) as f, tqdm(
                desc=str(filename),
                total=TOTAL,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for DATA in GET_OBJ.data.iter_content(chunk_size=1024):
                    SIZE = f.write(DATA)
                    bar.update(SIZE)
            print()
            return True
        except KeyboardInterrupt:
            print(color.RED + "\nCaught KeyboardInterrupt, exiting...\n" + color.RESET)
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        return False

    def local_to_oss(self, bucket_name, local_path, namespace):
        CURRENT_TIME = datetime.datetime.now()
        object_name = local_path
        if not os.path.isfile(object_name) and not os.path.isdir(object_name):
            Log.critical("unable to upload object to OSS because the file does not exist")
        if os.path.isfile(object_name):
            with open(object_name, 'rb') as f:
                try:
                    obj = self.OSS.put_object(namespace, bucket_name, object_name, f)
                    Log.info(f"finished uploading {object_name} to {bucket_name}")
                    return True
                except:
                    Log.warn(f"problem uploading {object_name} to {bucket_name}")
                    return False
        else:
            dir = local_path + os.path.sep + "*"
            proc_list = []
            for f in glob(dir):
                if os.path.isfile(f):
                    p = Process(target=upload_to_object_storage, args=(self.CONFIG_FROM_FILE, namespace, bucket_name, f, profile_name))
                    p.start()
                    proc_list.append(p)
            for job in proc_list:
                job.join()
        return 0

    def upload_to_object_storage(self, config, namespace, bucket_name, local_path, profile_name):
        CURRENT_TIME = datetime.datetime.now()
        if os.path.isdir(local_path):
            for ROOT, DIRS, FILES in os.walk(local_path):
                for NAME in FILES:
                    FILE_PATH = os.path.join(ROOT, NAME)
                    with open(FILE_PATH, "rb") as in_file:
                        KEY = NAME
                        try:
                            self.OSS.put_object(namespace,
                                                bucket_name,
                                                KEY,
                                                in_file)
                            Log.info(f"finished uploading {NAME} to {bucket_name}")
                            return True
                        except:
                            Log.warn(f"problem uploading {KEY} to {bucket_name}")
                            return False
                            pass
        else:
            try:
                KEY = local_path
                with open(local_path, "rb") as in_file:
                    try:
                        self.OSS.put_object(namespace,
                                            bucket_name,
                                            KEY,
                                            in_file)
                        Log.info(f"finished uploading {NAME} to {bucket_name}")
                        return True
                    except:
                        Log.warn(f"problem uploading {KEY} to {bucket_name}")
                        return False
            except:
                pass

    def get_compartments(self):
        COMPARTMENTS = self.CLIENT.list_compartments(self.OCID, compartment_id_in_subtree=True).data
        ROOT_COMPARTMENT = self.CLIENT.get_compartment(compartment_id=self.OCID).data
        COMPARTMENTS.append(ROOT_COMPARTMENT)
        return COMPARTMENTS
       
    def show_bucket_content(self, bucket_name, profile_name, total=0):
        BUCKETS = CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_buckets'][self.OCI_REGION]
        for BUCKETNAME in BUCKETS:
            if BUCKETNAME == bucket_name:
                namespace = BUCKETS[BUCKETNAME]['namespace']
        TIMEOUT = time.time() + 90
        ITEMS = []
        LASTMOD = ''
        TOTAL = total
        if self.CACHE_ONLY:
            self.get_connections()
        prefix_files_name = ''
        BUCKETS = self.OSS.list_buckets(compartment_id=self.OCID, namespace_name=namespace).data
        OBJECTS = self.OSS.list_objects(namespace, bucket_name, prefix=prefix_files_name, fields="name")
        OBJECTS_LIST = OBJECTS.data.objects
        prefix_files_name = ''
        for NAME in OBJECTS_LIST:
            ITEMS.append(NAME.name)
        return ITEMS

    def cache_buckets(self, profile_name='default'):
        osfields = ('namespaceName','bucketName','compartmentName','compartmentOcid')
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        
        Log.info('caching OCI object storage buckets...')
        BUCKETS_CACHE = {}
        COMPARTMENTS = self.get_compartments()
        for COMPARTMENT in COMPARTMENTS:
            BUCKETS = []
            NAMESPACE = []
            try:
                NAMESPACE = self.OSS.get_namespace(compartment_id=COMPARTMENT.id).data
                BUCKETS = self.OSS.list_buckets(compartment_id=COMPARTMENT.id, namespace_name=NAMESPACE).data
                COMP_NAME = str(COMPARTMENT.name)
                COMP_OCID = str(COMPARTMENT.id)
                if len(BUCKETS) > 0:
                    Log.debug("compartment name: " + COMP_NAME + " holds object storage buckets in region " + self.OCI_REGION)
                    for BUCKET in BUCKETS:
                        if BUCKET:
                            BUCKETNAME = str(BUCKET.name)
                            OBJECT_LIST = self.OSS.list_objects(NAMESPACE, BUCKETNAME, fields="name,timeCreated,size")
                            BUCKETS_CACHE[BUCKETNAME] = {
                                'name': BUCKETNAME,
                                'namespace': NAMESPACE,
                                'compartment': COMP_NAME,
                                'ocid': COMP_OCID
                            }
            except oci.exceptions.ServiceError as e:
                BUCKETS = ''
                pass

        BUCKETS_CACHE['last_cache_update'] = TIMESTAMP
        DICT = {}
        DICT[self.OCI_REGION] = BUCKETS_CACHE
        self.CONFIGSTORE.update_metadata(DICT, 'cached_buckets', profile_name, True)

    def get_cache(self, type, profile_name, subtype=None):
        if profile_name not in self.CONFIGSTORE.PROFILES:
            return None
        if type not in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
            return None
        if subtype is None:
            return self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][oci_region]
        else:
            if subtype in self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type]:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][subtype]
            else:
                return None

    def show_cache(self, type, profile_name, oci_region):
        DATA = []
        for ENTRY in self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][oci_region]:
            DATA_ENTRY = {}
            if ENTRY != 'last_cache_update' and ENTRY != 'lastmod' and ENTRY != 'total':
                DATA_ENTRY['Name'] = ENTRY
                DATA.append(DATA_ENTRY)
        Log.info(f"{type}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")

    def get_oss_path_filename(self, key):
        key = str(key)
        return key.replace(key.split('/')[-1],""), key.split('/')[-1]

    def delete_bucket(self, namespace, bucket_name, profile_name):
        try:
            RESPONSE = oci.pagination.list_call_get_all_results(self.OSS.list_preauthenticated_requests, namespace_name=namespace, bucket_name=bucket_name)
        except:
            Log.critical(f"FAIL: bucket {bucket_name} not found in profile: {profile_name}")
            return False

        if RESPONSE:
            for auth in RESPONSE.data:
                self.OSS.ObjectStorageClient.delete_preauthenticated_request(self.OSS, namespace_name=namespace, bucket_name=bucket_name, par_id=auth.id)
        try:
            self.OSS.delete_bucket(namespace, bucket_name)
            Log.info('INFO: deleted bucket from: ' + profile_name)
            return True
        except:
            cmd='oci --profile %s os object bulk-delete --bucket-name %s --force >/dev/null 2>&1' %(profile_name, bucket_name)
            os.system(cmd)
            self.OSS.delete_bucket(namespace, bucket_name)
            Log.info('deleted bucket from: ' + profile_name)
            return True
        return 0

    def create_bucket(self, ocid, namespace, bucket_name, profile_name):
        request = CreateBucketDetails(public_access_type='NoPublicAccess')
        request.compartment_id = ocid
        request.name = bucket_name
        bucket = self.OSS.create_bucket(namespace, request)
        if bucket.data.etag:
            Log.info("bucket created for " + profile_name + " and bucket tag " + bucket.data.etag)
            return True

def setup_config_file(profile_name, oci_region):
    CONFIG_FROM_FILE = {
        'tenancy': CONFIGSTORE.get_metadata('tenancy', profile_name),
        'user': CONFIGSTORE.get_metadata('user', profile_name),
        'fingerprint': CONFIGSTORE.get_metadata('fingerprint', profile_name),
        'key_file': CONFIGSTORE.get_metadata('key_file', profile_name),
        'region': oci_region
    }
    try:
        oci.config.validate_config(CONFIG_FROM_FILE)
    except:
        Log.critical('unable to setup a proper oci configuration file')
    return CONFIG_FROM_FILE    
