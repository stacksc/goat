#!/usr/bin/env python3

import os, sys, oci, csv, json
base = '/opt/native/gen2cli'

if len(sys.argv) != 3:
    print("INFO: all parameters are required to run this tool:")
    print("- 1st param = tenantOcid")
    print("- 2nd param = region")
    sys.exit()

# init the items we need
tenantOcid = sys.argv[1]
region_name = sys.argv[2]

storage = []

# capture all regions
osfields = ('namespaceName','bucketName','compartmentName','compartmentOcid')
config = oci.config.from_file(profile_name='default')
id_client = oci.identity.IdentityClient(config)
tenantName = id_client.get_tenancy(tenancy_id=tenantOcid).data.name
os_client = oci.object_storage.ObjectStorageClient(config)
filename = base + "/logs/%s_all_compartments_%s.csv" %(tenantOcid, region_name)
osfilename = base + "/logs/%s_all_storage_%s.csv" %(tenantOcid, region_name)

print("INFO: refreshing storage buckets for region: " + region_name)
with open(osfilename, 'w', newline='', encoding='utf-8') as oscsvfile:
    compartments = id_client.list_compartments(tenantOcid, compartment_id_in_subtree=True).data
    root_compartment = id_client.get_compartment(compartment_id=tenantOcid).data
    compartments.append(root_compartment)

    oswriter = csv.writer(oscsvfile, lineterminator='\n')
    oswriter.writerow(osfields)

    for compartment in compartments:
        try:
            namespace = os_client.get_namespace(compartment_id=compartment.id).data
            buckets = os_client.list_buckets(compartment_id=compartment.id, namespace_name=namespace).data
            comp_name = str(compartment.name)
            comp_ocid = str(compartment.id)
            if len(buckets) > 0:
                print("INFO: compartment name: " + comp_name + " holds object storage buckets in region " + region_name)
                for bucket in buckets:
                    if bucket:
                        bucketname = str(bucket.name)
                        oscsvfile.write("{},{},{},{}\n".format(namespace, bucketname, comp_name, comp_ocid))
        except oci.exceptions.ServiceError as e:
            buckets = ''
            pass

f = open(osfilename, 'r')

f = open(osfilename, 'r')
reader = csv.DictReader(f)
for each in reader:
    row = {}
    for field in osfields:
        row[field] = each[field]
        if row not in storage:
            storage.append(row)

if len(storage) > 0:
    home = os.getenv("HOME")
    fname = home + '/.gen2/storage/' + tenantName + '/' + region_name + '.json'
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with open(fname, "w") as outfile:
        json.dump(storage, outfile, indent=2, sort_keys=True)
