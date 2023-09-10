import oci
from os import environ, unsetenv, mkdir, path
from pathlib import Path
from configparser import ConfigParser
from toolbox.logger import Log
from toolbox.getpass import get_secure_string

class OCIconfig():
    def __init__(self, oci_dir=f"{environ['HOME']}/.oci/", oci_config="config"):
        self.OCI_DIR = oci_dir
        self.OCI_CONFIG_FILE = self.verify_path(f"{oci_dir}{oci_config}")

    def add_oci_profile(self, tenancy, user, region, fingerprint, key_file, profile_name):
        self.update_oci_config('config', profile_name, 'region', region)
        self.update_oci_config('config', profile_name, 'tenancy', tenancy)
        self.update_oci_config('config', profile_name, 'user', user)
        self.update_oci_config('config', profile_name, 'fingerprint', fingerprint)
        self.update_oci_config('config', profile_name, 'key_file', key_file)

    def update_oci_config(self, config_type, profile_name, property_name, property_value):
        CONFIG, CONFIG_FILE = self.choose_configparser(config_type)
        try:
            CONFIG.add_section(profile_name)
        except:
            pass # this means the section already exists
        CONFIG.set(profile_name, property_name, property_value)
        with open(CONFIG_FILE, 'w') as CONFIG_FILE_STREAM:
            CONFIG.write(CONFIG_FILE_STREAM) 

    def get_from_config(self, config_type, config_property_name, alternative_method=None, alternative_method_value=None, profile_name=None, supplied_value=None):
        CONFIG, CONFIG_FILE = self.choose_configparser(config_type)
        if profile_name in CONFIG and config_property_name in CONFIG[profile_name]:
            RESULT = CONFIG[profile_name][config_property_name]
        else:
            RESULT = None
        if RESULT is None:
            if alternative_method == 'string':
                RESULT = alternative_method_value
            elif alternative_method == 'input':
                RESULT = input(alternative_method_value)
            elif alternative_method == 'secure':
                RESULT = get_secure_string(config_property_name, alternative_method_value)
            else:
                pass
        if supplied_value != None:
            if RESULT != supplied_value:
                RESULT = supplied_value
        return RESULT

    def choose_configparser(self, config_type):
        CONFIG = ConfigParser() 
        if config_type == "config":
            CONFIG_FILE = self.OCI_CONFIG_FILE
        else:
            Log.critical("invalid config type")
        CONFIG.read(CONFIG_FILE)
        return CONFIG, CONFIG_FILE

    def verify_path(self, path_to_file):
        try:
            PATH_TO_FOLDER = '/'.join(path_to_file.split('/')[:-1])
            if not path.exists(PATH_TO_FOLDER):
                mkdir(PATH_TO_FOLDER)
            Path(path_to_file).touch()
            return path_to_file
        except OSError:
            Log.critical("failed to create .oci directory")

    def display(self, type, profile_name=None):
        OCI_CONFIG, OCI_FILE = self.choose_configparser(type)
        if profile_name is None:
            print(f'\n-------------------- oci {type} for all profiles --------------------')
            for PROFILE in OCI_CONFIG:
                if PROFILE != 'DEFAULT': # oci uses uppercase default, remove redundant DEFAULT entry from output
                    print(f"    [{PROFILE}]")
                for PROPERTY in OCI_CONFIG[PROFILE]:
                    print(f"    {PROPERTY}={OCI_CONFIG[PROFILE][PROPERTY]}")
                print('')
            print('')
        else:
            if profile_name in OCI_CONFIG:
                print(f'\n-------------------- oci {type} for profile {profile_name} --------------------')
                print(f"    [{profile_name}]")
                for PROPERTY in OCI_CONFIG[profile_name]:
                        print(f"    {PROPERTY}={OCI_CONFIG[profile_name][PROPERTY]}")
                print('')
            else:
                return
