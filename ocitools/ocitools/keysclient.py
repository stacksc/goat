from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .oci_config import OCIconfig
from . import iam_nongc
import datetime
from tabulate import tabulate
import os, oci, json

CONFIGSTORE = Config('ocitools')

class KEYclient():

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
        self.KEYS = oci.key_management.KmsVaultClient(self.CONFIG_FROM_FILE)
        self.COMPOSITE = oci.key_management.KmsVaultClientCompositeOperations(self.KEYS)
        return self.CLIENT, self.TENANTNAME, self.VAULT, self.SECRETS, self.KEYS, self.COMPOSITE

    def get_keys_cache(self, profile_name='default'):
        KEYS_CACHE = {}
        VAULTS_CACHE = {}
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching vault keys across all compartments...")
        COMPARTMENTS = self.get_compartments()
        for COMPARTMENT in COMPARTMENTS:
            if COMPARTMENT.lifecycle_state != 'ACTIVE':
                continue
            KEYS = []
            VAULT_ID = ''
            try:
                VAULTS = self.KEYS.list_vaults(compartment_id=COMPARTMENT.id).data
                COMP_NAME = str(COMPARTMENT.name)
                COMP_OCID = str(COMPARTMENT.id)
                if len(VAULTS) > 0:
                    Log.debug("compartment name: " + COMP_NAME + " holds vaults in region " + self.OCI_REGION)
                    for DATA in VAULTS:
                        if DATA:
                            ID = DATA.id
                            NAME = DATA.display_name
                            CRYPTO_ENDPOINT = DATA.crypto_endpoint
                            MGMT_ENDPOINT = DATA.management_endpoint
                            STATE = DATA.lifecycle_state
                            if STATE != 'ACTIVE':
                                continue
                            VAULTS_CACHE[ID] = {
                                'display_name': NAME,
                                'compartment': COMP_OCID,
                                'crypto_endpoint': CRYPTO_ENDPOINT,
                                'management_endpoint': MGMT_ENDPOINT,
                                'lifecycle_state': STATE
                            }
            except oci.exceptions.ServiceError as e:
                VAULTS = ''
                pass

        for I in VAULTS_CACHE:
            NAME = VAULTS_CACHE[I]["display_name"]
            ID = VAULTS_CACHE[I]["compartment"]
            ENDPOINT = VAULTS_CACHE[I]["management_endpoint"]
            MYKEYS = self.list_keys(ID, ENDPOINT)

        for I in MYKEYS:
            ID = I.id
            NAME = I.display_name
            STATE = I.lifecycle_state
            ALGORITHM = I.algorithm
            MODE = I.protection_mode
            if STATE != 'ENABLED':
                continue
            else:
                KEYS_CACHE[ID] = {
                    'display_name': NAME,
                    'lifecycle_state': STATE,
                    'protection_mode': MODE,
                    'algorithm': ALGORITHM
                }
        KEYS_CACHE['last_cache_update'] = TIMESTAMP
        DICT = {}
        DICT[self.OCI_REGION] = KEYS_CACHE
        self.CONFIGSTORE.update_metadata(DICT, 'cached_keys', profile_name, True)
        self.CONFIGSTORE = Config('ocitools')

    def describe(self, key_ocid, profile_name):
        try:
            self.get_connections()
        except:
            return None
        DATA = self.KEYS.get_key(key_id=key_ocid).data
        DICT = {}
        DICT[key_ocid] = DATA
        return DICT

    def get_cached_keys(self, profile_name):
        if profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_keys' in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_keys'][self.OCI_REGION]
        else:
            return None

    def refresh(self, type, profile_name):
        if type == 'cached_keys':
            Log.info("caching keys...")
            self.get_keys_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def get_compartments(self):
        COMPARTMENTS = self.CLIENT.list_compartments(self.OCID, compartment_id_in_subtree=True).data
        ROOT_COMPARTMENT = self.CLIENT.get_compartment(compartment_id=self.OCID).data
        COMPARTMENTS.append(ROOT_COMPARTMENT)
        return COMPARTMENTS

    def list_keys(self, ocid, service_endpoint):
        self.get_connections()
        vault_management_client = oci.key_management.KmsManagementClient(self.CONFIG_FROM_FILE, service_endpoint=service_endpoint)
        KEYS = vault_management_client.list_keys(compartment_id=ocid, sort_by="DISPLAYNAME").data
        return KEYS

    def create_key(self, key_name, compartment_id, service_endpoint):
        vault_management_client = oci.key_management.KmsManagementClient(self.CONFIG_FROM_FILE, service_endpoint=service_endpoint)
        vault_management_client_composite = oci.key_management.KmsManagementClientCompositeOperations(vault_management_client)
        KEY_SHAPE = oci.key_management.models.KeyShape(algorithm="AES", length=32)
        KEY_DETAILS = oci.key_management.models.CreateKeyDetails(compartment_id=compartment_id, display_name=key_name, key_shape=KEY_SHAPE)
        RESPONSE = vault_management_client_composite.create_key_and_wait_for_state(KEY_DETAILS, wait_for_states=[oci.key_management.models.Key.LIFECYCLE_STATE_ENABLED])
        return RESPONSE.data

    def schedule_deletion_key(self, deletion_time, key_id, service_endpoint):
        vault_management_client = oci.key_management.KmsManagementClient(self.CONFIG_FROM_FILE, service_endpoint=service_endpoint)
        vault_management_client_composite = oci.key_management.KmsManagementClientCompositeOperations(vault_management_client)
        SCHEDULE_KEY_DELETION_DETAILS = oci.key_management.models.ScheduleKeyDeletionDetails(time_of_deletion=deletion_time)
        RESPONSE = vault_management_client_composite.schedule_key_deletion_and_wait_for_state(key_id=key_id, schedule_key_deletion_details=SCHEDULE_KEY_DELETION_DETAILS, wait_for_states=[oci.key_management.models.Key.LIFECYCLE_STATE_PENDING_DELETION])
        return RESPONSE

    def auto_refresh(self, profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:
            KEYS_TS = self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_keys']['last_cache_update']
        except KeyError:
            KEYS_TS = 0
        if TIME_NOW - float(KEYS_TS) > self.CACHE_UPDATE_INTERVAL:
            self.get_keys_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')
