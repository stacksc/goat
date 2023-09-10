from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .oci_config import OCIconfig
from . import iam_nongc
import datetime
from tabulate import tabulate
import os, oci, json

CONFIGSTORE = Config('ocitools')

class IAMclient():

    def __init__(self, profile_name, region='us-ashburn-1', cache_only=False):
        self.CONFIGSTORE = Config('ocitools')
        self.CONFIG = OCIconfig()
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
        self.CLIENT = oci.identity.IdentityClient(self.CONFIG_FROM_FILE)
        self.TENANTNAME = self.CLIENT.get_tenancy(tenancy_id=self.OCID).data.name
        self.VAULT = oci.vault.VaultsClient(self.CONFIG_FROM_FILE)
        self.SECRETS = oci.secrets.SecretsClient(self.CONFIG_FROM_FILE)
        self.KMS_VAULT = oci.key_management.KmsVaultClient(self.CONFIG_FROM_FILE)
        self.COMPOSITE = oci.key_management.KmsVaultClientCompositeOperations(self.KMS_VAULT)
        return self.CLIENT, self.TENANTNAME, self.VAULT, self.SECRETS, self.KMS_VAULT, self.COMPOSITE

    def get_compartments(self):
        try:
            self.get_connections()
        except:
            return None
        COMPARTMENTS = self.CLIENT.list_compartments(self.OCID, compartment_id_in_subtree=True).data
        ROOT_COMPARTMENT = self.CLIENT.get_compartment(compartment_id=self.OCID).data
        COMPARTMENTS.append(ROOT_COMPARTMENT)
        return COMPARTMENTS

    def get_region_from_profile(self, profile_name):
        REGION = self.CONFIG.get_from_config('config', 'region', profile_name=profile_name)
        if REGION is None:
            Log.critical("Please run goat oci iam authenticate for the target profile before using the oss module")
        return REGION

    def get_cached_compartments(self, profile_name):
        if profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_compartments' in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_compartments'][self.OCI_REGION]
        else:
            return None

    def refresh(self, type, profile_name):
        if type == 'cached_compartments':
            Log.info("caching compartments...")
            self.get_compartments_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def get_compartments_cache(self, profile_name='default'):
        CACHE = {}
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching compartment data across all levels...")
        COMPARTMENTS = self.get_compartments()
        for COMPARTMENT in COMPARTMENTS:
            DESC = COMPARTMENT.description
            ID = COMPARTMENT.id
            STATE = COMPARTMENT.lifecycle_state
            NAME = COMPARTMENT.name
            CACHE[ID] = {
                'name': NAME,
                'id': ID,
                'lifecycle_state': STATE,
                'description': DESC
            }
        CACHE['last_cache_update'] = TIMESTAMP
        DICT = {}
        DICT[self.OCI_REGION] = CACHE
        self.CONFIGSTORE.update_metadata(DICT, 'cached_compartments', profile_name, True)

    def describe(self, comp_ocid, profile_name):
        try:
            self.get_connections()
        except:
            return None
        RESPONSE = self.CLIENT.get_compartment(compartment_id=comp_ocid).data
        DICT = {}
        DICT[comp_ocid] = RESPONSE
        return DICT

    def create_compartment(self, comp_ocid, name, description):
        RESPONSE = self.CLIENT.create_compartment(create_compartment_details=oci.identity.models.CreateCompartmentDetails(compartment_id=comp_ocid, name=name, description=description)).data
        return RESPONSE

    def delete_compartment(self, comp_ocid):
        RESPONSE = self.CLIENT.delete_compartment(compartment_id=comp_ocid).headers
        return RESPONSE

