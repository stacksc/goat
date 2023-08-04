import sys, os, re
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getOtherCreds
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import getpass, datetime, os, subprocess, json, base64, requests

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
CONFIG = Config('jfrogtools')

class Client:

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
                USERNAME, PASSWORD = getOtherCreds(title='Artifactory')
                if PASSWORD != '':
                    break
                else:
                    Log.warn("username/password cannot be empty. Please try again")
        if CURRENT_SETUP is not None:
            if 'access_token' in CURRENT_SETUP and not overwrite:
                Log.warn("Detected existing config for target artifactory")
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
        ACCESS_TOKEN = self.generate_access_token(PASSWORD, USERNAME, user_profile)
        self.update_config(new_data={
                    'access_token': ACCESS_TOKEN
                }, profile_name=user_profile)
        return True

    def _get_prereq(self, user_profile='default'):
        CONFIG = Config('jfrogtools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_config(self, user_profile='default'):
        CONFIG = Config('jfrogtools')
        ARTIFACTS_CONFIG = CONFIG.display_profile(user_profile)
        return ARTIFACTS_CONFIG

    def get_config(self, user_profile='default'):
        CONFIG = Config('jfrogtools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        ARTIFACTS_CONFIG = PROFILE['config']
        return ARTIFACTS_CONFIG

    def get_password(self, user_profile='default'):
        return self.get_property('password', user_profile)

    def get_username(self, user_profile='default'):
        return self.get_property('username', user_profile)

    def get_property(self, property_name, user_profile='default'):
        CONFIG = Config('jfrogtools')
        if not self._get_prereq(user_profile):
            return None
        ARTIFACTS_CONFIG = self.get_config(user_profile)
        if ARTIFACTS_CONFIG is None:
            Log.critical('please setup artifacts - auth setup - before proceeding with this option')
        return ARTIFACTS_CONFIG[property_name]

    def get_access_token_age(self, user_profile='default'):
        ACCESS_TOKEN_DATA = self.get_property('access_token', user_profile)
        CREATED_ON = ACCESS_TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def get_access_token(self, user_profile='default'):
        CONFIG = Config('jfrogtools')
        try:
            PASSWORD = self.get_password(user_profile)
            USERNAME = self.get_username(user_profile)
        except FileExistsError:
            PASSWORD = None
            USERNAME = None
        if PASSWORD is None or USERNAME is None:
            Log.warn("Failed getting access token - no password available")
            return None
        try:
            ACCESS_TOKEN_AGE = self.get_access_token_age(user_profile)
        except:
            ACCESS_TOKEN_AGE = None
        if ACCESS_TOKEN_AGE is not None:
            if ACCESS_TOKEN_AGE < self.ACCESS_TOKEN_MAX_AGE:
                return self._get_access_token(user_profile)
        Log.info("Access token expired or not found. Generating a new one")
        ACCESS_TOKEN_DATA = self.generate_access_token(PASSWORD, USERNAME, user_profile)
        self.update_config(new_data={
                    'access_token': ACCESS_TOKEN_DATA
                }, profile_name=user_profile)
        return ACCESS_TOKEN_DATA['token']

    def _get_access_token(self, user_profile='default'):
        REFRESH_TOKEN_DATA = self.get_property('access_token', user_profile)
        return REFRESH_TOKEN_DATA['token']

    def generate_access_token(self, PASSWORD, USERNAME, user_profile):
        api_url = self.get_api_url(user_profile)
        basicauth = base64.b64encode(bytes(USERNAME+ ':' + PASSWORD, 'utf-8'))
        basicauth = basicauth.decode('utf-8')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + str(basicauth)
        }
        RESPONSE = requests.get(
            api_url,
            headers=headers,
            verify=False)

        if RESPONSE.status_code != 200:
            Log.critical("Failed to retrieve new access token from Nexus - API call failed: " + RESPONSE.text)

        ACCESS_TOKEN = str(basicauth)
        ACCESS_TOKEN_TIMESTAMP = datetime.datetime.now().timestamp()
        ACCESS_TOKEN_DATA = {
             'token': ACCESS_TOKEN,
             'timestamp': ACCESS_TOKEN_TIMESTAMP
        }
        return ACCESS_TOKEN_DATA

    def get_api_url(self, user_profile='default', nexus_url=None):
        CONFIG = Config('jfrogtools')
        url = CONFIG.get_metadata('ARTIFACTORY_URL', user_profile)
        if url is None:
            url = CONFIG.get_metadata(user_profile, 'ARTIFACTORY_URL')
            if url is None:
                try:
                    url = os.environ['ARTIFACTORY_URL']
                except KeyError:
                    url = None
                if url is None:
                    url = getpass.getpass("Please provide full URL to Artifactory: ")
        CONFIG.update_metadata(url, 'ARTIFACTORY_URL', user_profile)
        return url

    def update_config(self, new_data, profile_name):
        CONFIG = Config('jfrogtools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            ARTIFACTS_CONFIG = PROFILE['config']
        except KeyError: 
            PROFILE['config'] = {}
            ARTIFACTS_CONFIG = PROFILE['config']
        ARTIFACTS_CONFIG.update(new_data)
        PROFILE['config'] = ARTIFACTS_CONFIG
        CONFIG.update_profile(PROFILE)
        
    def get_access_details(self, user_profile):
        ACCESS_TOKEN = self.get_access_token(user_profile=user_profile)
        URL = self.get_api_url(user_profile)
        return ACCESS_TOKEN, URL

    def list_all_repos(self, pattern, user_profile='default'):
        ACCESS_TOKEN, JFROG_URL = self.get_access_details(user_profile)
        URL = JFROG_URL + '/api/repositories'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of repositories from jfrog: " + RESP)
        for I in RESP:
            if pattern is not None and pattern in I['key']:
                DATA.append(I)
            elif pattern is None:
                DATA.append(I)
            elif pattern is not None and pattern not in I['key']:
                continue
        return DATA

    def list_repo_details(self, repo, user_profile='default'):
        ACCESS_TOKEN, JFROG_URL = self.get_access_details(user_profile)
        URL = JFROG_URL + f'/api/repositories/{repo}'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if not RESP:
            Log.critical("failed to get a list of repositories from jfrog: " + RESP)
        return RESP

    def list_artifacts(self, name, user_profile='default'):
        ACCESS_TOKEN, JFROG_URL = self.get_access_details(user_profile)
        URL = JFROG_URL + f'/artifactory/{name}'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if not RESP:
            Log.critical("failed to get a list of artifacts from jfrog: " + RESP)
        DATA = []
        PATTERNS = ['Index', 'Name', 'Artifactory', '..']
        for LINE in RESP.text.split("\n"):
            LINE = re.sub("<.*?>"," ",LINE)
            LINE = ' '.join(LINE.split())
            if LINE:
                B = LINE.split(" ")[0]
                if B not in PATTERNS and 'Artifactory' not in B:
                    DATA.append(B)
        return DATA
