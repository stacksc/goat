from os import environ, unsetenv, mkdir, path
from pathlib import Path
from configparser import ConfigParser
from toolbox.logger import Log
from toolbox.getpass import get_secure_string

class AWSconfig():
    def __init__(self, aws_dir=f"{environ['HOME']}/.aws/", aws_config="config", aws_credentials="credentials"):
        self.AWS_DIR = aws_dir
        self.AWS_CONFIG_FILE = self.verify_path(f"{aws_dir}{aws_config}")
        self.AWS_CREDS_FILE = self.verify_path(f"{aws_dir}{aws_credentials}")

    def profile_or_role(self, profile_name):
        ROLE_ARN = self.get_from_config('creds', 'role_arn', 'string', "", profile_name)
        if ROLE_ARN == "" or ROLE_ARN is None:
            return True # no role_arn so the profile must be for the main account
        else:
            return False # role_arn fonud so the profile must be for a role

    def add_aws_profile(self, aws_access_key_id, aws_secret_access_key, aws_region, aws_output, profile_name):
        self.update_aws_config('creds', profile_name, 'aws_access_key_id', aws_access_key_id)
        self.update_aws_config('creds', profile_name, 'aws_secret_access_key', aws_secret_access_key)
        self.update_aws_config('config', profile_name, 'region', aws_region)
        self.update_aws_config('config', profile_name, 'output', aws_output)

    def add_aws_profile_saml(self, aws_access_key_id, aws_secret_access_key, aws_session_token, aws_region, aws_output, profile_name):
        self.update_aws_config('creds', profile_name, 'aws_access_key_id', aws_access_key_id)
        self.update_aws_config('creds', profile_name, 'aws_secret_access_key', aws_secret_access_key)
        self.update_aws_config('creds', profile_name, 'aws_session_token', aws_session_token)
        self.update_aws_config('config', profile_name, 'region', aws_region)
        self.update_aws_config('config', profile_name, 'output', aws_output)

    def config_add_role(self, profile_name, role_arn, creds_profile):
        self.update_aws_config('config', profile_name, 'role_arn', role_arn)
        self.update_aws_config('config', profile_name, 'source_profile', creds_profile)
    
    def add_sim_config(self, sim_region, token, iam_profile, profile_name):
        self.update_aws_config('config', profile_name, 'region', sim_region)
        self.update_aws_config('creds', profile_name, 'aws_session_token', token)
        self.update_aws_config('creds', profile_name, 'source_profile', iam_profile)

    def update_aws_config(self, config_type, profile_name, property_name, property_value):
        CONFIG, CONFIG_FILE = self.choose_configparser(config_type)
        if config_type == "config":
            profile_name = "profile " + profile_name
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
        if config_type == "creds":
            CONFIG_FILE = self.AWS_CREDS_FILE
        elif config_type == "config":
            CONFIG_FILE = self.AWS_CONFIG_FILE
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
                Log.critical("failed to create .aws directory")

    def unset_aws_profile(self, *args):
        if args is None:
            if 'AWS_ACCESS_KEY_ID' in os.environ:
                del environ['AWS_ACCESS_KEY_ID']
            if 'AWS_SECRET_ACCESS_KEY' in os.environ:
                del environ['AWS_SECRET_ACCESS_KEY']
            if 'AWS_DEFAULT_REGION' in os.environ:
                del environ['AWS_DEFAULT_REGION']
            if 'AWS_SESSION_TOKEN' in os.environ:
                del environ['AWS_SESSION_TOKEN']
            if 'AWS_OUTPUT' in os.environ:
                del environ['AWS_OUTPUT']
            if 'AWS_ROLE_ARN' in os.environ:
                del environ['AWS_ROLE_ARN']
            if 'AWS_SOURCE' in os.environ:
                del environ['AWS_SOURCE']
        else:
            for arg in args:
                unsetenv(arg)
        try:
            del environ['AWS_ACCESS_KEY_ID']
            del environ['AWS_SECRET_ACCESS_KEY']
            del environ['AWS_SESSION_TOKEN']
        except:
            pass

    def set_aws_profile(self, aws_session_token, aws_region, aws_output):
        environ['AWS_SESSION_TOKEN'] = aws_session_token
        environ['AWS_DEFAULT_REGION'] = aws_region
        environ['AWS_OUTPUT'] = aws_output

    def set_env_variables(self, aws_access_key_id, aws_secret_access_key, aws_session_token):
        environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
        environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
        environ['AWS_SESSION_TOKEN'] = aws_session_token

    def display(self, type, profile_name=None):
        AWS_CONFIG, AWS_FILE = self.choose_configparser(type)
        if profile_name is None:
            print(f'\n-------------------- aws {type} for all profiles --------------------')
            for PROFILE in AWS_CONFIG:
                if PROFILE != 'DEFAULT': # aws uses lowercase default, remove redundant DEFAULT entry from output
                    print(f"    [{PROFILE}]")
                for PROPERTY in AWS_CONFIG[PROFILE]:
                    print(f"    {PROPERTY}={AWS_CONFIG[PROFILE][PROPERTY]}")
                print('')
            print('')
        else:
            if profile_name in AWS_CONFIG:
                print(f'\n-------------------- aws {type} for profile {profile_name} --------------------')
                print(f"    [{profile_name}]")
                for PROPERTY in AWS_CONFIG[profile_name]:
                        print(f"    {PROPERTY}={AWS_CONFIG[profile_name][PROPERTY]}")
                print('')
            else:
                return
