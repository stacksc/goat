from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .oci_config import OCIconfig
from . import iam_nongc
import datetime
from tabulate import tabulate
import os, oci, json
from . import shapes

CONFIGSTORE = Config('ocitools')

class REGIONSclient():

    def __init__(self, profile_name, region='us-ashburn-1', cache_only=False):
        self.CONFIGSTORE = Config('ocitools')
        self.CONFIG = OCIconfig()
        self.CONFIG_FROM_FILE = oci.config.from_file(profile_name=profile_name)
        self.CACHE_UPDATE_INTERVAL = 60*60*24*7 # update cache every week
        self.OCI_PROFILE = profile_name
        self.OCI_REGION = region
        self.CACHE_ONLY = cache_only
        self.OCID = CONFIGSTORE.get_metadata('tenancy', profile_name)
        if not self.CACHE_ONLY:
            self.get_connections()

    def get_connections(self):
        oci.regions.enable_instance_metadata_service()
        #Log.info(f"connecting to OCI as {self.OCI_PROFILE} via {self.OCI_REGION}...")
        self.CLIENT = oci.identity.IdentityClient(self.CONFIG_FROM_FILE)
        self.TENANTNAME = self.CLIENT.get_tenancy(tenancy_id=self.OCID).data.name
        return self.CLIENT, self.TENANTNAME

    def get_region_cache(self, profile_name='default'):
        REGION_CACHE = {}
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching region subscriptions...")
        REGION_SUBSCRIPTIONS = self.CLIENT.list_region_subscriptions(tenancy_id=self.OCID).data
        for DATA in REGION_SUBSCRIPTIONS:
            IS_HOME = DATA.is_home_region
            KEY = DATA.region_key
            NAME = DATA.region_name
            STATUS = DATA.status
            REGION_CACHE[NAME] = {
                 'region_key': KEY,
                 'region_name': NAME,
                 'status': STATUS,
                 'is_home_region': IS_HOME,
            }
        DATADICT = {}
        DATA = []
        for I in REGION_CACHE:
            if 'last_cache_update' not in I:
                DATA.append(REGION_CACHE[I])
            if DATA:
                 DATADICT = DATA
                 self.CONFIGSTORE.update_metadata(REGION_CACHE, 'cached_regions', profile_name, True)
                 self.CONFIGSTORE = Config('ocitools')

    def get_cached_regions(self, profile_name):
        if profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_regions' in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_regions']
        else:
            return None

    def refresh(self, type, profile_name):
        if type == 'cached_regions':
            Log.info("caching regions...")
            self.get_region_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def describe(self, profile_name):
        self.get_connections()
        # Get the current user
        USER = self.CLIENT.get_user(self.CONFIG_FROM_FILE["user"]).data
        TENANCY = self.CLIENT.get_tenancy(tenancy_id=self.OCID).data
        return USER, TENANCY
   
    def list_regions(self, profile_name):
        if not self.CLIENT:
            self.get_connections()
        return self.CLIENT.list_regions().data 
