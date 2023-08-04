import sys, os, string, random
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getVIDMcreds
import getpass, datetime, sys, os, subprocess, json, base64, requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from random_words import RandomWords

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
CONFIG = Config('idptools')

def env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=False):
    source = '%s source %s' % ("set -a && " if include_unexported_variables else "", file_to_source_path)
    dump = '/usr/bin/python -c "import os, json; print json.dumps(dict(os.environ))"'
    pipe = subprocess.Popen(['/bin/bash', '-c', '%s && %s' % (source, dump)], stdout=subprocess.PIPE)
    return json.loads(pipe.stdout.read())

class IDPclient:
    def __init__(self, ctx):
        os.environ = env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=True)
        self.access_token = None

        try:
            if ctx.obj['setup'] == True:
                return None
        except:
            pass

        try:
            self.idp = ctx.obj['url']
        except:
            self.idp = None
            PROFILE = CONFIG.get_profile(ctx.obj['profile'])
            if PROFILE:
                ALL_ORGS = PROFILE['config']
                for ORG_ID in ALL_ORGS:
                    AUTH = ORG_ID
                    if AUTH:
                        ctx.obj['auth'] = AUTH
                        break
                self.idp = PROFILE['config'][AUTH]['url']
                ctx.obj['setup'] = False
            else:
                return None
        try:
            self._authenticate(ctx.obj['client-id'], ctx.obj['client-secret'])
        except:
            client_id, client_secret = self.get_client_id_secret(ctx.obj['profile'])
            try:
                self._authenticate(client_id, client_secret)
            except:
                PROFILE = CONFIG.get_profile(ctx.obj['profile'])
                ALL = PROFILE['config']
                for I in ALL:
                    client_id = ALL[I]['client-id']
                    secret = ALL[I]['client-secret']
                    url = ALL[I]['url']
                    if client_id and secret:
                        ctx.obj['client-id'] = client_id
                        ctx.obj['client-secret'] = secret
                        ctx.obj['url'] = url
                        break
                try:
                    self.idp = ctx.obj['url']
                    self._authenticate(client_id, secret)
                except:
                    Log.critical("unable to authenticate with profile: " + ctx.obj['profile'])

    def setup_access(self, url, client_id, secret, user_profile='default', overwrite=False):
        IDP = url
        if user_profile not in CONFIG.PROFILES:
            CONFIG.create_profile(user_profile)
        if not client_id and not secret:
            while True:
                CLIENT_ID, SECRET = getVIDMcreds()
                if SECRET != '':
                    break
                else:
                    Log.warn("client-secret cannot be empty. Please try again")
        else:
            CLIENT_ID = client_id
            SECRET = secret
        CURRENT_SETUP = CONFIG.get_config(CLIENT_ID, user_profile)
        if CURRENT_SETUP is not None:
            if 'client-secret' in CURRENT_SETUP and not overwrite:
                Log.warn("Detected existing config for target organization")
                while True:
                    CHOICE = input("Overwrite existing config? (Y/N): ")
                    if CHOICE == 'y' or CHOICE == 'Y' or CHOICE == 'n' or CHOICE == 'N':
                        break
                if CHOICE == 'n' or CHOICE == 'N':
                    return False   
            else:
                self.update_client_config(CLIENT_ID, new_data={
                    'client-id': CLIENT_ID,
                    'client-secret': SECRET,
                    'url': IDP,
                }, profile_name=user_profile)
        else:
            self.update_client_config(CLIENT_ID, new_data={
                'client-id': CLIENT_ID,
                'client-secret': SECRET,
                'url': IDP,
            }, profile_name=user_profile)
        return True

    def update_client_config(self, client_id, new_data, profile_name):
        CONFIG = Config('idptools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            CLIENT_CONFIG = PROFILE['config'][client_id]
        except KeyError:
            PROFILE['config'][client_id] = {}
            CLIENT_CONFIG = PROFILE['config'][client_id]
        CLIENT_CONFIG.update(new_data)
        PROFILE['config'][client_id] = CLIENT_CONFIG
        CONFIG.update_profile(PROFILE)

    def get_client_id_secret(self, profile_name):

        CONFIG = Config('idptools')
        PROFILE = CONFIG.get_profile(profile_name)
        if not PROFILE:
            return None, None
        try:
            ALL_ORGS = PROFILE['config']
            for ORG_ID in ALL_ORGS:
                AUTH = ORG_ID
                if AUTH:
                   break
            CLIENT_ID = PROFILE['config'][AUTH]['client-id']
            CLIENT_SECRET = PROFILE['config'][AUTH]['client-secret']
        except KeyError:
            Log.critical("unable to get client-config information")
        return CLIENT_ID, CLIENT_SECRET

    def display_idp_config(self, user_profile='default'):
        CONFIG = Config('idptools')
        VIDM_CONFIG = CONFIG.display_profile(user_profile)
        return VIDM_CONFIG

    def set_password(self, uid, password):

        URL = self.idp + '/SAAS/jersey/manager/api/scim/Users/' + uid
        HEADERS = {'Authorization': 'Bearer %s' % self.access_token}
        RESP = requests.patch(URL, headers=HEADERS, data='{"password": "%s"}' % password)
        if RESP.status_code != 204:
            Log.critical('Failed to set password with error: ' + RESP.text)
        else:
            Log.info(f'password reset is complete for user: {uid}')
            Log.info(f'password is: {password}')

    def generate_password(self):
        chars = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        number = random.sample('0123456789',1)
        upper = random.sample(string.ascii_uppercase,1)
        lower = random.sample(string.ascii_lowercase,1)
        special = random.sample('~!#$%^&*()=+[]{}|;:,.<>/?@',2)
        short = random.sample(chars,10)
        p15 = number + upper + lower + special + short
        rw = RandomWords()
        word = rw.random_word()[:3]
        postfix = "".join(random.sample(p15, 15))
        password = word + "_" + postfix
        return password

    
    def _authenticate(self, clientid, clientsecret):
        basicauth = base64.b64encode(bytes(clientid + ':' + clientsecret, 'utf-8'))
        basicauth = basicauth.decode('utf-8')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + str(basicauth)
        }
        resp = requests.post(
            self.idp + '/SAAS/auth/oauthtoken',
            headers=headers,
            data='grant_type=client_credentials',
            verify=False)

        if resp.status_code != 200:
            sys.exit(resp.text)
        access_token = resp.json()['access_token']
        self.access_token = access_token

    def list_tenant_config(self, tenant):

        DATA = []
        url = self.idp + '/SAAS/jersey/manager/api/tenants/settings?tenantId=' + tenant.upper()
        headers = {
                'Content-Type': 'application/vnd.vmware.horizon.manager.tenants.tenant.config.list+json',
                'Accept': 'application/vnd.vmware.horizon.manager.tenants.tenant.config.list+json',
                'Authorization': 'HZN %s' % self.access_token}

        try:
            resp = requests.get(url, headers=headers)
        except:
            return None
        DATA.append(resp.json()["items"])
        return DATA

    def list_directories(self, raw=False):
        directories = []
        url = self.idp + '/SAAS/jersey/manager/api/connectormanagement/directoryconfigs?includeJitDirectories=true'
        headers = {
                'Authorization': 'Bearer %s' % self.access_token
                }

        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            Log.critical("failed to get directories: " + resp.text)

        if raw is True:
            return resp.json()['items']

        for directory in resp.json()['items']:
            data = {
                "type": directory["type"],
                "name": directory["name"],
                "directoryId": directory["directoryId"]
            }
            directories.append(data)
        return directories

    def list_users(self, raw=False):
        users = []
        url = self.idp + '/SAAS/jersey/manager/api/scim/Users'
        headers = {'Authorization': 'Bearer %s' % self.access_token}
        params = { 'count': 10000 }
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            sys.exit(resp.text)

        if raw is True:
            return resp.json()['Resources']
        try:
            for user in resp.json()['Resources']:
                data = {
                    "username": user["userName"],
                    "givenName": user["name"]["givenName"],
                    "familyName": user["name"]["familyName"],
                    "id": user["id"],
                    "email": user["emails"][0]["value"],
                    "active": user["active"],
                    "domain": user["urn:scim:schemas:extension:workspace:1.0"]["domain"],
                    "lastModified": user["meta"]["lastModified"]
                }
                users.append(data)
        except IndexError:
            return None
        return users

    def listPasswordExpiration(self, days):

        if not days:
            days = 1
        url = self.idp + '/SAAS/jersey/manager/api/scim/Users'
        headers = {'Authorization': 'Bearer %s' % self.access_token}
        params = { 'count': 10000 }
        resp = requests.get(url, headers=headers, params=params)

        if resp.status_code != 200:
            sys.exit(resp.text)

        try:
            users = []
            for user in resp.json()['Resources']:
                try:
                    modifiedDate = datetime.datetime.strptime(user["meta"]["lastModified"], '%Y-%m-%dT%H:%M:%S.%fZ')
                    expirationDate = modifiedDate + datetime.timedelta(days=60)
                    remainingDays = expirationDate - datetime.datetime.now()
                except:
                    continue

                # if remainingDays.days < int(days) and user["urn:scim:schemas:extension:workspace:1.0"]["domain"] != "System Domain":
                if remainingDays.days < int(days):
                    data = {
                        "username": user["userName"],
                        "givenName": user["name"]["givenName"],
                        "familyName": user["name"]["familyName"],
                        "id": user["id"],
                        "email": user["emails"][0]["value"],
                        "active": user["active"],
                        "domain": user["urn:scim:schemas:extension:workspace:1.0"]["domain"],
                        "lastModified": user["meta"]["lastModified"],
                        "expirationDate": expirationDate.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "expiredIn": remainingDays.days
                    }
                    users.append(data)
        except IndexError:
            return None
        return users

