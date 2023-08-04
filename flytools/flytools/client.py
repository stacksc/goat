import sys, os, re, socketserver
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getOtherCreds, getOtherToken
import getpass, datetime, os, subprocess, json, base64, requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import concoursepy

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
CONFIG = Config('flytools')

class Client:

    def __init__(self):
        self.ACCESS_TOKEN_MAX_AGE = 86400 # max access token age; in seconds = 1 day

    def setup_access(self, user_profile='default', username=None, password=None, overwrite=False):
        if user_profile not in CONFIG.PROFILES:
            CONFIG.create_profile(user_profile)
        CURRENT_SETUP = CONFIG.get_config(user_profile)
        if password is not None and username is not None:
            PASSWORD = password
            USERNAME = username
        else:
            while True:
                USERNAME, PASSWORD = getOtherCreds(title='Concourse')
                if PASSWORD != '':
                    break
                else:
                    Log.warn("username/password cannot be empty. Please try again")
        if CURRENT_SETUP is not None:
            if 'access_token' in CURRENT_SETUP and not overwrite:
                Log.warn("Detected existing config for target concourse")
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
        CONFIG = Config('flytools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_config(self, user_profile='default'):
        CONFIG = Config('flytools')
        MY_CONFIG = CONFIG.display_profile(user_profile)
        return MY_CONFIG

    def get_config(self, user_profile='default'):
        CONFIG = Config('flytools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        MY_CONFIG = PROFILE['config']
        return MY_CONFIG

    def get_password(self, user_profile='default'):
        return self.get_property('password', user_profile)

    def get_username(self, user_profile='default'):
        return self.get_property('username', user_profile)

    def get_property(self, property_name, user_profile='default'):
        CONFIG = Config('flytools')
        if not self._get_prereq(user_profile):
            return None
        MY_CONFIG = self.get_config(user_profile)
        if MY_CONFIG is None:
            Log.critical('please setup concourse runway - auth setup - before proceeding with this option')
        return MY_CONFIG[property_name]

    def get_access_token_age(self, user_profile='default'):
        ACCESS_TOKEN_DATA = self.get_property('access_token', user_profile)
        CREATED_ON = ACCESS_TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def get_access_token(self, user_profile='default'):
        CONFIG = Config('flytools')
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
        ACCESS_TOKEN = None
        api_url = self.get_api_url(user_profile)
        with socketserver.TCPServer(("localhost", 0), None) as S:
            PORT = S.server_address[1]
            URL = api_url + f"/login?fly_port={PORT}"
        try:
            Log.info(f"Launching the following URL in your browser for the token:\n      {URL}")
            open_url(URL)
        except: 
            Log.info(f"Please login to the following URL in your browser for the token:\n      {URL}")
        ACCESS_TOKEN = getOtherToken('concourse runway')
        if ACCESS_TOKEN is None:
            Log.critical("failed to retrieve new access token from Concourse, or token cannot be empty")
        else:
            try:
                ACCESS_TOKEN = ACCESS_TOKEN.replace('bearer ','')
            except:
                pass
        ACCESS_TOKEN_TIMESTAMP = datetime.datetime.now().timestamp()
        ACCESS_TOKEN_DATA = {
             'token': ACCESS_TOKEN,
             'timestamp': ACCESS_TOKEN_TIMESTAMP
        }
        return ACCESS_TOKEN_DATA

    def get_api_url(self, user_profile='default', nexus_url=None):
        CONFIG = Config('flytools')
        url = CONFIG.get_metadata('CONCOURSE_URL', user_profile)
        if url is None:
            url = CONFIG.get_metadata(user_profile, 'CONCOURSE_URL')
            if url is None:
                try:
                    url = os.environ['CONCOURSE_URL']
                except KeyError:
                    url = None
                if url is None:
                    url = getpass.getpass("Please provide full URL to Concourse: ")
        if url is None:
            user_profile = 'preset'
            url = CONFIG.get_metadata(user_profile, 'CONCOURSE_URL')
            if url is None:
                try:
                    url = os.environ['CONCOURSE_URL']
                except KeyError:
                    url = None
                if url is None:
                    url = getpass.getpass("Please provide full URL to Concourse: ")
        CONFIG.update_metadata(url, 'CONCOURSE_URL', user_profile)
        return url

    def update_config(self, new_data, profile_name):
        CONFIG = Config('flytools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            MY_CONFIG = PROFILE['config']
        except KeyError: 
            PROFILE['config'] = {}
            MY_CONFIG = PROFILE['config']
        MY_CONFIG.update(new_data)
        PROFILE['config'] = MY_CONFIG
        CONFIG.update_profile(PROFILE)
        
    def get_access_details(self, user_profile):
        ACCESS_TOKEN = self.get_access_token(user_profile=user_profile)
        URL = self.get_api_url(user_profile)
        return ACCESS_TOKEN, URL

    def list_all_pipelines(self, pattern, raw=False, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        URL = FLY_URL + '/api/v1/pipelines'
        headers = {
            'Authorization': 'Bearer ' + ACCESS_TOKEN
        }
        RESULT = curl.get(URL, headers=headers)
        DATA = []
        if RESULT == []:
            Log.critical("failed to get a list of teams from Concourse: " + RESULT.status_code)
        if not raw:
            REDUCTION = {'id':None,'name':None,'team_name':None}
            RESULT = reduce_json(RESULT, REDUCTION)
            for I in RESULT:
                if pattern is not None and pattern in I['name']:
                    DATA.append(I)
                elif pattern is not None and pattern not in I['name']:
                    continue
                elif pattern is None:
                    DATA.append(I)
        else:
            for I in RESULT:
                if pattern is not None and pattern in I['name']:
                    DATA.append(I)
                elif pattern is not None and pattern not in I['name']:
                    continue
                elif pattern is None:
                    DATA.append(I)
        return DATA

    def list_all_teams(self, pattern, raw=False, user_profile='default'):
        if pattern:
            pattern = pattern.strip()
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        URL = FLY_URL + '/api/v1/teams'
        headers = {
            'Authorization': 'bearer ' + ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        RESULT = curl.get(URL, headers=headers)
        DATA = []
        if RESULT == []:
            Log.critical("failed to get a list of teams from Concourse: " + RESULT.status_code)
        if not raw:
            REDUCTION = {'id':None,'name':None}
            RESULT = reduce_json(RESULT, REDUCTION)
            for I in RESULT:
                if pattern is not None and pattern in I['name']:
                    DATA.append(I)
                elif pattern is not None and pattern not in I['name']:
                    continue
                elif pattern is None:
                    DATA.append(I)
        else:
            for I in RESULT:
                if pattern is not None and pattern in I['name']:
                    DATA.append(I)
                elif pattern is not None and pattern not in I['name']:
                    continue
                elif pattern is None:
                    DATA.append(I)
        return DATA

    def list_pipeline_details(self, team, pipeline=None, raw=False, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        if pipeline is None:
            URL = FLY_URL + f'/api/v1/teams/{team}/pipelines'
        else:
            URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/{pipeline}'
        headers = {
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical("failed to get a list of pipelines from Concourse: " + RESP.status_code)
        return RESP

    def list_resource_versions(self, team, pipeline=None, resource=None, raw=False, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        if pipeline is None or resource is None:
            return None
        CI = concoursepy.api(FLY_URL, token=ACCESS_TOKEN)
        RESP = CI.list_resource_versions(team_name=team, pipeline_name=pipeline, resource_name=resource)
        if RESP == []:
            Log.critical("failed to get a list of resource versions from Concourse: " + RESP.status_code)
        return RESP
    
    def list_jobs(self, team, pipeline=None, raw=False, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        if pipeline is None:
            return None
        else:
            URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/{pipeline}/jobs'
        headers = {
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical("failed to get a list of jobs from Concourse: " + RESP.status_code)
        return RESP

    def list_builds(self, team, job=None, pipeline=None, raw=False, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        if pipeline is None or job is None:
            return None
        else:
            URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/{pipeline}/jobs/{job}/builds'
        headers = {
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical("failed to get a list of builds from Concourse: " + RESP.status_code)
        return RESP

    def list_build(self, team, build=None, job=None, pipeline=None, raw=False, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        if pipeline is None or job is None or build is None:
            return None
        else:
            URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/{pipeline}/jobs/{job}/builds/{build}'
        headers = {
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical("failed to get a list of builds from Concourse: " + RESP.status_code)
        return RESP

    def trigger_post_deploy_job(self, team, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/prd-push/jobs/govcloud-post-prd-deploy/builds'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.post(URL, headers=headers)
        return RESP

    def trigger_cscm_ticket_automation(self, team, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/cscm-ticket-automation/jobs/govcloud-cscm-ticket/builds'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.post(URL, headers=headers)
        return RESP

    def get_post_deploy_results(self, team, user_profile='default'):
        ACCESS_TOKEN, FLY_URL = self.get_access_details(user_profile)
        URL = FLY_URL + f'/api/v1/teams/{team}/pipelines/prd-push/jobs/govcloud-post-prd-deploy/builds'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'bearer ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        return RESP

def open_url(URL):
    import click
    try:
        click.launch(URL)
    except:
        pass
