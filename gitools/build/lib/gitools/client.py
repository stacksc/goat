import sys, os, gitlab
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getOtherCreds, getOtherToken
import getpass, datetime, os, subprocess, json, base64, requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

pushstack = list()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

CONFIG = Config('gitools')

class Client:

    def __init__(self):

        self.ACCESS_TOKEN_MAX_AGE = 2628288 # max access token age; in seconds for 1 month

    def setup_access(self, user_profile='default', username=None, password=None, overwrite=False):
        if user_profile not in CONFIG.PROFILES:
            CONFIG.create_profile(user_profile)
        CURRENT_SETUP = CONFIG.get_config(user_profile)
        if password is not None and username is not None:
            PASSWORD = password
            USERNAME = username
        else:
            while True:
                USERNAME, PASSWORD = getOtherCreds(title='gitlab')
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
        CONFIG = Config('gitools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_config(self, user_profile='default'):
        CONFIG = Config('gitools')
        GIT_CONFIG = CONFIG.display_profile(user_profile)
        return GIT_CONFIG

    def display_config(self, user_profile='default'):
        return self.get_config(user_profile) # OBSOLETE

    def get_config(self, user_profile='default'):
        CONFIG = Config('gitools')
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        GIT_CONFIG = PROFILE['config']
        return GIT_CONFIG

    def get_password(self, user_profile='default'):
        return self.get_property('password', user_profile)

    def get_username(self, user_profile='default'):
        return self.get_property('username', user_profile)

    def get_property(self, property_name, user_profile='default'):
        CONFIG = Config('gitools')
        if not self._get_prereq(user_profile):
            return None
        GIT_CONFIG = self.get_config(user_profile)
        if GIT_CONFIG is None:
            Log.critical('please setup git - auth setup - before proceeding with this option')
        return GIT_CONFIG[property_name]

    def get_access_token_age(self, user_profile='default'):
        ACCESS_TOKEN_DATA = self.get_property('access_token', user_profile)
        CREATED_ON = ACCESS_TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def get_access_token(self, user_profile='default'):
        CONFIG = Config('gitools')
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
        ACCESS_TOKEN_DATA = self.generate_access_token(user_profile)
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
        ACCESS_TOKEN = getOtherToken('git')
        if ACCESS_TOKEN is None:
            Log.critical("failed to retrieve new access token for gitlab, or token cannot be empty")
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

    def get_api_url(self, user_profile='default', url=None):
        CONFIG = Config('gitools')
        url = CONFIG.get_metadata('GIT_URL', user_profile)
        if url is None:
            url = CONFIG.get_metadata(user_profile, 'GIT_URL')
            if url is None:
                try:
                    url = os.environ['GIT_URL']
                except KeyError:
                    url = None
                if url is None:
                    url = getpass.getpass("Please provide full URL to GIT: ")
        CONFIG.update_metadata(url, 'GIT_URL', user_profile)
        return url

    def update_config(self, new_data, profile_name):
        CONFIG = Config('gitools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            GIT_CONFIG = PROFILE['config']
        except KeyError: # org_id wasn't present in configstore
            PROFILE['config'] = {}
            GIT_CONFIG = PROFILE['config']
        GIT_CONFIG.update(new_data)
        PROFILE['config'] = GIT_CONFIG
        CONFIG.update_profile(PROFILE)
        
    def get_access_details(self, user_profile):
        ACCESS_TOKEN = self.get_access_token(user_profile=user_profile)
        GIT_URL = self.get_api_url(user_profile)
        return ACCESS_TOKEN, GIT_URL

    def list_my_projects(self, pattern, raw=False, user_profile='default'):
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        URL = GIT_URL + f'/api/v4/projects'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(ACCESS_TOKEN)
        }
        RESULT = curl.get(URL, headers=headers)
        if not raw:
            DATA = []
            REDUCTION = {'name':None,'id':None,'description':None,'ssh_url_to_repo':None,'http_url_to_repo':None,'web_url':None}
            RESULT = reduce_json(RESULT, REDUCTION)
            if pattern:
                for I in RESULT:
                    if pattern in I:
                        return I
        return RESULT

    def list_group(self, group, raw=False, user_profile='default'):
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        URL = GIT_URL + f'/api/v4/groups/{group}'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(ACCESS_TOKEN)
        }
        RESULT = curl.get(URL, headers=headers)
        if not raw:
            DATA = []
            REDUCTION = {'projects':None}
            RESULT = reduce_json(RESULT, REDUCTION)
            for I in RESULT:
                REDUCTION = {'name':None,'id':None,'description':None,'ssh_url_to_repo':None,'http_url_to_repo':None,'web_url':None}
                OUT = reduce_json(RESULT[I], REDUCTION)
                DATA.append(OUT)
            return DATA
        return RESULT

    def list_my_groups(self, pattern, raw=False, user_profile='default'):
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        URL = GIT_URL + f'/api/v4/groups'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(ACCESS_TOKEN)
        }
        RESULT = curl.get(URL, headers=headers)
        RESP = self.list_my_namespaces(pattern, raw=raw, user_profile=user_profile)
        if RESP and RESULT:
            DATA = RESULT + RESP
        else:
            return None
        if not raw:
            REDUCTION = {'id':None,'name':None,'web_url':None}
            RESULT = reduce_json(RESULT, REDUCTION)
            RESP = reduce_json(RESP, REDUCTION)
            DATA = RESP + RESULT
            return list(map(dict, set(tuple(sorted(d.items())) for d in DATA)))
        return DATA

    def list_my_namespaces(self, pattern, raw=False, user_profile='default'):
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        URL = GIT_URL + f'/api/v4/namespaces'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(ACCESS_TOKEN)
        }
        RESULT = curl.get(URL, headers=headers)
        if not raw:
            REDUCTION = {'name':None,'id':None,'web_url':None}
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT
    
    def get_client(self, user_profile='default'):
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        GL = gitlab.Gitlab(GIT_URL, private_token=ACCESS_TOKEN)
        GL.auth()
        return GL

    def pull_repo(self, repo_url, all=False, user_profile='default'):
        import subprocess
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        RELATIVEPATH = "repos/"
        ABSOLUTE = os.path.expanduser("~/" + RELATIVEPATH)
        os.makedirs(ABSOLUTE, exist_ok=True)
        GL = self.get_client(user_profile)
        OWNED = GL.projects.list(owned=True, all=True)
        for ITEM in OWNED:
            FOLDER = ABSOLUTE + ITEM.namespace['name'] + "/" + ITEM.name
            if all is False:
                if repo_url == ITEM.ssh_url_to_repo:
                    pushd(FOLDER)
                    Log.info(f"Found matching repository: {ITEM.ssh_url_to_repo}")
                    Log.info("Pulling repository now")
                    if not os.path.exists(FOLDER):
                        Log.info("Creating directory for repo: " + FOLDER)
                        os.makedirs(FOLDER, exist_ok=True)
                    cancel_stdout()
                    subprocess.call(['git', 'pull', ITEM.ssh_url_to_repo])
                    restore_stdout()
            else:
                Log.info(f"Found matching repository: {ITEM.ssh_url_to_repo}")
                Log.info("Pulling repository now")
                if not os.path.exists(FOLDER):
                    Log.info("Creating directory for repo: " + FOLDER)
                    os.makedirs(FOLDER, exist_ok=True)
                pushd(FOLDER)
                cancel_stdout()
                subprocess.call(['git', 'pull', ITEM.ssh_url_to_repo])
                restore_stdout()
        return True

    def clone_repo(self, repo_url, all=False, user_profile='default'):
        import subprocess
        ACCESS_TOKEN, GIT_URL = self.get_access_details(user_profile)
        RELATIVEPATH = "repos/"
        ABSOLUTE = os.path.expanduser("~/" + RELATIVEPATH)
        os.makedirs(ABSOLUTE, exist_ok=True)
        GL = self.get_client(user_profile)
        OWNED = GL.projects.list(owned=True, all=True)
        for ITEM in OWNED:
            FOLDER = ABSOLUTE + ITEM.namespace['name'] + "/" + ITEM.name
            if all is False:
                if repo_url == ITEM.ssh_url_to_repo:
                    Log.info(f"Found matching repository: {ITEM.ssh_url_to_repo}")
                    Log.info("Cloning repository now")
                    if not os.path.exists(FOLDER):
                        Log.info("Creating directory for repo: " + FOLDER)
                        os.makedirs(FOLDER, exist_ok=True)
                    subprocess.call(['git', 'clone', ITEM.ssh_url_to_repo, FOLDER])
            else:
                Log.info(f"Found matching repository: {ITEM.ssh_url_to_repo}")
                Log.info("Cloning repository now")
                if not os.path.exists(FOLDER):
                    Log.info("Creating directory for repo: " + FOLDER)
                    os.makedirs(FOLDER, exist_ok=True)
                subprocess.call(['git', 'clone', ITEM.ssh_url_to_repo, FOLDER])
        return True

    def check_local_repo(self, repo_name, user_profile='default'):
        RELATIVEPATH = "repos/"
        ABSOLUTE = os.path.expanduser("~/" + RELATIVEPATH)
        GL = self.get_client(user_profile)
        OWNED = GL.projects.list(owned=True, all=True)
        for ITEM in OWNED:
            REPO = ITEM.namespace['name'] + "/" + ITEM.name
            FOLDER = ABSOLUTE + REPO
            if REPO == repo_name:
                if os.path.exists(FOLDER):
                    return True
        return False

def pushd(dirname):
    global pushstack
    pushstack.append(os.getcwd())
    os.chdir(dirname)

def popd():
    global pushstack
    os.chdir(pushstack.pop())

oldstdout = os.dup(1)
oldstderr = os.dup(2)
oldsysstdout = sys.stdout
oldsysstderr = sys.stderr

def cancel_stdout(stderr=True):
    sys.stdout.flush()
    devnull = open('/dev/null', 'w')
    os.dup2(devnull.fileno(), 1)
    sys.stdout = devnull
    if stderr:
        os.dup2(devnull.fileno(), 2)
        sys.stderr = devnull

def restore_stdout():
    sys.stdout.flush()
    sys.stdout.close()
    os.dup2(oldstdout, 1)
    os.dup2(oldstderr, 2)
    sys.stdout = oldsysstdout
    sys.stderr = oldsysstderr

