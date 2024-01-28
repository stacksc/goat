import time
import sys, os
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox.getpass import getCreds
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getOtherCreds, get_azure_url, get_azure_org
import getpass, datetime, os, subprocess, json, base64, requests
from datetime import timedelta
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
CONFIG = Config('azdev')

class AzDevClient:

    def __init__(self):

        self.ACCESS_TOKEN_MAX_AGE = 29*60 # max access token age; in seconds

    def setup_access(self, user_profile='default', username=None, password=None, overwrite=False):
        if user_profile not in CONFIG.PROFILES:
            CONFIG.create_profile(user_profile)

        CURRENT_SETUP = CONFIG.get_config(user_profile)
        if password is not None and username is not None:
            PASSWORD = password
            USERNAME = username
        else:
            while True:
                USERNAME, PASSWORD = getOtherCreds('azdev')
                if PASSWORD != '':
                    break
                else:
                    Log.warn("username/password cannot be empty. Please try again")

        if CURRENT_SETUP is not None:
            if 'access_token' in CURRENT_SETUP and not overwrite:
                Log.warn("Detected existing config for target profile")
                while True:
                    CHOICE = input("Overwrite existing config? (Y/N): ")
                    if CHOICE == 'y' or CHOICE == 'Y' or CHOICE == 'n' or CHOICE == 'N':
                        break
                if CHOICE == 'n' or CHOICE == 'N':
                    return False   
            else:
                self.update_config(new_data={
                    'password': PASSWORD
                }, profile_name=user_profile)
        else:
            self.update_config(new_data={
                    'username': USERNAME,
                    'password': PASSWORD
                }, profile_name=user_profile)
        return True

    def _get_prereq(self, user_profile='default'):
        CONFIG = Config('azdev')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_azdev_config(self, user_profile='default'):
        CONFIG = Config('azdev')
        AZ_CONFIG = CONFIG.display_profile(user_profile)
        return AZ_CONFIG

    def display_config(self, user_profile='default'):
        return self.get_config(user_profile) # OBSOLETE

    def get_config(self, user_profile='default'):
        CONFIG = Config('azdev')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        AZ_CONFIG = PROFILE['config']
        return AZ_CONFIG

    def get_azdev_password(self, user_profile='default'):
        return self.get_azdev_property('pass', user_profile)

    def get_azdev_username(self, user_profile='default'):
        return self.get_azdev_property('user', user_profile)

    def get_azdev_property(self, property_name, user_profile='default'):
        CONFIG = Config('azdev')
        if not self._get_prereq(user_profile):
            return None
        AZ_CONFIG = self.get_config(user_profile)
        if AZ_CONFIG is None:
            Log.critical('please setup azure-devops - auth setup - before proceeding with this option')
        return AZ_CONFIG[property_name]

    def get_azdev_api_url(self, user_profile='default', azdev_url=None):
        CONFIG = Config('azdev')
        az_url = CONFIG.get_metadata('url', user_profile)
        if az_url is None:
            az_url = get_azure_url('azure-devops')
        CONFIG.update_metadata(az_url, 'URL', user_profile)
        return az_url

    def update_config(self, new_data, profile_name):
        CONFIG = Config('azdev')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            AZ_CONFIG = PROFILE['config']
        except KeyError: # org_id wasn't present in configstore
            PROFILE['config'] = {}
            AZ_CONFIG = PROFILE['config']
        AZ_CONFIG.update(new_data)
        PROFILE['config'] = AZ_CONFIG
        CONFIG.update_profile(PROFILE)
        
    def get_azdev_creds(self, user_profile='default'):
        USERNAME = self.get_azdev_username(user_profile=user_profile)
        PASSWORD = self.get_azdev_password(user_profile=user_profile)
        AZ_URL = self.get_azdev_api_url(user_profile)
        return USERNAME, PASSWORD, AZ_URL

    def set_default_url(self, profile, current):
        CONFIG = Config('azdev')
        for PROFILE in CONFIG.PROFILES:
            if profile == PROFILE:
                CONFIG.update_config('Y', 'default', PROFILE)
                try:
                    VAL = CONFIG.get_config('default', PROFILE)
                    URL = CONFIG.get_config('url', PROFILE)
                    if VAL == 'Y':
                        Log.info(f'{profile} has been updated to default')
                        CONFIG.update_config('N', 'default', current)
                    else:
                        Log.critical(f'{profile} was not updated to default due to an error in configstore')
                except:
                    Log.critical(f'{profile} was not updated to default due to an error in configstore')

    def get_default_profile(self):
        CONFIG = Config('azdev')
        PROFILE = 'default'
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y' or VAL == 'y':
                return PROFILE
        return PROFILE
    
    def get_default_url(self):
        CONFIG = Config('azdev')
        URL = 'default'
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y' or VAL == 'y':
                URL = CONFIG.get_config('url', PROFILE)
                return URL
        return URL

    def check_for_registered_default(self):
        CONFIG = Config('azdev')
        for PROFILE in CONFIG.PROFILES:
            VAL = CONFIG.get_config('default', PROFILE)
            if VAL == 'Y':
                return True
        return False

    def get_session(self, url=None, profile_name='default'):
        CONFIG = Config('azdev')
        auth_mode = 'pass'  # default to pass, it really is a PAT though
        PROFILE = CONFIG.get_profile(profile_name)
        
        if PROFILE is None or PROFILE['config'] == {}:
            Log.debug(f"Profile '{profile_name}' not found; creating a new profile")
            while auth_mode != 'pass':
                auth_mode = 'pass'
            
            if self.check_for_registered_default() is False:
                DEFAULT_PROFILE = input('\nIs this going to be your default profile (Y/N)? : ')
            else:
                DEFAULT_PROFILE = 'N'

            url = get_azure_url('azure-devops')
            org = get_azure_org('azure-org')
            url = url + '/' + org

            CONFIG.create_profile(profile_name)
            CONFIG.update_config(auth_mode, 'mode', profile_name=profile_name)
            CONFIG.update_config(url, 'url', profile_name=profile_name)
            CONFIG.update_config(DEFAULT_PROFILE, 'default', profile_name=profile_name)
            
            if auth_mode == "pass":
                return self.setup_pass_auth(url, profile_name)
        else:
            try:
                URL = CONFIG.get_config('url', profile_name=profile_name)
                MODE = CONFIG.get_config('mode', profile_name=profile_name)
                
                if MODE == 'pass':
                    USER = CONFIG.get_config('user', profile_name=profile_name)
                    PASS = CONFIG.get_config('pass', profile_name=profile_name)
                    return self.get_session_pass_auth(URL, USER, PASS)
                else:
                    Log.critical("something went wrong")
            except:
                Log.warn(f"Profile {profile_name} might be corrupted. Would you like to delete it?")
                CHOICE = ""
                while CHOICE != "Y" and CHOICE != "y" and CHOICE != "N" and CHOICE != "n":
                    CHOICE = input("Delete profile? (Y/N): ")
                
                if CHOICE == "Y" or CHOICE == "y":
                    CONFIG.clear_profile(profile_name)
                    Log.info(f"Profile {profile_name} has been deleted. Please try again.")
                    sys.exit()
                else:
                    Log.warn(f"Profile {profile_name} not deleted. Please verify it manually and try again")
    
    def setup_pass_auth(self, url, profile_name):
        while True:
            user, mypass = getCreds()
            if user != '' and mypass != '':
                break
        if url is None:
            try:
                url = CONFIG.get_config('url', profile_name=profile_name)
            except:
                Log.critical(MSG)
        SESSION = self.get_session_pass_auth(url, user, mypass)
        CONFIG.update_config(user, 'user', profile_name=profile_name)
        CONFIG.update_config(mypass, 'pass', profile_name=profile_name)
        self.cache_facts(SESSION, profile_name)
        return SESSION

    def get_projects(self, core_client):
        PROJECTS = []
        try:
            get_projects_response = core_client.get_projects()
            index = 0
            while get_projects_response:
                for project in get_projects_response:
                    PROJECTS.append(project.name)
                # Check if there's a continuation token for pagination
                continuation_token = getattr(get_projects_response, 'continuation_token', None)
                if continuation_token:
                    get_projects_response = core_client.get_projects(continuation_token=continuation_token)
                else:
                    get_projects_response = None
        except Exception as e:
            print(f"Error retrieving projects: {e}")
            return None
        return PROJECTS
    
    def cache_facts(self, session, profile_name):
        CONFIG = Config('azdev')
        Log.info("Caching some system info now to save time later... please wait")
        PROJECT_KEYS = {}
        PROJECTS = self.get_projects(session)
        for PROJECT in PROJECTS:
            PROJECT_KEYS[PROJECT] = {}
        CONFIG.update_metadata(PROJECT_KEYS, 'projects', profile_name)
        Log.info("Caching facts complete")
    
    def get_session_pass_auth(self, url, user, token):
        try:
            CREDENTIALS = BasicAuthentication('', token)
            SESSION = Connection(base_url=url, creds=CREDENTIALS)
            CLIENT = SESSION.clients.get_core_client()
        except Exception as e:
            print(f"Error establishing connection: {e}")
            return None
        return CLIENT
    
    def get_user_creds(self, user_profile):
        CONFIG = Config('azdev')
        AUTH_MODE = CONFIG.get_config('mode', user_profile)
        if AUTH_MODE == 'pass':
            USERNAME = CONFIG.get_config('user', user_profile)
            PASSWORD = CONFIG.get_config('pass', user_profile)
            return [USERNAME, PASSWORD]
    
    def get_url(self, userprofile):
        CONFIG = Config('azdev')
        return CONFIG.get_config('url', userprofile)

    def get_access_token(self, user_profile='default'):
        TOKEN_DATA = self.get_property('pass', user_profile)
        return TOKEN_DATA

    def get_property(self, property_name, user_profile='default'):
        CONFIG = Config('azdev')
        AZ_CONFIG = CONFIG.get_config(property_name, user_profile)
        if AZ_CONFIG is None:
            Log.critical('please setup azdev - auth setup - before proceeding with this option')
        return AZ_CONFIG
    
    def get_access_token_age(self, user_profile='default'):
        CREATED_ON = float(CONFIG.get_metadata('created_at', user_profile))
        TIME_NOW = float(datetime.datetime.now().timestamp())
        RESULT = TIME_NOW - CREATED_ON
        RESULT = round(RESULT / 60.0, 2) # convert to minutes
        return RESULT

    def get_credentials(self, profile):
        creds = self.get_user_creds(profile)
        token = creds[1]
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        credentials = ('', token)
        return headers, credentials

    def update_latest_profile(self, profile_name):
        BASICS = Config('azdev')
        LATEST = BASICS.get_profile('latest')
        if LATEST is None:
            BASICS.create_profile('latest')
            BASICS.update_config(profile_name, 'role', 'latest')
        else:
            BASICS.update_config(profile_name, 'role', 'latest')
