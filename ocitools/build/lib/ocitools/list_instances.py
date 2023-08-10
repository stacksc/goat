#!/usr/bin/env python3
# Oracle OCI - Instance report script
# Version: 1.8 22-November 2018
# Written by: richard@oc-blog.com
# More info see: www.oc-blog.com
#
# This script will create a CSV report for all compute and DB instances (including ADW and ATP)
# in your OCI account, including predefined tags
#
# Instructions:
# - you need the OCI python API, this can be installed by running: pip install oci
# - you need the OCI CLI, this can be installed by running: pip install oci-cli
# - Make sure you have a user with an API key setup in the OCI Identity
# - Create a config file using the oci cli tool by running: oci setup config
# - In the script specify the config file to be used for running the report
# - You can specify any region in the config file, the script will query all enabled regions

import sys, os

import oci
import json
import shapes
import logging

AllPredefinedTags = True        # use only predefined tags from root compartment or include all compartment tags as well
NoValueString = "n/a"           # what value should be used when no data is available
FieldSeperator = ","            # what value should be used as field seperator
ReportFile = "/opt/native/gen2cli/logs/report.csv"
ReportJson = "/opt/native/gen2cli/logs/report.json"
EndLine = "\n"
home = ''

if len(sys.argv) != 4:
    print("INFO: all parameters are required to run this tool:")
    print("- 1st param = profile")
    print("- 2nd param = tenancy ocid")
    print("- 3rd param = compartment name")
    sys.exit()

profile = sys.argv[1]
tenantOcid = sys.argv[2]
myCompartment = sys.argv[3]
config = oci.config.from_file(profile_name=profile)

def generate_signer_from_config(config):
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file")
    )
    return signer

signer = generate_signer_from_config(config)
identity_client = oci.identity.IdentityClient(config, signer=signer)
compute_client = oci.core.ComputeClient(config, signer=signer)
virtual_network_client = oci.core.VirtualNetworkClient(config, signer=signer)
original_stdout = sys.stdout

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

def DisplayInstances(instances, compartmentName, instancetype, regionname):
  for instance in instances:
    sys.stdout = jsonfile
    print(instance)
    sys.stdout = original_stdout
    privateips = ""
    publicips = ""
    instancetypename = ""
    tagtxt = ""
    OS = ""

    if instancetype == "Compute":
      OCPU, MEM, SSD = shapes.ComputeShape(instance.shape)
      response = ComputeClient.list_vnic_attachments(compartment_id = instance.compartment_id, instance_id = instance.id)
      vnics = response.data
      try:
        for vnic in vnics:
          responsenic = NetworkClient.get_vnic(vnic_id=vnic.vnic_id)
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
        response = ComputeClient.get_image(instance.source_details.image_id)
        imagedetails = response.data
        OS = imagedetails.display_name
      except:
        OS = NoValueString

      prefix,AD = instance.availability_domain.split(":")

    # Handle details for Database Instances
    if instancetype=="DB":
      OCPU, MEM, SSD = shapes.ComputeShape(instance.shape)
      OCPU = instance.cpu_core_count # Overwrite Shape's CPU count, with DB enabled CPU count
      response = databaseClient.list_db_nodes(compartment_id = instance.compartment_id, db_system_id = instance.id)
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

      instancetypename= "DB " + instance.database_edition
      OS = "Oracle Linux 6.8"
      shape = instance.shape
      prefix,AD = instance.availability_domain.split(":")

    # Handle details for Autonomous Database (ATP)
    if instancetype == "ATP":
      OCPU = instance.cpu_core_count
      MEM = NoValueString
      SSD = instance.data_storage_size_in_tbs
      instancetypename = "ATP"
      OS = NoValueString
      shape = "ATP"
      AD = regionname.upper()
      privateips = NoValueString
      publicips = NoValueString

    # Handle details for Autonomous Database (ADW)
    if instancetype == "ADW":
      OCPU = instance.cpu_core_count
      MEM = NoValueString
      SSD = instance.data_storage_size_in_tbs
      instancetypename = "ADW"
      OS = NoValueString
      shape = "ADW"
      AD = regionname.upper()
      privateips = NoValueString
      publicips = NoValueString

    try:
      namespaces = instance.defined_tags
      for customertag in customertags:
        try:
           tagtxt = tagtxt + FieldSeperator + namespaces[customertag[0]][customertag[1]]
        except:
           tagtxt = tagtxt + FieldSeperator + NoValueString
    except:
      tagtxt = ""  # No Tags

    line =   "{}{}".format(      instance.display_name,    FieldSeperator)
    line = "{}{}{}".format(line, instance.lifecycle_state, FieldSeperator)
    line = "{}{}{}".format(line, instancetypename,         FieldSeperator)
    line = "{}{}{}".format(line, shape,                    FieldSeperator)
    line = "{}{}{}".format(line, compartmentName,          FieldSeperator)
    line = "{}{}".format(line, AD)
    report.write(line + EndLine)

