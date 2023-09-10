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

class DBSclient():

    def __init__(self, profile_name, region='us-ashburn-1', cache_only=False):
        self.CONFIGSTORE = Config('ocitools')
        self.CONFIG = OCIconfig()
        self.OCI_REGION = region
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
        self.CACHE_UPDATE_INTERVAL = 60*60*24*7 # update cache every week
        self.OCI_PROFILE = profile_name
        self.CACHE_ONLY = cache_only
        self.OCID = CONFIGSTORE.get_metadata('tenancy', profile_name)
        if not self.CACHE_ONLY:
            self.get_connections()

    def get_connections(self):
        self.CLIENT = oci.identity.IdentityClient(self.CONFIG_FROM_FILE)
        self.TENANTNAME = self.CLIENT.get_tenancy(tenancy_id=self.OCID).data.name
        self.COMPUTE = oci.core.ComputeClient(self.CONFIG_FROM_FILE)
        self.NETWORK = oci.core.VirtualNetworkClient(self.CONFIG_FROM_FILE)
        self.DBS = oci.database.DatabaseClient(self.CONFIG_FROM_FILE)
        return self.CLIENT, self.COMPUTE, self.NETWORK, self.TENANTNAME

    def show_dbs_instances(self, profile_name):
        CACHE = self.get_cached_dbs_instances(profile_name)
        if CACHE is not None:
            return CACHE

    def DisplayInstances(self, instances, compartmentName, instancetype, region_name):

        TIMESTAMP = str(datetime.datetime.now().timestamp())
        AllPredefinedTags = True 
        NoValueString = "n/a"
        FieldSeperator = ","
        EndLine = "\n"
        customertags = []
        DBS_CACHE = {}
        ATP_CACHE = {}
        ADW_CACHE = {}

        for instance in instances:
            privateips = ""
            publicips = ""
            instancetypename = ""
            tagtxt = ""
            OS = ""
            # Handle details for Database Instances
            if instancetype == "DB":
                OCPU, MEM, SSD = shapes.ComputeShape(instance.shape)
                OCPU = instance.cpu_core_count # Overwrite Shape's CPU count, with DB enabled CPU count
                response = self.DBS.list_db_nodes(compartment_id=instance.compartment_id,db_system_id=instance.id)
                dbnodes = response.data
                try:
                    for dbnode in dbnodes:
                        responsenic = NetworkClient.get_vnic(vnic_id=dbnode.vnic_id)
                        nicinfo = responsenic.data
                        privateips = privateips + nicinfo.private_ip + " "
                        publicips = publicips + nicinfo.public_ip + " "
                except:
                    privateips = NoValueString
                    publicips = NoValueString

                instancetypename = "DB " + instance.database_edition
                OS = "Oracle Linux 6.8"
                shape = instance.shape
                prefix, AD = instance.availability_domain.split(":")

                DBS_CACHE[instance.display_name] = {
                                'display_name': instance.display_name,
                                'lifecycle_state': instance.lifecycle_state,
                                'ocpu': OCPU,
                                'shape': shape,
                                'compartment_name': compartmentName,
                                'type': instancetypename,
                                'public_ips': publicips,
                                'private_ips': privateips,
                                'OS': OS,
                                'AD': AD
                }
                DBS_CACHE['last_cache_update'] = TIMESTAMP

            # Handle details for Autonomous Database (ATP)
            if instancetype == "ATP":
                OCPU = instance.cpu_core_count
                MEM = NoValueString
                SSD = instance.data_storage_size_in_tbs
                instancetypename = "ATP"
                OS = NoValueString
                shape = "ATP"
                AD = region_name.upper()
                privateips = NoValueString
                publicips = NoValueString

                ATP_CACHE[instance.db_name] = {
                                'display_name': instance.db_name,
                                'lifecycle_state': instance.lifecycle_state,
                                'ocpu': OCPU,
                                'memory': MEM,
                                'shape': shape,
                                'compartment_name': compartmentName,
                                'type': instancetypename,
                                'public_ips': publicips,
                                'private_ips': privateips,
                                'OS': OS,
                                'AD': AD
                }
                ATP_CACHE['last_cache_update'] = TIMESTAMP

            # Handle details for Autonomous Database (ADW)
            if instancetype == "ADW":
                OCPU = instance.cpu_core_count
                MEM = NoValueString
                SSD = instance.data_storage_size_in_tbs
                instancetypename = "ADW"
                OS = NoValueString
                shape = "ADW"
                AD = region_name.upper()
                privateips = NoValueString
                publicips = NoValueString

                ADW_CACHE[instance.display_name] = {
                                'display_name': instance.display_name,
                                'lifecycle_state': instance.lifecycle_state,
                                'ocpu': OCPU,
                                'memory': MEM,
                                'shape': shape,
                                'compartment_name': compartmentName,
                                'type': instancetypename,
                                'public_ips': publicips,
                                'private_ips': privateips,
                                'OS': OS,
                                'AD': AD
                }
                ADW_CACHE['last_cache_update'] = TIMESTAMP
            try:
                namespaces = instance.defined_tags
                for customertag in customertags:
                    try:
                        tagtxt = tagtxt + FieldSeperator + namespaces[customertag[0]][customertag[1]]
                    except:
                        tagtxt = tagtxt + FieldSeperator + NoValueString
            except:
                tagtxt = ""  # No Tags
        return DBS_CACHE, ADW_CACHE, ATP_CACHE

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
            REGION_CACHE[KEY] = {
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

    def get_dbs_instances(self, profile_name='default'):

        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching DBS instances across all compartments...")
        response = oci.pagination.list_call_get_all_results(self.CLIENT.list_compartments,self.OCID,compartment_id_in_subtree=True)
        compartments = response.data
        RootCompartment = oci.identity.models.Compartment()
        RootCompartment.id = self.OCID
        RootCompartment.name = "root"
        RootCompartment.lifecycle_state = "ACTIVE"
        compartments.insert(0, RootCompartment)
        for compartment in compartments:
            compartmentName = compartment.name
            if compartment.lifecycle_state == "ACTIVE":
                Log.debug("processing compartment:  " + compartmentName)
                compartmentID = compartment.id
                try:
                    response = oci.pagination.list_call_get_all_results(self.DBS.list_instances,compartment_id=compartmentID)
                    if len(response.data) > 0:
                        DBS_CACHE, ADW_CACHE, ATP_CACHE = self.DisplayInstances(response.data, compartmentName, "DB", self.OCI_REGION)
                        DATADICT = {}
                        DATA = []
                        for I in DBS_CACHE:
                            if 'last_cache_update' not in I:
                                DATA.append(DBS_CACHE[I])
                        if DATA:
                            DATADICT = DATA
                            DICT = {}
                            DICT[self.OCI_REGION] = DBS_CACHE
                            self.CONFIGSTORE.update_metadata(DICT, 'cached_dbs_instances', profile_name, True)
                            self.CONFIGSTORE = Config('ocitools')
                except:
                    pass

                try:
                    response = oci.pagination.list_call_get_all_results(self.DBS.list_autonomous_data_warehouses,compartment_id=compartmentID)
                    if len(response.data) > 0:
                        DBS_CACHE, ADW_CACHE, ATP_CACHE = self.DisplayInstances(response.data, compartmentName, "ADW", self.OCI_REGION)
                        DATADICT = {}
                        DATA = []
                        for I in ADW_CACHE:
                            if 'last_cache_update' not in I:
                                DATA.append(ADW_CACHE[I])
                        if DATA:
                            DATADICT = DATA
                            DICT = {}
                            DICT[self.OCI_REGION] = ADW_CACHE
                            self.CONFIGSTORE.update_metadata(DICT, 'cached_dbs_instances', profile_name, True)
                            self.CONFIGSTORE = Config('ocitools')
                except:
                    pass

                try:
                    response = oci.pagination.list_call_get_all_results(self.DBS.list_autonomous_databases,compartment_id=compartmentID)
                    if len(response.data) > 0:
                        DBS_CACHE, ADW_CACHE, ATP_CACHE = self.DisplayInstances(response.data, compartmentName, "ATP", self.OCI_REGION)
                        DATADICT = {}
                        DATA = []
                        for I in ATP_CACHE:
                            if 'last_cache_update' not in I:
                                DATA.append(ATP_CACHE[I])
                        if DATA:
                            DATADICT = DATA
                            DICT = {}
                            DICT[self.OCI_REGION] = ATP_CACHE
                            self.CONFIGSTORE.update_metadata(DICT, 'cached_dbs_instances', profile_name, True)
                            self.CONFIGSTORE = Config('ocitools')
                except:
                    pass

    def get_cached_dbs_instances(self, profile_name):
        if profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_dbs_instances' in self.CONFIGSTORE.PROFILES[profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_dbs_instances']
        else:
            return None

    def refresh(self, type, profile_name):
        if type == 'cached_dbs_instances':
            Log.info("caching DBS instances...")
            self.get_dbs_instances(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def auto_refresh(self, profile_name):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:    
            DBS_INSTANCES_TS = self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_dbs_instances']['last_cache_update']
        except KeyError:
            DBS_INSTANCES_TS = 0    
        if TIME_NOW - float(DBS_INSTANCES_TS) > self.CACHE_UPDATE_INTERVAL:
            Log.info('automatic refresh of dbs instance cache initiated')
            self.refresh('cached_dbs_instances', profile_name)

    def get_region_from_profile(self, profile_name):
        REGION = self.CONFIG.get_from_config('config', 'region', profile_name=profile_name)
        if REGION is None:
            Log.critical("Please run goat oci iam authenticate for the target profile before using the oss module")
        return REGION