# helper function to make this more globally accessible
def idp_setup(self, url, client_id, secret, user_profile='default', overwrite=False):
    CONFIG = Config('idptools')
    IDP = url
    if user_profile not in CONFIG.PROFILES:
        CONFIG.create_profile(user_profile)
    if not client_id and not secret:
        while True:
            CLIENT_ID, SECRET = getVIDMcreds()
            if SECRET != '':
                break
            else:
                Log.warn("client-secret cannot be empty. Please try again")
    else:
        CLIENT_ID = client_id
        SECRET = secret
    CURRENT_SETUP = CONFIG.get_config(CLIENT_ID, user_profile)
    if CURRENT_SETUP is not None:
        if 'client-secret' in CURRENT_SETUP and not overwrite:
            Log.warn("Detected existing config for target organization")
            while True:
                CHOICE = input("Overwrite existing config? (Y/N): ")
                if CHOICE == 'y' or CHOICE == 'Y' or CHOICE == 'n' or CHOICE == 'N':
                    break
            if CHOICE == 'n' or CHOICE == 'N':
                return False   
        else:
            new_data = {
                'client-id': CLIENT_ID,
                'client-secret': SECRET,
                'url': IDP
            }
            PROFILE = CONFIG.get_profile(user_profile)
            try:
                CLIENT_CONFIG = PROFILE['config'][CLIENT_ID]
            except KeyError:
                PROFILE['config'][CLIENT_ID] = {}
                CLIENT_CONFIG = PROFILE['config'][CLIENT_ID]
            CLIENT_CONFIG.update(new_data)
            PROFILE['config'][CLIENT_ID] = CLIENT_CONFIG
            CONFIG.update_profile(PROFILE)
    else:
        new_data={
            'client-id': CLIENT_ID,
            'client-secret': SECRET,
            'url': IDP
        }
        PROFILE = CONFIG.get_profile(user_profile)
        try:
            CLIENT_CONFIG = PROFILE['config'][CLIENT_ID]
        except KeyError:
            PROFILE['config'][CLIENT_ID] = {}
            CLIENT_CONFIG = PROFILE['config'][CLIENT_ID]
        CLIENT_CONFIG.update(new_data)
        PROFILE['config'][CLIENT_ID] = CLIENT_CONFIG
        CONFIG.update_profile(PROFILE)