sys.stdout = original_stdout
report = open(ReportFile,'w')
jsonfile = open(ReportJson,'w')
customertags = []
header = "NAME,STATE,SERVICE,SHAPE,COMPARTMENT,AD".replace(",", FieldSeperator)

identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
RootCompartmentID = tenantOcid

print ("logged in as:\t\t {} @ {}".format(user.description, config["region"]))
print ("querying region: ", end='')

response = identity.list_region_subscriptions(config["tenancy"])
regions = response.data

for region in regions:
    if region.region_name == profile:
        if region.is_home_region:
            home = "Home region"
        print ("\t {} ({}) {}".format(region.region_name, region.status, home))
report.write(header + EndLine)

ComputeClient = oci.core.ComputeClient(config)
NetworkClient = oci.core.VirtualNetworkClient(config)

# Check instances for all the underlaying Compartments
response = oci.pagination.list_call_get_all_results(identity.list_compartments,RootCompartmentID,compartment_id_in_subtree=True)
compartments = response.data

# Insert (on top) the root compartment
RootCompartment = oci.identity.models.Compartment()
RootCompartment.id = RootCompartmentID
RootCompartment.name = "root"
RootCompartment.lifecycle_state = "ACTIVE"
compartments.insert(0, RootCompartment)

for compartment in compartments:
  if myCompartment == compartment.name:
    compartmentName = compartment.name
  else:
    continue
  if compartment.lifecycle_state == "ACTIVE":
    print ("processing compartment:  " + compartmentName)
    compartmentID = compartment.id
    try:
      response = oci.pagination.list_call_get_all_results(ComputeClient.list_instances,compartment_id=compartmentID)
      if len(response.data) > 0:
        DisplayInstances(response.data, compartmentName, "Compute", region.region_name)
    except:
      pass

    databaseClient = oci.database.DatabaseClient(config)
    try:
      response = oci.pagination.list_call_get_all_results(databaseClient.list_db_systems,compartment_id=compartmentID)
      if len(response.data) > 0:
        DisplayInstances(response.data, compartmentName, "DB", region.region_name)
    except:
      pass

    try:
      response = oci.pagination.list_call_get_all_results(databaseClient.list_autonomous_data_warehouses,compartment_id=compartmentID)
      if len(response.data) > 0:
        DisplayInstances(response.data, compartmentName, "ADW", region.region_name)
    except:
      pass

    try:
      response = oci.pagination.list_call_get_all_results(databaseClient.list_autonomous_databases,compartment_id=compartmentID)
      if len(response.data) > 0:
        DisplayInstances(response.data, compartmentName, "ATP", region.region_name)
    except:
      pass

report.close()
jsonfile.close()
report = '/opt/native/gen2cli/logs/report.csv'
cmd = 'tabulate --header -s, -f rst %s' %(report)
print()
os.system(cmd)
print()
print("INFO: complete JSON output:  " + ReportJson)
print("INFO: short summary output:  " + ReportFile)
