import configparser
import os

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
