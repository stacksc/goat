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

class MyComputeClient():

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
        return self.CLIENT, self.COMPUTE, self.NETWORK, self.TENANTNAME

    def auto_refresh(self, profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:
            INSTANCES_TS = self.CONFIGSTORE.PROFILES[profile_name]['metadata']['cached_instances']['last_cache_update']
        except KeyError:
            INSTANCES_TS = 0
        if TIME_NOW - float(INSTANCES_TS) > self.CACHE_UPDATE_INTERVAL:
            self.cache_instances(profile_name)
        self.CONFIGSTORE = Config('ocitools')

    def refresh(self, profile_name='default'):
        self.cache_instances(profile_name)

    def DisplayInstances(self, instances, compartmentName, instancetype, region_name):

        TIMESTAMP = str(datetime.datetime.now().timestamp())
        AllPredefinedTags = True 
        NoValueString = "n/a"
        FieldSeperator = ","
        EndLine = "\n"
        customertags = []
        header = "NAME,STATE,SERVICE,SHAPE,COMPARTMENT,AD".replace(",", FieldSeperator)
        COMPUTE_CACHE = {}

        for instance in instances:
            privateips = ""
            publicips = ""
            instancetypename = ""
            tagtxt = ""
            OS = ""
            if instancetype == "Compute":
                OCPU, MEM, SSD = shapes.ComputeShape(instance.shape)
                response = self.COMPUTE.list_vnic_attachments(compartment_id = instance.compartment_id, instance_id = instance.id)
                vnics = response.data
                try:
                    for vnic in vnics:
                        responsenic = self.NETWORK.get_vnic(vnic_id=vnic.vnic_id)
                        nicinfo = responsenic.data
                        privateips = privateips + nicinfo.private_ip + " "
                        publicips = publicips + nicinfo.public_ip + " "
                except:
                    privateips = NoValueString
                    publicips = NoValueString
                instancetypename = "Compute"
                namespaces = instance.defined_tags
                shape = instance.shape
                # Get OS Details
                try:
                    response = self.COMPUTE.get_image(instance.source_details.image_id)
                    imagedetails = response.data
                    OS = imagedetails.display_name
                except:
                    OS = NoValueString
                prefix, AD = instance.availability_domain.split(":")
            try:
                namespaces = instance.defined_tags
                for customertag in customertags:
                    try:
                        tagtxt = tagtxt + FieldSeperator + namespaces[customertag[0]][customertag[1]]
                    except:
                        tagtxt = tagtxt + FieldSeperator + NoValueString
            except:
                tagtxt = ""  # No Tags

            COMPUTE_CACHE[instance.display_name] = {
                                'display_name': instance.display_name,
                                'lifecycle_state': instance.lifecycle_state,
                                'instance_type': instancetypename,
                                'shape': shape,
                                'compartment_name': compartmentName,
                                'public_ips': publicips,
                                'private_ips': privateips,
                                'AD': AD
            }
            COMPUTE_CACHE['last_cache_update'] = TIMESTAMP
        return COMPUTE_CACHE

    def cache_instances(self, profile_name='default'):
        if profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(profile_name)
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        self.get_connections()
        Log.info("caching compute instances...")
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
                    response = oci.pagination.list_call_get_all_results(self.COMPUTE.list_instances,compartment_id=compartmentID)
                    if len(response.data) > 0:
                        COMPUTE_CACHE = self.DisplayInstances(response.data, compartmentName, "Compute", self.OCI_REGION)
                        DATADICT = {}
                        DATA = []
                        for I in COMPUTE_CACHE:
                            if 'last_cache_update' not in I:
                                DATA.append(COMPUTE_CACHE[I])
                        if DATA:
                            DATADICT = DATA
                        DICT = {}
                        DICT[self.OCI_REGION] = COMPUTE_CACHE 
                        self.CONFIGSTORE.update_metadata(DICT, 'cached_instances', profile_name, True)
                        self.CONFIGSTORE = Config('ocitools')
                except:
                    pass

    def show_cache(self, profile_name, oci_region, type, display):
        DATA = []
        for ENTRY in self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][oci_region]:
            DATA_ENTRY = {}
            if ENTRY != 'last_cache_update':
                DATA_ENTRY['Name/ID'] = ENTRY
                for PROPERTY in self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][oci_region][ENTRY]:
                    DATA_ENTRY[PROPERTY] = self.CONFIGSTORE.PROFILES[profile_name]['metadata'][type][oci_region][ENTRY][PROPERTY]
                DATA.append(DATA_ENTRY)
        if DATA != []:
            if display is True:
                Log.info(f"{type}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")
            return DATA

    def show_all_cache(self, oci_region, profile_name):
        self.show_cache(profile_name, oci_region, 'cached_instances', display=False)
        self.show_cache(profile_name, oci_region, 'cached_public_ips', display=False)
        self.show_cache(profile_name, oci_region, 'cached_regions', display=False)

    def get_region_from_profile(self, profile_name):
        REGION = self.CONFIG.get_from_config('config', 'region', profile_name=profile_name)
        if REGION is None:
            Log.critical("Please run goat oci iam authenticate for the target profile before using the oss module")
        return REGION
