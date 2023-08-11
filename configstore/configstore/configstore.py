#!/usr/bin/env python3

import os, json, datetime, signal, time
from toolbox import fernet

def handler(signum, frame):
    res = input("\nCTRL-C was pressed => Do you really want to exit? (y/n): ")
    if res == 'Y' or res == 'y':
        exit(1)

signal.signal(signal.SIGINT, handler)

class Config:

    def __init__(self, name):
        self.NAME = name
        HOME = os.getenv('HOME')
        os.makedirs(f'{HOME}/goat', exist_ok=True)
        self.PATH = f'{HOME}/goat/.{name}.cfg'
        self.PROFILES = self.load_cfg_file()
        if self.PROFILES is None:
            self.PROFILES = { }
        self.reload_cfg()

    # save whatever is stored by the class to a file and encrypt it
    def save_cfg_file(self):
        with open(self.PATH, "w+") as FILE: 
            FILE.seek(0)
            ENCRYPTED_DATA = fernet.encrypt_string(self.NAME, json.dumps(self.PROFILES)) 
            FILE.write(ENCRYPTED_DATA)
        return True
    
    # decrypt the source file and load its content
    def load_cfg_file(self):
        if os.path.exists(self.PATH):
            with open(self.PATH, "r") as FILE: 
                FILE.seek(0)
                ENCRYPTED_DATA = FILE.read()
                JSON_DATA = fernet.decrypt_string(self.NAME, ENCRYPTED_DATA)
                DATA = json.loads(JSON_DATA)
                return DATA
        else:
            return None

    # re-load the source file and re-initialize the local class variable
    def reload_cfg(self):
        self.save_cfg_file()
        self.PROFILES = self.load_cfg_file()
    
    # re-load the source file while also uppdating the local class variable
    def load_cfg(self):
        self.PROFILES = self.load_cfg_file()

    # create a profile and populate it with preset data if it exists
    def create_profile(self, profile_name='default'):
        self.load_cfg()
        if 'preset' in self.PROFILES:
            PROFILE = self.PROFILES['preset']
            PROFILE['metadata'].update({
                'name': profile_name,
                'created_by': os.environ['USER'],
                'created_at': str(datetime.datetime.now().timestamp())
            })
        else:
            PROFILE = {
                'config': {},
                'metadata': {
                    'name': profile_name,
                    'created_by': os.environ['USER'],
                    'created_at': str(datetime.datetime.now().timestamp())
                }
            }
        self.PROFILES[profile_name] = PROFILE
        self.reload_cfg()
        return True

    # create a preset for new profiles
    def create_preset(self, preset_data):
        self.load_cfg()
        PRESET = {
            'config': preset_data['config'],
            'metadata': {
                'name': 'preset',
                'created_by': os.environ['USER'],
                'created_at': str(datetime.datetime.now().timestamp()),
            }    
        } 
        PRESET['metadata'].update(preset_data['metadata'])
        self.PROFILES['preset'] = PRESET   
        self.reload_cfg()
        return True

    # replace the current data stored in a profile with an entirely new dict
    def update_profile(self, profile_data, overwrite=True, _preset=False):
        self.load_cfg()
        try:
            PROFILE_NAME = profile_data['metadata']['name']
            if not _preset:
                self.verify_profile(PROFILE_NAME)
                if overwrite:
                    self.PROFILES[PROFILE_NAME] = profile_data
                else:
                    self.PROFILES[PROFILE_NAME].update(profile_data)
        except KeyError:
            return False
        self.reload_cfg()
        return True

    # update the preset in configstore with an entirely new dict
    def update_preset(self, preset_data, overwrite=True): 
        self.load_cfg()
        self.update_section('config', data=preset_data['config'], overwrite=True)
        self.update_section('metadata', data=preset_data['metadata'], overwrite=True)    
        self.reload_cfg()
        return True

    # update either the entire config within a profile or a single config property
    def update_config(self, config_data, config_name=None, profile_name='default', overwrite=True):
        self.load_cfg()
        PROFILE = self.get_profile(profile_name)
        return self.update_section('config', config_data, config_name, PROFILE, overwrite)

    # update either the entire metadata within a profile or a single metadata property
    def update_metadata(self, metadata_data, metadata_name=None, profile_name='default', overwrite=True):
        self.load_cfg()
        PROFILE = self.get_profile(profile_name)
        return self.update_section('metadata', metadata_data, metadata_name, PROFILE, overwrite)

    # worker method for update_config and update_metadata
    def update_section(self, section, data, data_name, profile_data, overwrite=False):
        self.load_cfg()
        try:
            if type(data) == dict:
                if data_name is None:
                    profile_data[section] = data
                else:
                    if data_name in profile_data[section]:
                        profile_data[section][data_name].update(data)
                    else:
                        profile_data[section][data_name] = {}
                        profile_data[section][data_name] = data
            else:
                if data_name is None:
                    profile_data[section] = data
                else:
                    profile_data[section][data_name] = data
            if overwrite:
                if data_name is None:
                    profile_data[section] = data
                else:
                    profile_data[section][data_name] = data
            else:
                if data_name is None:
                    profile_data[section].update(data)
                else:
                    profile_data[section][data_name].update(data)
        except KeyError:
            return False
        self.update_profile(profile_data)
        self.reload_cfg()
        return True

    # delete the entire profile
    def clear_profile(self, profile_name='default'):
        self.load_cfg()
        try:
            del self.PROFILES[profile_name]
        except KeyError as e:
            return False
        self.reload_cfg()
        return True

    # delete the preset in configstore
    def clear_preset(self):
        self.load_cfg()
        self.PROFILES['preset'] = {}
        self.reload_cfg()
        return True

    # delete the config setion of the configstore, or individual config property
    def clear_config(self, profile_name, config_name=None):
        return self.clear_section(profile_name, config_name)

    # delete the metadata setion of the configstore, or individual metadata property
    def clear_metadata(self, profile_name, metadata_name=None):
        return self.clear_section(profile_name, metadata_name)

    # worker method for clear_config and clear_metadata
    def clear_section(self, type, profile_name='default', section_name=None):
        self.load_cfg()
        if section_name is None:
            del self.PROFILES[profile_name][type]
        else:
            del self.PROFILES[profile_name][type][section_name]
        self.reload_cfg()
        return True

    # get the entire content of a configstore profile or None if profile doesn't exist
    def get_profile(self, profile_name='default'):
        if profile_name in self.PROFILES:
            return self.PROFILES[profile_name]
        else:
            return None

    # get the content of the preset in configstore
    def get_preset(self):
        if self.PROFILES['preset'] != {}:
            return self.PROFILES['preset']
        else:
            return None

    # retrieve full config for a profile or a specific property within the config if config_name is defined
    # returns None if config or config property doesn't exist
    def get_config(self, config_name=None, profile_name='default'):
        PROFILE = self.get_profile(profile_name)
        if PROFILE is None:
            return None
        if 'config' in PROFILE:
            if config_name is None:
                return PROFILE['config']
            elif config_name in PROFILE['config']:
                return PROFILE['config'][config_name]
        else:
            return None

    # retrieve full metadata for a profile or a specific property within the metadta if metadata_name is defined
    # returns None if metadata or metadata property doesn't exist
    def get_metadata(self, metadata_name=None, profile_name='default'):
        PROFILE = self.get_profile(profile_name)
        if PROFILE is None:
            return None
        if 'metadata' in PROFILE:
            if metadata_name is None:
                return PROFILE['metadata']
            elif metadata_name in PROFILE['metadata']:
                return PROFILE['metadata'][metadata_name]
        else:
            return None

    def get_metadata_aws(self, metadata_name=None, profile_name='default', region_name='us-east-1'):
        PROFILE = self.get_profile(profile_name)
        if PROFILE is None:
            return None
        if 'metadata' in PROFILE:
            if metadata_name is None:
                return PROFILE['metadata']
            elif metadata_name in PROFILE['metadata']:
                return PROFILE['metadata'][metadata_name][region_name]
        else:
            return None

    def get_from_env(self, variable_name, prompt_msg=None, property_type='config', profile_name='default'):
        PROFILE_DATA = self.get_profile(profile_name)
        if prompt_msg is None:
            prompt_msg = f"unable to source {variable_name} from environment variables\nmanual input: "
        try:
            VARIABLE = os.environ[variable_name]
        except:
            VARIABLE = input(prompt_msg)
        self.update_section(property_type, VARIABLE, variable_name, PROFILE_DATA)
        return VARIABLE

    def get_var(self, property_name, property_type='config', env_var_name=None, profile_name='default'):
        if property_type == 'config':
            VAR = self.get_config(property_name, profile_name)
        if property_type == 'metadta':
            VAR = self.get_metadata(property_name, profile_name)
        else:
            VAR = None
        if VAR is None:
            PROFILE_DATA = self.get_profile(profile_name)
            try:
                VAR = os.environ[env_var_name] 
            except:
                VAR = input(f"please provide value for {property_name}: ")
        if VAR is not None:
            self.update_section(property_type, VAR, property_name, PROFILE_DATA)
        return VAR

    def display_configstore(self):
        PROFILES = self.PROFILES
        self.filter_print(PROFILES)
        return PROFILES

    def display_profile(self, profile_name):
        PROFILE = self.get_profile(profile_name)
        self.filter_print(PROFILE)
        return PROFILE

    def display_config(self, profile_name):
        CONFIG = self.get_profile(profile_name)['config']
        self.filter_print(CONFIG)
        return CONFIG

    def display_metadata(self, profile_name):
        METADATA = self.get_profile(profile_name)['metadata']
        self.filter_print(METADATA)
        return METADATA

    def verify_profile(self, profile_name):
        self.load_cfg()
        if profile_name not in self.PROFILES:
            self.create_profile(profile_name)
        self.reload_cfg()
        return self.refresh(self.NAME)

    def filter_print(self, data):
        data = self.filter_data(data)
        print(json.dumps(data, indent=4))

    def filter_data(self, data):
        RESTRICTED_KEYS = ['pass', 'password', 'token']
        for RESTRICTED_KEY in RESTRICTED_KEYS:
            for KEY in data:
                if type(data[KEY]) == dict:
                    data[KEY] = self.filter_data(data[KEY])
                if KEY == RESTRICTED_KEY:
                    data[KEY] = '******************'
        return data
        
    @classmethod
    def refresh(cls, name):
        return cls(name)
