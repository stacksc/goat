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

class SECRETclient():

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
        self.KEYS = oci.key_management.KmsVaultClient(self.CONFIG_FROM_FILE)
        self.COMPOSITE = oci.key_management.KmsVaultClientCompositeOperations(self.KEYS)
        return self.CLIENT, self.TENANTNAME, self.VAULT, self.SECRETS, self.KEYS, self.COMPOSITE

    def get_secrets_cache(self, profile_name='default'):
        FIELDS = ['id','key_id','lifecycle_state','secret_name','description']
        SECRETS_CACHE = {}
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching secrets across all compartments...")
        COMPARTMENTS = self.get_compartments()
        for COMPARTMENT in COMPARTMENTS:
            if COMPARTMENT.lifecycle_state != 'ACTIVE':
                continue
            SECRETS = []
            VAULT_ID = ''
            try:
                SECRETS = self.VAULT.list_secrets(compartment_id=COMPARTMENT.id, lifecycle_state="ACTIVE").data
                COMP_NAME = str(COMPARTMENT.name)
                COMP_OCID = str(COMPARTMENT.id)
                if len(SECRETS) > 0:
                    Log.debug("compartment name: " + COMP_NAME + " holds secrets in region " + self.OCI_REGION)
                    for DATA in SECRETS:
                        if DATA:
                            ID = DATA.id
                            KEY_ID = DATA.key_id
                            SECRET_RESPONSE = self.SECRETS.get_secret_bundle(secret_id=ID).data
                            TYPE = SECRET_RESPONSE.secret_bundle_content.content_type
                            CONTENT = SECRET_RESPONSE.secret_bundle_content.content
                            SECRET_NAME = DATA.secret_name
                            DESC = DATA.description
                            NEW_VAULT_ID = DATA.vault_id
                            STATE = DATA.lifecycle_state
                            SECRETS_CACHE[ID] = {
                                'secret_name': SECRET_NAME,
                                'content': CONTENT,
                                'type': TYPE,
                                'description': DESC,
                                'compartment': COMP_NAME,
                                'lifecycle_state': STATE
                            }
            except oci.exceptions.ServiceError as e:
                SECRETS = ''
                pass

        SECRETS_CACHE['last_cache_update'] = TIMESTAMP
        DICT = {}
        DICT[self.OCI_REGION] = SECRETS_CACHE
        self.CONFIGSTORE.update_metadata(DICT, 'cached_secrets', profile_name, True)

    def describe(self, secret_ocid, profile_name):
        try:
            self.get_connections()
        except:
            return None
        SECRET_RESPONSE = self.SECRETS.get_secret_bundle(secret_id=secret_ocid).data
        TYPE = SECRET_RESPONSE.secret_bundle_content.content_type
        CONTENT = SECRET_RESPONSE.secret_bundle_content.content
        DATA = self.VAULT.get_secret(secret_id=secret_ocid).data
        DICT = {}
        DICT[secret_ocid] = DATA
        DICT['content'] = CONTENT
        return DICT

    def get_cached_secrets(self, profile_name):
        if profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_secrets' in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_secrets'][self.OCI_REGION]
        else:
            return None

    def refresh(self, type, profile_name):
        if type == 'cached_secrets':
            Log.info("caching secrets...")
            self.get_secrets_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def get_compartments(self):
        COMPARTMENTS = self.CLIENT.list_compartments(self.OCID, compartment_id_in_subtree=True).data
        ROOT_COMPARTMENT = self.CLIENT.get_compartment(compartment_id=self.OCID).data
        COMPARTMENTS.append(ROOT_COMPARTMENT)
        return COMPARTMENTS

    def delete_secret(self, ocid):
        DETAILS = oci.vault.models.ScheduleSecretDeletionDetails()
        RESPONSE = self.VAULT.schedule_secret_deletion(ocid, DETAILS)
        return RESPONSE

    def list_secrets(self, ocid):
        self.get_connections()
        SECRETS = self.VAULT.list_secrets(compartment_id=ocid, lifecycle_state="ACTIVE").data
        return SECRETS

    def create_secret(self, compartment_id, secret_content, secret_name, vault_id, key_id, secret_description):
        self.get_connections()
        VAULT_COMPOSITE = oci.vault.VaultsClientCompositeOperations(self.VAULT)
        SECRET_CONTENT_DETAILS = oci.vault.models.Base64SecretContentDetails(content_type=oci.vault.models.SecretContentDetails.CONTENT_TYPE_BASE64, name=secret_name, stage="CURRENT", content=secret_content)
        SECRETS_DETAILS = oci.vault.models.CreateSecretDetails(compartment_id=compartment_id, description=secret_description, secret_content=SECRET_CONTENT_DETAILS, secret_name=secret_name, vault_id=vault_id, key_id=key_id)
        RESPONSE = VAULT_COMPOSITE.create_secret_and_wait_for_state(create_secret_details=SECRETS_DETAILS, wait_for_states=[oci.vault.models.Secret.LIFECYCLE_STATE_ACTIVE])
        return RESPONSE.data

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
        SCHEDULE_KEY_DELETION_DETAILS = oci.key_management.models.sc(time_of_deletion=deletion_time)
        RESPONSE = vault_management_client_composite.schedule_key_deletion_and_wait_for_state(schedule_key_deletion_details, wait_for_states=[oci.key_management.models.Key.LIFECYCLE_STATE_PENDING_DELETION])
        return RESPONSE

    def auto_refresh(self, profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:
            SECRET_TS = self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_secrets']['last_cache_update']
        except KeyError:
            SECRET_TS = 0
        if TIME_NOW - float(SECRET_TS) > self.CACHE_UPDATE_INTERVAL:
            self.get_secrets_cache(profile_name)
        self.CONFIGSTORE = Config('ocitools')
