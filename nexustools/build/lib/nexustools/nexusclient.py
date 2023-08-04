import sys, os
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getNexusCreds
import getpass, datetime, os, subprocess, json, base64, requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

CONFIG = Config('nexustools')

def env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=False):
    source = '%s source %s' % ("set -a && " if include_unexported_variables else "", file_to_source_path)
    dump = '/usr/bin/python -c "import os, json; print json.dumps(dict(os.environ))"'
    pipe = subprocess.Popen(['/bin/bash', '-c', '%s && %s' % (source, dump)], stdout=subprocess.PIPE)
    return json.loads(pipe.stdout.read())

class NexusClient:

    def __init__(self):

        os.environ = env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=True)
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
                USERNAME, PASSWORD = getNexusCreds()
                if PASSWORD != '':
                    break
                else:
                    Log.warn("username/password cannot be empty. Please try again")

        if CURRENT_SETUP is not None:
            if 'access_token' in CURRENT_SETUP and not overwrite:
                Log.warn("Detected existing config for target organization")
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
        CONFIG = Config('nexustools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_nexus_config(self, user_profile='default'):
        CONFIG = Config('nexustools')
        NEXUS_CONFIG = CONFIG.display_profile(user_profile)
        return NEXUS_CONFIG

    def display_config(self, user_profile='default'):
        return self.get_config(user_profile) # OBSOLETE

    def get_config(self, user_profile='default'):
        CONFIG = Config('nexustools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        NEXUS_CONFIG = PROFILE['config']
        return NEXUS_CONFIG

    def get_nexus_password(self, user_profile='default'):
        return self.get_nexus_property('password', user_profile)

    def get_nexus_username(self, user_profile='default'):
        return self.get_nexus_property('username', user_profile)

    def get_nexus_property(self, property_name, user_profile='default'):
        CONFIG = Config('nexustools')
        if not self._get_prereq(user_profile):
            return None
        NEXUS_CONFIG = self.get_config(user_profile)
        if NEXUS_CONFIG is None:
            Log.critical('please setup nexus - auth setup - before proceeding with this option')
        return NEXUS_CONFIG[property_name]

    def get_access_token_age(self, user_profile='default'):
        ACCESS_TOKEN_DATA = self.get_nexus_property('access_token', user_profile)
        CREATED_ON = ACCESS_TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def get_access_token(self, user_profile='default'):
        CONFIG = Config('nexustools')
        try:
            PASSWORD = self.get_nexus_password(user_profile)
            USERNAME = self.get_nexus_username(user_profile)
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
        REFRESH_TOKEN_DATA = self.get_nexus_property('access_token', user_profile)
        return REFRESH_TOKEN_DATA['token']

    def generate_access_token(self, PASSWORD, USERNAME, user_profile):
        nexus_api_url = self.get_nexus_api_url(user_profile)
        basicauth = base64.b64encode(bytes(USERNAME+ ':' + PASSWORD, 'utf-8'))
        basicauth = basicauth.decode('utf-8')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + str(basicauth)
        }
        RESPONSE = requests.get(
            nexus_api_url,
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

    def get_nexus_api_url(self, user_profile='default', nexus_url=None):
        CONFIG = Config('nexustools')
        nexus_url = CONFIG.get_metadata('NEXUS_URL', user_profile)
        if nexus_url is None:
            nexus_url = CONFIG.get_metadata(user_profile, 'NEXUS_URL')
            if nexus_url is None:
                try:
                    nexus_url = os.environ['NEXUS_URL']
                except KeyError:
                    nexus_url = None
                if nexus_url is None:
                    nexus_url = getpass.getpass("Please provide full URL to NEXUS: ")
        CONFIG.update_metadata(nexus_url, 'NEXUS_URL', user_profile)
        return nexus_url

    def list_all_repos(self, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + '/service/rest/v1/repositories'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if not RESP:
            Log.critical("failed to get a list of services from nexus: " + RESP)
        return RESP

    def list_vmc_services(self, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + '/service/rest/repository/browse/docker-internal-prd/v2/vmc'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of services from nexus: " + RESP.text)
        for I in RESP.text.split('\n'):
            if '<td><a href=' in I and 'Parent Directory' not in I:
                DATA.append('vmc/'+(I.split('>')[2]).replace('</a',''))
        return DATA

    def list_atlas_services(self, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + '/service/rest/repository/browse/docker-internal-prd/v2/atlas'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of services from nexus: " + RESP.text)
        for I in RESP.text.split('\n'):
            if '<td><a href=' in I and 'Parent Directory' not in I:
                DATA.append('atlas/'+(I.split('>')[2]).replace('</a',''))
        return DATA

    def list_all_services(self, user_profile, raw=False):
        CONFIG = Config('nexustools')
        CACHE = CONFIG.get_metadata('components', user_profile)
        if CACHE:
            return CACHE
        CHK = CONFIG.get_metadata()
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + '/service/rest/repository/browse/docker-internal-prd/v2'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []

        if not RESP:
            Log.critical("failed to get a list of services from nexus: " + RESP.text)
        for I in RESP.text.split('\n'):
            if '<td><a href=' in I:
                NAME = I.split('>')[2].replace('</a','')
                MYURL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{NAME}/manifests'
                CHK = curl.get(MYURL, headers=headers)
                if CHK.status_code == 200:
                    DATA.append(NAME)
                    continue
                else:
                    MYURL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{NAME}/'
                    CHK = curl.get(MYURL, headers=headers)
                    for M in CHK.text.split('\n'):
                        if '<td><a href=' in M and 'blobs' not in M: 
                            NEWNAME = M.split('>')[2].replace('</a','')
                            MYURL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{NAME}/{NEWNAME}/manifests'
                            CHK = curl.get(MYURL, headers=headers)
                            if CHK.status_code == 200:
                                DATA.append(NAME + "/" + NEWNAME)
                                continue
                            else:
                                MYURL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{NAME}/{NEWNAME}/'
                                CHK = curl.get(MYURL, headers=headers)
                                for M in CHK.text.split('\n'):
                                    if '<td><a href=' in M and 'blobs' not in M: 
                                        MYNAME = M.split('>')[2].replace('</a','')
                                        MYURL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{NAME}/{NEWNAME}/{MYNAME}/manifests'
                                        CHK = curl.get(MYURL, headers=headers)
                                        if CHK.status_code == 200:
                                            DATA.append(NAME + "/" + NEWNAME + "/" + MYNAME)
                                            continue

        VMCDATA = self.list_vmc_services(raw=False)
        ATLASDATA = self.list_atlas_services(raw=False)
        CONFIG.update_metadata(DATA, 'components', user_profile)
        return DATA + VMCDATA + ATLASDATA
   
    def list_repo(self, name, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL_V2 = NEXUS_URL + f'/service/rest/repository/browse/{name}/v2/'
        URL_V1 = NEXUS_URL + f'/service/rest/repository/browse/{name}/'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL_V2, headers=headers)
        if RESP.status_code != 200:
            RESP = curl.get(URL_V1, headers=headers)
            if RESP.status_code != 200:
                return None
        DATA = []
        for I in RESP.text.split('\n'):
            if '<td><a href=' in I and 'Parent Directory' not in I:
                DATA.append((I.split('>')[2]).replace('</a',''))
        if 'docker' in name:
            URL = NEXUS_URL + f'/service/rest/v1/repositories/docker/hosted/{name}'
            RESP = curl.get(URL, headers=headers)
            if RESP:
                DATA.append(RESP)
        return DATA

    def list_all_users(self, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + f'/service/rest/v1/security/users/'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        RESP = curl.get(URL, headers=headers)
        return RESP

    def list_user(self, name, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + f'/service/rest/v1/security/users?userId={name}'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        RESP = curl.get(URL, headers=headers)
        return RESP

    def list_all_manifests(self, service, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{service}/manifests'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of manifests from nexus: " + RESP.text)
        for I in RESP.text.split('\n'):
            if '<td><a href=' in I and 'Parent Directory' not in I:
                DATA.append((I.split('>')[2]).replace('</a',''))
        DATA.sort()
        return DATA

    def list_manifest_details(self, service, manifest, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + f'/repository/docker-internal-prd/v2/{service}/manifests/{manifest}'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of tags from nexus: " + RESP)

        if not raw:
            try:
                REDUCTION = { 'schemaVersion': None, 'mediaType': None, 'config': None }
                RESP = reduce_json(RESP, REDUCTION)
            except:
                return None
        return RESP

    def list_tag_details(self, service, tag, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + f'/repository/docker-internal-prd/v2/{service}/manifests/{tag}'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of tags from nexus: " + RESP)

        if not raw:
            try:
                REDUCTION = { 'schemaVersion': None, 'name': None, 'tag': None, 'architecture': None }
                RESP = reduce_json(RESP, REDUCTION)
            except:
                return None
        return RESP

    def list_all_tags(self, service, raw=False):
        ACCESS_TOKEN, NEXUS_URL = self.get_access_details(user_profile='default')
        URL = NEXUS_URL + f'/service/rest/repository/browse/docker-internal-prd/v2/{service}/tags'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        DATA = []
        if not RESP:
            Log.critical("failed to get a list of tags from nexus: " + RESP.text)
        for I in RESP.text.split('\n'):
            if '<td><a href=' in I and 'Parent Directory' not in I:
                DATA.append((I.split('>')[2]).replace('</a',''))
        DATA.sort()
        return DATA

    def update_config(self, new_data, profile_name):
        CONFIG = Config('nexustools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            NEXUS_CONFIG = PROFILE['config']
        except KeyError: # org_id wasn't present in configstore
            PROFILE['config'] = {}
            NEXUS_CONFIG = PROFILE['config']
        NEXUS_CONFIG.update(new_data)
        PROFILE['config'] = NEXUS_CONFIG
        CONFIG.update_profile(PROFILE)
        
    def get_access_details(self, user_profile):
        ACCESS_TOKEN = self.get_access_token(user_profile=user_profile)
        NEXUS_URL = self.get_nexus_api_url(user_profile)
        return ACCESS_TOKEN, NEXUS_URL

