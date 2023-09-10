from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .oci_config import OCIconfig
from . import iam_nongc
import datetime
from tabulate import tabulate
import os, oci, json

CONFIGSTORE = Config('ocitools')

class VAULTclient():

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
        #Log.info(f"connecting to OCI as {self.OCI_PROFILE} via {self.OCI_REGION}...")
        self.CLIENT = oci.identity.IdentityClient(self.CONFIG_FROM_FILE)
        self.TENANTNAME = self.CLIENT.get_tenancy(tenancy_id=self.OCID).data.name
        self.VAULT = oci.vault.VaultsClient(self.CONFIG_FROM_FILE)
        self.SECRETS = oci.secrets.SecretsClient(self.CONFIG_FROM_FILE)
        self.KMS_VAULT = oci.key_management.KmsVaultClient(self.CONFIG_FROM_FILE)
        self.COMPOSITE = oci.key_management.KmsVaultClientCompositeOperations(self.KMS_VAULT)
        return self.CLIENT, self.TENANTNAME, self.VAULT, self.SECRETS, self.KMS_VAULT, self.COMPOSITE

    def get_vaults_cache(self, profile_name='default'):
        VAULTS_CACHE = {}
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching vault data across all compartments...")
        COMPARTMENTS = self.get_compartments()
        for COMPARTMENT in COMPARTMENTS:
            VAULTS = []
            try:
                VAULTS = self.KMS_VAULT.list_vaults(compartment_id=COMPARTMENT.id).data
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
                            VAULTS_CACHE[ID] = {
                                'display_name': NAME,
                                'compartment': COMP_NAME,
                                'crypto_endpoint': CRYPTO_ENDPOINT,
                                'management_endpoint': MGMT_ENDPOINT,
                                'lifecycle_state': STATE
                            }
            except oci.exceptions.ServiceError as e:
                VAULTS = ''
                pass
        VAULTS_CACHE['last_cache_update'] = TIMESTAMP
        DICT = {}
        DICT[self.OCI_REGION] = VAULTS_CACHE
        self.CONFIGSTORE.update_metadata(DICT, 'cached_vaults', profile_name, True)

    def describe(self, vault_ocid, profile_name):
        try:
            self.get_connections()
        except:
            return None
        RESPONSE = self.KMS_VAULT.get_vault(vault_ocid).data
        DICT = {}
        DICT[vault_ocid] = RESPONSE
        return DICT

    def get_cached_vaults(self, profile_name):
        if profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_vaults' in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_vaults'][self.OCI_REGION]
        else:
            return None

    def refresh(self, type, profile_name):
        if type == 'cached_vaults':
            Log.info("caching vaults...")
            self.get_vaults_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def get_compartments(self):
        try:
            self.get_connections()
        except:
            return None
        COMPARTMENTS = self.CLIENT.list_compartments(self.OCID, compartment_id_in_subtree=True).data
        ROOT_COMPARTMENT = self.CLIENT.get_compartment(compartment_id=self.OCID).data
        COMPARTMENTS.append(ROOT_COMPARTMENT)
        return COMPARTMENTS

    def create_vault(self, comp_id, vault_name):
        DETAILS = oci.key_management.models.CreateVaultDetails(compartment_id=comp_id, vault_type="DEFAULT", display_name=vault_name)
        try:
            RESPONSE = self.COMPOSITE.create_vault_and_wait_for_state(DETAILS, wait_for_states=[oci.key_management.models.Vault.LIFECYCLE_STATE_ACTIVE])
        except Exception as err:
            Log.critical(err)
        return RESPONSE

    def delete_vault(self, vault_id, deletion_time):
        schedule_vault_deletion_details = oci.key_management.models.ScheduleVaultDeletionDetails(time_of_deletion=deletion_time)
        RESPONSE = self.COMPOSITE.schedule_vault_deletion_and_wait_for_state(vault_id, schedule_vault_deletion_details=schedule_vault_deletion_details, wait_for_states=[oci.key_management.models.Vault.LIFECYCLE_STATE_PENDING_DELETION])
        return RESPONSE

    def get_region_from_profile(self, profile_name):
        REGION = self.CONFIG.get_from_config('config', 'region', profile_name=profile_name)
        if REGION is None:
            Log.critical("Please run goat oci iam authenticate for the target profile before using the oss module")
        return REGION

    def get_vaults(self, comp_id):
        VAULTS = self.KMS_VAULT.list_vaults(compartment_id=comp_id, sort_by='DISPLAYNAME', sort_order='ASC').data
        return VAULTS

    def auto_refresh(self, profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:
            VAULT_TS = self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_vaults']['last_cache_update']
        except KeyError:
            VAULT_TS = 0
        if TIME_NOW - float(VAULT_TS) > self.CACHE_UPDATE_INTERVAL:
            self.get_vaults_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')
