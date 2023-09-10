#!/usr/bin/env python3

# script compiled from oci oracle examples

import oci
import sys
import os.path
from hashlib import md5
from codecs import decode
from time import sleep

if len(sys.argv) != 3:
    print("INFO: all parameters are required to run this tool:")
    print("- 1st param = public key location")
    print("- 2nd param = region")
    sys.exit()

public_key_path = sys.argv[1]
region = sys.argv[2]

config = oci.config.from_file(profile_name='default')

def generate_signer_from_config(config):
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file")
    )

    return signer

signer = generate_signer_from_config(config)
identity = oci.identity.IdentityClient(config, signer=signer)
compute_client = oci.core.ComputeClient(config, signer=signer)
virtual_network_client = oci.core.VirtualNetworkClient(config, signer=signer)

def get_fingerprint(key):

    # There should be more error checking here, but to keep the example simple
    # the error checking has been omitted.
    m = md5()

    # Strip out the parts of the key that are not used in the fingerprint
    # computation.
    key = key.replace(b'-----BEGIN PUBLIC KEY-----\n', b'')
    key = key.replace(b'\n-----END PUBLIC KEY-----', b'')

    # The key is base64 encoded and needs to be decoded before getting the md5
    # hash
    decoded_key = decode(key, "base64")
    m.update(decoded_key)
    hash = m.hexdigest()

    # Break the hash into 2 character parts.
    length = 2
    parts = list(hash[0 + i:length + i] for i in range(0, len(hash), length))

    # Join the parts with a colon seperator
    fingerprint = ":".join(parts)
    return fingerprint

def is_key_already_uploaded(keys, fingerprint):
    for key in keys:
        if key.fingerprint == fingerprint:
            return True
    return False

# Check there are enough arguments
if len(sys.argv) != 3:
    raise RuntimeError('INFO: this script expects an argument of a path to the public API key')

# Verify the path to the public key exists
if not os.path.exists(public_key_path):
    raise RuntimeError('INFO: this argument must be a valid path to a public API key')

# Open the key file and store the contents
with open(public_key_path, 'rb') as f:
    public_key = f.read().strip()

# Get the fingerprint for the key
fingerprint = get_fingerprint(public_key)
print("INFO: fingerprint of API key is: {}".format(fingerprint))

# Read the config file and initialize the identity client
config = oci.config.from_file(profile_name='default')

# Check to see if this key is already associated with the user.
if is_key_already_uploaded(identity.list_api_keys(config['user']).data, fingerprint):
    print("INFO: key with fingerprint {} has already been added to user".format(fingerprint))
    sys.exit()

# Initialize the CreateApiKeyDetails model
key_details = oci.identity.models.CreateApiKeyDetails(key=public_key.decode())

# Upload the key
response = identity.upload_api_key(config['user'], key_details)

# Results of uploading key
print("INFO: results of uploading key:")
print()
print(response.data)
print()

while True:
    if is_key_already_uploaded(identity.list_api_keys(config['user']).data, fingerprint):
        print("INFO: sucessfully uploaded API key {}".format(public_key_path))
        break
    sleep(2)
