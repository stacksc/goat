import time
import jenkins
from jenkins import Jenkins
import sys, os
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getOtherCreds, getFullUrl
import getpass, datetime, os, subprocess, json, base64, requests
from datetime import timedelta
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
CONFIG = Config('jenkinstools')

class JenkinsClient:

    def __init__(self):

        self.ACCESS_TOKEN_MAX_AGE = 29*60 # max access token age; in seconds
        self.CRUMB_TOKEN_MAX_AGE = 29*60 # max crumb token age; in seconds

    def setup_access(self, user_profile='default', username=None, password=None, overwrite=False):
        if user_profile not in CONFIG.PROFILES:
            CONFIG.create_profile(user_profile)

        CURRENT_SETUP = CONFIG.get_config(user_profile)
        if password is not None and username is not None:
            PASSWORD = password
            USERNAME = username
        else:
            while True:
                USERNAME, PASSWORD = getOtherCreds('jenkins')
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
        ACCESS_TOKEN = self.generate_access_token(PASSWORD, USERNAME, user_profile)
        try:
            CRUMB_TOKEN = self.generate_crumb(user_profile)
        except:
            CRUMB_TOKEN = 'N/A'
        self.update_config(new_data={
                    'access_token': ACCESS_TOKEN
                }, profile_name=user_profile)
        self.update_config(new_data={
                    'crumb_token': CRUMB_TOKEN
                }, profile_name=user_profile)
        return True

    def _get_prereq(self, user_profile='default'):
        CONFIG = Config('jenkinstools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_jenkins_config(self, user_profile='default'):
        CONFIG = Config('jenkinstools')
        JENKINS_CONFIG = CONFIG.display_profile(user_profile)
        return JENKINS_CONFIG

    def display_config(self, user_profile='default'):
        return self.get_config(user_profile) # OBSOLETE

    def get_config(self, user_profile='default'):
        CONFIG = Config('jenkinstools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        JENKINS_CONFIG = PROFILE['config']
        return JENKINS_CONFIG

    def get_jenkins_password(self, user_profile='default'):
        return self.get_jenkins_property('password', user_profile)

    def get_jenkins_username(self, user_profile='default'):
        return self.get_jenkins_property('username', user_profile)

    def get_jenkins_property(self, property_name, user_profile='default'):
        CONFIG = Config('jenkinstools')
        if not self._get_prereq(user_profile):
            return None
        JENKINS_CONFIG = self.get_config(user_profile)
        if JENKINS_CONFIG is None:
            Log.critical('please setup jenkins - auth setup - before proceeding with this option')
        return JENKINS_CONFIG[property_name]

    def get_access_token_age(self, user_profile='default'):
        TOKEN_DATA = self.get_jenkins_property('access_token', user_profile)
        CREATED_ON = TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def get_crumb_token_age(self, user_profile='default'):
        TOKEN_DATA = self.get_jenkins_property('crumb_token', user_profile)
        CREATED_ON = TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def get_crumb_token(self, user_profile='default'):
        CONFIG = Config('jenkinstools')
        try:
            PASSWORD = self.get_jenkins_password(user_profile)
            USERNAME = self.get_jenkins_username(user_profile)
        except FileExistsError:
            PASSWORD = None
            USERNAME = None

        if PASSWORD is None or USERNAME is None:
            Log.warn("Failed getting crumb token - no password available")
            return None
        try:
            CRUMB_TOKEN_AGE = self.get_crumb_token_age(user_profile)
        except:
            CRUMB_TOKEN_AGE = None
        if CRUMB_TOKEN_AGE is not None:
            if CRUMB_TOKEN_AGE < self.CRUMB_TOKEN_MAX_AGE:
                return self._get_crumb_token(user_profile)
        Log.info("crumb token expired or not found. Generating a new one")
        try:
            CRUMB_TOKEN_DATA = self.generate_crumb(user_profile)
            self.update_config(new_data={
                        'crumb_token': CRUMB_TOKEN_DATA
                    }, profile_name=user_profile)
            return CRUMB_TOKEN_DATA['token']
        except:
            pass

    def get_access_token(self, user_profile='default'):
        CONFIG = Config('jenkinstools')
        try:
            PASSWORD = self.get_jenkins_password(user_profile)
            USERNAME = self.get_jenkins_username(user_profile)
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
        Log.info("access token expired or not found. Generating a new one")
        ACCESS_TOKEN_DATA = self.generate_access_token(PASSWORD, USERNAME, user_profile)
        self.update_config(new_data={
                    'access_token': ACCESS_TOKEN_DATA
                }, profile_name=user_profile)
        return ACCESS_TOKEN_DATA['token']

    def _get_access_token(self, user_profile='default'):
        TOKEN_DATA = self.get_jenkins_property('access_token', user_profile)
        return TOKEN_DATA['token']

    def _get_crumb_token(self, user_profile='default'):
        TOKEN_DATA = self.get_jenkins_property('crumb_token', user_profile)
        return TOKEN_DATA['crumb']

    def all_job_history(self, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + '/api/json?tree=jobs[name,url,builds[result,url]{0,10}]&pretty=true'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list build history from jenkins and user {name}: " + str(RESP))
        try:
            REDUCTION = { 'name': None, 'builds':['result'] }
            RESP = reduce_json(RESP['jobs'], REDUCTION)
            DATA.append(RESP)
        except:
            DATA.append(RESP)
        return DATA

    def last_job_history(self, name, raw, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + f'/job/{name}/lastBuild/api/json'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list job history from jenkins and {name}: " + str(RESP))
        if not raw:
            try:
                REDUCTION = { 'number': None, 'result': None, 'url': None, 'fullDisplayName': None, 'subBuilds': None }
                RESP = reduce_json(RESP, REDUCTION)
                DATA.append(RESP)
            except:
                DATA.append(RESP)
            return DATA
        return RESP

    def job_history(self, name, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + f'/job/{name}/api/json?tree=name,builds[url]'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list job history from jenkins and {name}: " + str(RESP))
        for I in RESP['builds']:
            DATA.append(I['url'])
        return DATA

    def job_details(self, url, raw, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = url + '/api/json'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list job history from jenkins and {url}: " + str(RESP))
        if not raw:
            try:
                REDUCTION = { 'number': None, 'result': None, 'url': None, 'fullDisplayName': None, 'subBuilds': None }
                RESP = reduce_json(RESP, REDUCTION)
                DATA.append(RESP)
            except:
                DATA.append(RESP)
            return DATA
        return RESP

    def get_log_output(self, url, raw, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = url + '/log'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list job log ouptut from jenkins and {url}: " + str(RESP))
        return RESP.text

    def get_console_output(self, url, raw, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = url + '/consoleText'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list job console ouptut from jenkins and {url}: " + str(RESP))
        return RESP.text

    def job_names(self, pattern=None, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + '/api/json?tree=jobs[name,jobs[name,jobs[name]]]&pretty=true'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list all job names from jenkins: " + str(RESP))
        try:
            REDUCTION = { 'name': None }
            RESP = reduce_json(RESP['jobs'], REDUCTION)
            for I in RESP:
                if pattern:
                    if pattern in I['name']:
                        DATA.append(I['name'])
                else:
                    DATA.append(I['name'])
        except:
            DATA.append(RESP)
        return DATA

    def generate_crumb(self, user_profile='default'):
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + '/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,%22:%22,//crumb)'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN
        }
        RESP = curl.get(URL, headers=headers)
        if RESP.status_code != 200:
            Log.critical("failed to generate crumb from jenkins: " + RESP)
        CRUMB_TOKEN_TIMESTAMP = datetime.datetime.now().timestamp()
        CRUMB_TOKEN_DATA = {
                'crumb': RESP.text.replace('"','').strip(),
                'timestamp': CRUMB_TOKEN_TIMESTAMP
        }
        return CRUMB_TOKEN_DATA

    def generate_access_token(self, PASSWORD, USERNAME, user_profile):
        api_url = self.get_jenkins_api_url(user_profile)
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
            Log.critical("Failed to retrieve new access token from Jenkins - API call failed: " + RESPONSE.text)

        ACCESS_TOKEN = str(basicauth)
        ACCESS_TOKEN_TIMESTAMP = datetime.datetime.now().timestamp()
        ACCESS_TOKEN_DATA = {
             'token': ACCESS_TOKEN,
             'timestamp': ACCESS_TOKEN_TIMESTAMP
        }
        return ACCESS_TOKEN_DATA

    def get_jenkins_api_url(self, user_profile='default', jenkins_url=None):
        CONFIG = Config('jenkinstools')
        jenkins_url = CONFIG.get_metadata('JENKINS_URL', user_profile)
        if jenkins_url is None:
            jenkins_url = getFullUrl('jenkins')
        CONFIG.update_metadata(jenkins_url, 'JENKINS_URL', user_profile)
        return jenkins_url

    def update_config(self, new_data, profile_name):
        CONFIG = Config('jenkinstools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            JENKINS_CONFIG = PROFILE['config']
        except KeyError: # org_id wasn't present in configstore
            PROFILE['config'] = {}
            JENKINS_CONFIG = PROFILE['config']
        JENKINS_CONFIG.update(new_data)
        PROFILE['config'] = JENKINS_CONFIG
        CONFIG.update_profile(PROFILE)
        
    def get_access_details(self, user_profile='default'):
        ACCESS_TOKEN = self.get_access_token(user_profile=user_profile)
        JENKINS_URL = self.get_jenkins_api_url(user_profile)
        return ACCESS_TOKEN, JENKINS_URL

    def get_jenkins_creds(self, user_profile='default'):
        USERNAME = self.get_jenkins_username(user_profile=user_profile)
        PASSWORD = self.get_jenkins_password(user_profile=user_profile)
        JENKINS_URL = self.get_jenkins_api_url(user_profile)
        return USERNAME, PASSWORD, JENKINS_URL

    def get_jenkins_session(self, url, username, password):
        SESSION = Jenkins(url,
            username=username,
            password=password
        )
        return SESSION
 
    def get_job_info(self, name, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        INFO = SERVER.get_job_info(name)
        if not INFO:
            Log.critical(f"unable to pull information for job name {name}")
        return INFO

    def get_job_config(self, name, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        INFO = SERVER.get_job_config(name)
        if not INFO:
            Log.critical(f"unable to pull configuration for job name {name}")
        return INFO

    def get_user_details(self, name, raw, user_profile='default', url=False):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        if url is True:
            URL = name + '/api/json?depth=1&pretty=true'
        else:
            URL = JENKINS_URL + f'/user/{name}/api/json?depth=1&pretty=true'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list user details for {name} from jenkins: " + str(RESP))
        if raw is False:
            try:
                REDUCTION = { 'id': None, 'fullName': None, 'absoluteUrl': None}
                RESP = reduce_json(RESP, REDUCTION)
                DATA.append(RESP)
            except:
                DATA.append(RESP)
        else:
            DATA.append(RESP)
        return DATA

    def get_creds(self, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + f'/credentials'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list build history for {name} from jenkins: " + str(RESP))
        for LINE in RESP.text.split("\n"):
             if "</td><td><a href=" in LINE:
                  if "<span tooltip=" in LINE:
                      DATA.append(LINE)
        return DATA

    def get_users(self, user_profile='default'):
        DATA = []
        ACCESS_TOKEN, JENKINS_URL = self.get_access_details(user_profile)
        URL = JENKINS_URL + f'/asynchPeople/api/json?depth=1&pretty=true'
        headers = {
            'Authorization': 'Basic ' + ACCESS_TOKEN,
        }
        RESP = curl.get(URL, headers=headers)
        if RESP == []:
            Log.critical(f"failed to list build history for {name} from jenkins: " + str(RESP))
        return RESP

    def get_whoami(self, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        INFO = SERVER.get_whoami()
        if not INFO:
            Log.critical(f"unable to pull configuration for job name {name}")
        return INFO

    def last_failed_build(self, name, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        INFO = SERVER.get_job_info(name)['lastFailedBuild']
        return INFO

    def last_good_build(self, name, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        INFO = SERVER.get_job_info(name)['lastSuccessfulBuild']
        return INFO

    def build_url(self, job, params, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        MYURL = SERVER.build_job_url(job, params)
        return MYURL

    def trigger_build(self, job, params, user_profile='default'):
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        SERVER = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        SERVER.build_job(job, params)
        QUEUE = SERVER.get_queue_info()
        ID = QUEUE[0].get('id')
        if ID:
            return ID
        return QUEUE

    def launch_job(self, job_name, parameters={}, files={}, wait=True, interval=30,  time_out=7200, sleep=10, user_profile='default'):
        JOB_NAME = job_name
        # get our default credentials
        USERNAME, PASSWORD, JENKINS_URL = self.get_jenkins_creds(user_profile)
        # establish our session
        JENKINS_CONNECTION = self.get_jenkins_session(JENKINS_URL, USERNAME, PASSWORD)
        # we lunch the job and returns a queue_id
        JOB_ID = JENKINS_CONNECTION.build_job(JOB_NAME, parameters, files=files)
        # from the queue_id we get the job number that was created
        time.sleep(sleep)
        try:
            QUEUE_JOB = JENKINS_CONNECTION.get_queue_item(JOB_ID, depth=0)
            BUILD_NUMBER = QUEUE_JOB["executable"]["number"]
            Log.info(f"job_name: {JOB_NAME}")
            Log.info(f"build_number: {BUILD_NUMBER}")
            if wait is True:
                NOW = datetime.datetime.now()
                LATER = NOW + timedelta(seconds=time_out)
                while True:
                    # we check current time vs the timeout(later)
                    if datetime.datetime.now() > LATER:
                        raise ValueError(f"Job: {JOB_NAME}:{BUILD_NUMBER} is running for more than {time_out} seconds and we"
                                         f"stopped monitoring the job. Please check it in Jenkins console.")
                    B = JENKINS_CONNECTION.get_job_info(JOB_NAME, depth=1, fetch_all_builds=False)
                    for I in B["builds"]:
                        LOOP_ID = I["id"]
                        if int(LOOP_ID) == BUILD_NUMBER:
                            RESULT = (I["result"])
                            Log.info(f"result: running...")  # in the json looks it will look like null
                            if RESULT is not None:
                                return I
                    time.sleep(interval)
            return BUILD_NUMBER
        except:
            return JOB_ID
        return JOB_ID
