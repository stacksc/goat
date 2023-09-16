import configparser
import os
import shutil

def get_aws_account(profile_name='default'):
    import boto3
    session = boto3.Session(profile_name=profile_name)
    client = session.client('sts')
    response = client.get_caller_identity()
    return response['Account']

def get_aws_user(profile_name='default'):
    import boto3
    user = None
    try:
        session = boto3.Session(profile_name=profile_name)
        client = session.client('iam')
        user = client.get_user()
        return user['User']['UserName']
    except:
        pass
    return user

def get_oci_tenant(profile_name='DEFAULT'):
    import oci
    oci_config = oci.config.from_file("~/.oci/config", profile_name)
    identity_client = oci.identity.IdentityClient(oci_config)
    tenancy_id = oci_config["tenancy"]
    tenancy = identity_client.get_tenancy(tenancy_id)
    return tenancy.data

def get_oci_user(profile_name='DEFAULT'):
    import oci
    oci_config = oci.config.from_file("~/.oci/config", profile_name)
    return oci_config["user"]

def read_oci_profiles():
    oci_config_file = os.path.expanduser("~/.oci/config")
    if not os.path.exists(oci_config_file):
        return "OCI config file not found"
    
    config = configparser.ConfigParser()
    config.read(oci_config_file)
    
    return list(config.sections())

def read_aws_profiles():
    aws_config_file = os.path.expanduser("~/.aws/credentials")
    if not os.path.exists(aws_config_file):
        return "AWS config file not found"
    
    config = configparser.ConfigParser()
    config.read(aws_config_file)
    
    return list(config.sections())

# Example usage
def read_cloud_profiles():
    aws_profiles = read_aws_profiles()
    oci_profiles = read_oci_profiles()

    return {
        "AWS": aws_profiles,
        "OCI": oci_profiles
    }
    import subprocess

def is_command_available(command):
    return shutil.which(command) is not None
