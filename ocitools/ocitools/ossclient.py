import datetime, time, os, importlib_resources, json, re, oci
from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from . import iam_nongc
from .oci_config import OCIconfig
from tabulate import tabulate
from pathlib import Path

CONFIGSTORE = Config('ocitools')

class OSSclient():

    def __init__(self, profile_name, region='us-ashburn-1', cache_only=False):
        self.CONFIG = OCIconfig()
        self.CONFIG_FROM_FILE = oci.config.from_file(profile_name=profile_name)
        self.CONFIGSTORE = Config('ocitools')
        self.size_table={0: 'Bs', 1: 'KBs', 2: 'MBs', 3: 'GBs', 4: 'TBs', 5: 'PBs', 6: 'EBs'}
        self.CACHE_UPDATE_INTERVAL = 60*60*24*7 # update cache every week
        self.OCI_PROFILE = profile_name
        self.OCI_REGION = region
        self.CACHE_ONLY = cache_only
        self.OCID = CONFIGSTORE.get_metadata('tenancy', profile_name)
        if not self.CACHE_ONLY:
            self.get_connections()

    def get_connections(self):
        Log.info(f"connecting to OSS as {self.OCI_PROFILE} via {self.OCI_REGION}...")
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

    def get_compartments(self):
        COMPARTMENTS = self.CLIENT.list_compartments(self.OCID, compartment_id_in_subtree=True).data
        ROOT_COMPARTMENT = self.CLIENT.get_compartment(compartment_id=self.OCID).data
        COMPARTMENTS.append(ROOT_COMPARTMENT)
        return COMPARTMENTS
        
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
                    print("INFO: compartment name: " + COMP_NAME + " holds object storage buckets in region " + self.OCI_REGION)
                    for BUCKET in BUCKETS:
                        if BUCKET:
                            BUCKETNAME = str(BUCKET.name)
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
        self.CONFIGSTORE.update_metadata(BUCKETS_CACHE, 'cached_buckets', profile_name, True)

    def get_cache(self, type, profile_name, subtype=None):
        if profile_name not in self.CONFIGSTORE.PROFILES:
            return None
        if type not in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
            return None
        if subtype is None:
            return self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type]
        else:
            if subtype in self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type]:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][subtype]
            else:
                return None

    def show_cache(self, type, profile_name):
        self.auto_refresh(profile_name)
        DATA = []
        for ENTRY in self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type]:
            DATA_ENTRY = {}
            if ENTRY != 'last_cache_update' and ENTRY != 'lastmod' and ENTRY != 'total':
                DATA_ENTRY['Name'] = ENTRY
                DATA.append(DATA_ENTRY)
        Log.info(f"{type}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")

