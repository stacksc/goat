import re
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import curl
from configstore.configstore import Config
from toolbox.getpass import getCSPcreds
import getpass, datetime, os, subprocess, json

def env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=False):
    source = '%s source %s' % ("set -a && " if include_unexported_variables else "", file_to_source_path)
    dump = '/usr/bin/python -c "import os, json; print json.dumps(dict(os.environ))"'
    pipe = subprocess.Popen(['/bin/bash', '-c', '%s && %s' % (source, dump)], stdout=subprocess.PIPE)
    return json.loads(pipe.stdout.read())

class CSPclient:

    def __init__(self):

        os.environ = env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=True)
        self.ACCESS_TOKEN_MAX_AGE = 29*60 # max access token age; in seconds

    def setup_org_access(self, org_id=None, org_name=None, user_profile='default', refresh_token=None, overwrite=False):
        CONFIG = Config('csptools')
        if user_profile not in CONFIG.PROFILES:
            CONFIG.create_profile(user_profile)
        if org_id is None:
            if org_name is None:
                MSG = 'orgid or name for the org is required to setup access'
                LINK = 'https://gitlab.eng.vmware.com/govcloud-ops/govcloud-devops-python/-/blob/main/csptools/README.md'
                CMD = None
                TITLE = 'PYPS'
                SUBTITLE = 'CRITICAL'
                Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
                Log.critical(MSG)
            org_id = self.find_org_id(org_name, user_profile)
            if org_id is None:
                Log.critical('please provide orgid; org name not found in configstore')
        if refresh_token is not None:
            REFRESH_TOKEN = refresh_token
        else:
            while True:
                REFRESH_TOKEN = getCSPcreds()
                if REFRESH_TOKEN != '':
                    break
                else:
                    Log.warn("Access token cannot be empty. Please try again")
        CURRENT_ORG_SETUP = CONFIG.get_config(org_id, user_profile)
        if CURRENT_ORG_SETUP is not None:
            if 'access_token' in CURRENT_ORG_SETUP and not overwrite:
                Log.warn("Detected existing config for target organization")
                while True:
                    CHOICE = input("Overwrite existing config? (Y/N): ")
                    if CHOICE == 'y' or CHOICE == 'Y' or CHOICE == 'n' or CHOICE == 'N':
                        break
                if CHOICE == 'n' or CHOICE == 'N':
                    return False   
            else:
                self.update_org_config(org_id, new_data={
                    'refresh_token': REFRESH_TOKEN
                }, profile_name=user_profile)
        else:
            self.update_org_config(org_id, new_data={
                    'id': org_id,
                    'refresh_token': REFRESH_TOKEN
                }, profile_name=user_profile)
            if org_name is not None:
                self.update_org_config(org_id, new_data={
                    'name': org_name
                }, profile_name=user_profile)
        ACCESS_TOKEN = self.generate_access_token(REFRESH_TOKEN, user_profile)
        self.update_org_config(org_id, new_data={
                    'access_token': ACCESS_TOKEN
                }, profile_name=user_profile)
        return True

    def _get_prereq(self, org_id=None, org_name=None, user_profile='default'):
        CONFIG = Config('csptools')
        if org_id is None and org_name is None:
            Log.warn('Operation cannot continue - either org_id or org_name is required')
            return False
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None or PROFILE['config'] == {}:
            Log.warn("Operation cannot continue - user profile does not exist")
            return False
        return True

    def display_csp_config(self, user_profile='default'):
        CONFIG = Config('csptools')
        CSP_CONFIG = CONFIG.display_profile(user_profile)
        return CSP_CONFIG

    def display_org_config(self, org_id=None, org_name=None, user_profile='default'):
        return self.get_org_config(org_id, org_name, user_profile) # OBSOLETE

    def get_org_config(self, org_id=None, org_name=None, user_profile='default'):
        CONFIG = Config('csptools')
        if org_id is None and org_name is not None:
            org_id = self.find_org_id(org_name, user_profile)
        PROFILE = CONFIG.get_profile(user_profile)
        if PROFILE is None:
            return None
        ORG_CONFIG = PROFILE['config']
        return ORG_CONFIG

    def get_org_property(self, property_name, org_id=None, org_name=None, user_profile='default'):
        CONFIG = Config('csptools')
        if not self._get_prereq(org_id, org_name, user_profile):
            return None
        if org_id is None and org_name is not None:
            org_id = self.find_org_id(org_name, user_profile)
        ORG_CONFIG = self.get_org_config(org_id, org_name, user_profile)
        if ORG_CONFIG is None:
            Log.critical('please setup an org - auth setup - before proceeding with this option')
        return ORG_CONFIG[org_id][property_name]

    def get_org_refresh_token(self, org_id=None, org_name=None, user_profile='default'):
        return self.get_org_property('refresh_token', org_id, org_name, user_profile)

    def get_org_access_token_age(self, org_id=None, org_name=None, user_profile='default'):
        ACCESS_TOKEN_DATA = self.get_org_property('access_token', org_id, org_name, user_profile)
        CREATED_ON = ACCESS_TOKEN_DATA['timestamp']
        TIME_NOW = datetime.datetime.now().timestamp()
        return TIME_NOW - CREATED_ON

    def find_org_id(self, org_name, user_profile='default'):
        # finds org ID from the list of SAVED orgs; does not look through CSP database
        CONFIG = Config('csptools')
        try:
            PROFILE = CONFIG.get_profile(user_profile)
        except:
            return None
        ALL_ORGS = PROFILE['config']
        for ORG_NAME in ALL_ORGS:
            ORG = ALL_ORGS[ORG_NAME]
            if re.search(org_name, ORG['name'], re.IGNORECASE):
                return ORG['id']
        return None

    def find_org_name(self, org_id, user_profile='default'):
        # finds org ID from the list of SAVED orgs; does not look through CSP database
        CONFIG = Config('csptools')
        try:
            PROFILE = CONFIG.get_profile(user_profile)
        except:
            return None
        ALL_ORGS = PROFILE['config']
        for ORG_NAME in ALL_ORGS:
            ORG = ALL_ORGS[ORG_NAME]
            if ORG['id'] == org_id:
                return ORG['name']
        return None

    def get_org_access_token(self, org_id=None, org_name=None, user_profile='default'):
        CONFIG = Config('csptools')
        try:
            REFRESH_TOKEN = self.get_org_refresh_token(org_id, org_name, user_profile)
        except FileExistsError:
            REFRESH_TOKEN = None
        if REFRESH_TOKEN is None:
            Log.warn("Failed getting org access token - no refresh token available")
            return None
        try:
            ACCESS_TOKEN_AGE = self.get_org_access_token_age(org_id, org_name, user_profile)
        except:
            ACCESS_TOKEN_AGE = None
        if ACCESS_TOKEN_AGE is not None:
            if ACCESS_TOKEN_AGE < self.ACCESS_TOKEN_MAX_AGE:
                return self._get_org_access_token(org_id, org_name, user_profile)
        Log.info("Access token expired or not found. Generating a new one")
        if org_id is None:
            org_id = self.find_org_id(org_name, user_profile)
        ACCESS_TOKEN_DATA = self.generate_access_token(REFRESH_TOKEN, user_profile)
        UPDATE_DATA = {
            'access_token':{
                'token': ACCESS_TOKEN_DATA['token'],
                'timestamp': ACCESS_TOKEN_DATA['timestamp']
            }
        }
        CONFIG.update_config(UPDATE_DATA, org_id, user_profile)
        return ACCESS_TOKEN_DATA['token']

    def _get_org_access_token(self, org_id=None, org_name=None, user_profile='default'):
        REFRESH_TOKEN_DATA = self.get_org_property('access_token', org_id, org_name, user_profile)
        return REFRESH_TOKEN_DATA['token']

    def generate_access_token(self, REFRESH_TOKEN, user_profile):
        CSP_API_URL = self.get_csp_api_url(user_profile)
        RESPONSE = curl.post(
            url=f"{CSP_API_URL}/csp/gateway/am/api/auth/api-tokens/authorize", 
            headers={
                        "accept": "application/json",
                        "content-type": "application/x-www-form-urlencoded"
                    }, 
            data={
                "refresh_token": {REFRESH_TOKEN}
            }
        )
        if RESPONSE is None:
            Log.warn("Failed to retrieve new access token from CSP - API call failed")
            return None
        if 'username' in RESPONSE.keys():
            if RESPONSE['username'] == 'null':
                Log.warn("Failed to retrieve new access token from CSP - null username detected")
                return None
        if 'access_token' not in RESPONSE.keys():
            Log.warn('Failed to retrieve new access token from CSP - see response below')
            Log.warn(f'{RESPONSE}')
            return None
        else:
            ACCESS_TOKEN = RESPONSE['access_token']
            ACCESS_TOKEN_TIMESTAMP = datetime.datetime.now().timestamp()
            ACCESS_TOKEN_DATA = {
                'token': ACCESS_TOKEN,
                'timestamp': ACCESS_TOKEN_TIMESTAMP
            }
            return ACCESS_TOKEN_DATA

    def get_csp_api_url(self, user_profile, csp_url=None):
        CONFIG = Config('csptools')
        csp_url = CONFIG.get_metadata('CSP_URL', user_profile)
        if csp_url is None:
            csp_url = CONFIG.get_metadata(user_profile, 'CSP_URL')
            if csp_url is None:
                try:
                    csp_url = os.environ['CSP_URL']
                except KeyError:
                    csp_url = None
                if csp_url is None:
                    csp_url = getpass.getpass("Please provide full URL to CSP: ")
        CONFIG.update_metadata(csp_url, 'CSP_URL', user_profile)
        return csp_url

    def update_org_config(self, org_id, new_data, profile_name):
        CONFIG = Config('csptools')
        PROFILE = CONFIG.get_profile(profile_name)
        try:
            ORG_CONFIG = PROFILE['config'][org_id]
        except KeyError: # org_id wasn't present in configstore
            PROFILE['config'][org_id] = {}
            ORG_CONFIG = PROFILE['config'][org_id]
        ORG_CONFIG.update(new_data)
        PROFILE['config'][org_id] = ORG_CONFIG
        CONFIG.update_profile(PROFILE)

    def get_access_details(self, auth_org_id, user_profile):
        ACCESS_TOKEN = self.get_org_access_token(org_id=auth_org_id, user_profile=user_profile)
        CSP_URL = self.get_csp_api_url(user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        return ACCESS_TOKEN, CSP_URL, VMC_URL

    def create_org(self, new_org_name=None, auth_org='operator', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.post(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "displayName": new_org_name
            }
        )

        ORGID = RESULT['refLink'].split('/')[-1]
        return ORGID

    def add_to_service_id(self, org_id, service_id, auth_org='platform', user_profile='platform'):

        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = { "isTosPreSigned": "true", "serviceDefinitionId": service_id, "orgId": org_id }
        RESULT = curl.post(
            url=f"{CSP_URL}/csp/gateway/slc/api/service-access",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson = DATA
        )
        return RESULT

    def list_orgs_with_sddc(self, auth_org, user_profile='operator', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/orgs",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = {'id':None,'display_name':None,'name':None,'user_name':None,'created':None,'org_type':None,'project_state':None,'properties':None}
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT

    def trigger_ss_backend(self, auth_org, user_profile='operator', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/orgs",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = {'id':None,'display_name':None,'name':None,'user_name':None,'created':None,'org_type':None,'project_state':None}
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT

    def list_orgs(self, auth_org, user_profile='operator', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/orgs",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = {'id':None,'display_name':None,'name':None,'user_name':None,'created':None,'org_type':None,'project_state':None}
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT

    def list_roles(self, raw, auth_org, user_profile='default'):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/config",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = {'all_roles':None}
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT

    def org_property_list(self, target_org, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}/properties/versions?max=1",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def list_org_features(self, target_org, auth_org='operator', user_profile='default', raw=False):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}/features",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = { 'id':['feature','id'], 'description':['feature','description'], 'enable':['feature','enable'], 'toggle_type':['feature','toggle_type'], 
                        'type':['feature','type'], 'category':['feature','category'], 'namespace':['feature','namespace'], 'state':['feature','state']}
            RESULT = reduce_json(RESULT, REDUCTION, True)
        return RESULT

    def list_org_tags(self, target_org, auth_org='operator', user_profile='default'):
        RESULT = self.org_property_list(target_org, auth_org, user_profile)
        if 'tags' in RESULT:
            return RESULT['tags']
        else:
            return []

    def get_vmc_api_url(self, user_profile):
        CONFIG = Config('csptools')
        VMC_URL = CONFIG.get_metadata('VMC_URL', user_profile)
        if VMC_URL is None:
            VMC_URL = CONFIG.get_from_env('VMC_URL', 'Please provide full URL to VMC (Skyscraper): ', 'metadata', user_profile)
        return VMC_URL

    def rename_org(self, target_org_id, new_org_name, auth_org='operator', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.patch(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org_id}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "displayName": new_org_name
            }
        )
        return RESULT

    def delete_org(self, target_org_id, auth_org='operator', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.delete(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{target_org_id}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )
        return RESULT

    def activate_org(self, target_org_id, auth_org='operator', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.put(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{target_org_id}?action=enable",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )
        return RESULT

    def org_property_delete(self, target_org, property_name, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.delete(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}/properties/{property_name}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )
        return RESULT

    def org_type_add(self, target_org, property_name, property_value, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.patch(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                    property_name: property_value
            }
        )
        return RESULT

    def org_property_add(self, target_org, property_name, property_value, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.patch(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "properties": {
                    "values": {
                        property_name: property_value
                    }
                }
            }
        )
        return RESULT

    def org_set_type(self, target_org, org_type, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        return self.org_type_add(TARGET_ID, 'org_type', org_type, AUTH_ID, user_profile)

    def update_sid(self, sid, target_org, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.patch(
            url=f"{VMC_URL}/vmc/api/orgs/{TARGET_ID}/tags",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                    "sdpSid": sid
                }
        )
        return RESULT

    def org_default_properties(self, target_org, auth_org='operator', user_profile='default'):
        CONFIG = Config('csptools')
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        REGION = CONFIG.get_var('vmc_west', 'metadata', 'REGION', user_profile)
        DC_1 = CONFIG.get_var('vmc_west_dc1', 'metadata', 'DC_1', user_profile)
        DC_2 = CONFIG.get_var('vmc_west_dc1', 'metadata', 'DC_2', user_profile)
        DC_4 = CONFIG.get_var('vmc_west_dc1', 'metadata', 'DC_4', user_profile)
        EREGION = CONFIG.get_var('vmc_east', 'metadata', 'EREGION', user_profile)
        EDC_0 = CONFIG.get_var('vmc_east_ec0', 'metadata', 'EDC_0', user_profile)
        EDC_1 = CONFIG.get_var('vmc_east_ec1', 'metadata', 'EDC_1', user_profile)
        EDC_2 = CONFIG.get_var('vmc_east_ec2', 'metadata', 'EDC_2', user_profile)
        RESULT = curl.patch(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "properties": {
                    "values": {
                        "accountLinkingOptional": "false",
                        "enableZeroCloudCloudProvider": "false",
                        "certificateValidDays": "365",
                        "defaultAwsRegions": "GovCloud,US_GOV_EAST_1",
                        "defaultHostsPerSddc": "3",
                        "enableAWSCloudProvider": "true",
                        "enabledAvailabilityZones": f"{{\"{REGION}\":[\"{DC_1}\",\"{DC_4}\",\"{DC_2}\"], \"{EREGION}\": [\"{EDC_0}\",\"{EDC_1}\",\"{EDC_2}\"]}}",
                        "enabledI3AvailabilityZones": f"{{\"{REGION}\":[\"{DC_1}\",\"{DC_4}\",\"{DC_2}\"], \"{EREGION}\": [\"{EDC_0}\",\"{EDC_1}\",\"{EDC_2}\"]}}", 
                        "enabledM5AvailabilityZones": f"{{\"{REGION}\":[\"{DC_1}\",\"{DC_4}\",\"{DC_2}\"], \"{EREGION}\": [\"{EDC_0}\",\"{EDC_1}\",\"{EDC_2}\"]}}", 
                        "enabledR5AvailabilityZones": f"{{\"{REGION}\":[\"{DC_1}\",\"{DC_4}\",\"{DC_2}\"], \"{EREGION}\": [\"{EDC_0}\",\"{EDC_1}\",\"{EDC_2}\"]}}", 
                        "enabledI3ENMetalAvailabilityZones": f"{{\"{REGION}\":[\"{DC_1}\",\"{DC_4}\",\"{DC_2}\"], \"{EREGION}\": [\"{EDC_0}\",\"{EDC_1}\",\"{EDC_2}\"]}}",
                        "enableGssChat": "true",
                        "hostLimit": "32",
                        "maxClustersPerSDDC": "10",
                        "maxClustersPerSDDCMultiAz": "10",
                        "maxHostsPerSddc": "16",
                        "maxHostsPerSddcMultiAz": "28",
                        "maxHostsPerSddcOnCreateMultiAz": "28",
                        "maxHostsPerSddcOnCreate": "4",
                        "minHostsPerSddc": "2",
                        "minHostsPerSddcMultiAz": "2",
                        "sddcLimit": "2",
                        "sddcTypes": "1NODE,DEFAULT",
                        "sddcIndexForClusterName": "0"
                    }
                }
            }
        )
        return RESULT

    def org_show_details(self, target_org, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/orgs/{TARGET_ID}",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def show_oauth_managed_apps(self, target_org, auth_org='platform', user_profile='default', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        try:
            RESULT = curl.get(
                url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/clients",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                }
            )
            REDUCTION = {'id':None}
            CHK = reduce_json(RESULT['results'], REDUCTION)
            if CHK:
                if not raw:
                    RESULT = reduce_json(RESULT['results'], REDUCTION)
                    DATA.append(RESULT)
                else:
                    DATA.append(RESULT)
        except:
            return None
        return DATA

    def show_oauth_service_definition_id(self, target_org, auth_org='platform', user_profile='default', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        try:
            RESULT = curl.get(
                url=f"{CSP_URL}/csp/gateway/slc/api/v2/ui/definitions/?org_id={target_org}&locale=en_US",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                }
            )
            REDUCTION = {'serviceDefinitionId':None}
            CHK = reduce_json(RESULT['servicesList'], REDUCTION)
            if CHK:
                if not raw:
                    RESULT = reduce_json(RESULT['servicesList'], REDUCTION)
                    DATA.append(RESULT)
                else:
                    DATA.append(RESULT)
        except:
            return None
        return DATA

    def create_oauth_publisher_id(self, target_org, app_id, service_id, auth_org='platform', user_profile='default', raw=False):

        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        JSON = {
                "clientID": f"{app_id}",
                "orgID": f"{target_org}",
                "role": "service-owner"
        }

        RESULT = curl.post(
            url=f"{CSP_URL}/csp/gateway/po/api/v1/publishers",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson=JSON
        )
        return RESULT

    def create_oauth_app(self, target_org, app_id, secret, auth_org='platform', user_profile='default'):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        JSON = {
            "id": f"{app_id}-prd-gov",
            "accessTokenTTL": 1800,
            "allowedScopes": {
                "allRoles": "False",
                "generalScopes": [],
                "organizationScopes": {
                    "roleNames": [
                        "org_member"
                    ]
                  },
                  "serviceScopes": []
            },
            "description": f"{app_id} micro service in prd-gov",
            "displayName": f"{app_id} service prd-gov",
            "secret": f"{secret}",
            "grantTypes": [
                "client_credentials"
            ]
        }
        RESULT = curl.post(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/oauth-apps",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson=JSON
        )
        return RESULT

    def add_oauth_app_to_org(self, target_org, app_id, auth_org='platform', user_profile='default'):
        app_id = f"{app_id}-prd-gov"
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        JSON = {
                "ids": [app_id],
                "organizationRoles": [{"name":"org_member"}],
                "serviceRoles": []
        }
        RESULT = curl.post(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/clients",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson=JSON
        )
        return RESULT

    def delete_oauth_app(self, target_org, app_id, auth_org='platform', user_profile='default'):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.delete(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/oauth-apps",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                 "clientIdsToDelete": [ app_id ]
            }
        )
        return RESULT

    def patch_oauth_app(self, target_org, app_id, service_id, auth_org='platform', user_profile='default'):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        JSON = {
             "organizationRoles":
                 {
                     "rolesToAdd": [
                         {
                             "name": "org_member"
                         }
                     ]
                 },
                 "serviceRoles": [
                     {
                         "serviceDefinitionId": f"{service_id}",
                         "rolesToAdd": [
                             {
                                 "name": "vmc-operator:rw"
                             },
                             {
                                 "name":"vmc-operator:feature-flag-rw"
                             },
                             {
                                 "name": "vmc-user:full"
                             }
                         ]
                     }
                 ]
        }
        try:
            RESULT = curl.patch(
                url=f"{CSP_URL}/csp/gateway/am/api/clients/{app_id}/orgs/{target_org}/roles",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                },
                rjson=JSON
            )
        except:
            try:
                RESULT = curl.post(
                    url=f"{CSP_URL}/csp/gateway/am/api/clients/{app_id}/orgs/{target_org}/roles",
                    headers={
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'csp-auth-token': ACCESS_TOKEN
                    },
                    rjson=JSON
                )
            except:
                return None
        return RESULT

    def show_oauth_details(self, target_org, app_id, auth_org='platform', user_profile='default', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        try:
            RESULT = curl.get(
                url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/oauth-apps/{app_id}",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                }
            )
            DATA.append(RESULT)
        except:
            return None
        return DATA

    def show_oauth_scopes(self, target_org, app_id, auth_org='platform', user_profile='default', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        try:
            RESULT = curl.get(
                url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/oauth-apps/{app_id}",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                }
            )
            if raw is False:
                REDUCTION = {'allowedScopes':None}
            else:
                DATA.append(RESULT)
                return DATA
            CHK = reduce_json(RESULT, REDUCTION)
            if CHK:
                if not raw:
                    RESULT = reduce_json(RESULT, REDUCTION)
                    DATA.append(RESULT)
                else:
                    DATA.append(RESULT)
            else:
                DATA.append(RESULT)
        except:
            return None
        return DATA

    def show_oauth_published_apps(self, auth_org='platform', user_profile='default', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        try:
            RESULT = curl.get(
                url=f"{CSP_URL}/csp/gateway/po/api/v1/publishers",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                }
            )
            if raw is False:
                REDUCTION = {'clientID':None,'publisherID':None,'orgID':None,'role':None}
            else:
                DATA.append(RESULT)
                return DATA
            CHK = reduce_json(RESULT, REDUCTION)
            if CHK:
                if not raw:
                    RESULT = reduce_json(RESULT, REDUCTION)
                    DATA.append(RESULT)
                else:
                    DATA.append(RESULT)
            else:
                DATA.append(RESULT)
        except:
            return None
        return DATA

    def show_oauth_roles(self, target_org, app_id, auth_org='platform', user_profile='default', raw=False, org_roles=False, service_roles=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        try:
            RESULT = curl.get(
                url=f"{CSP_URL}/csp/gateway/am/api/clients/{app_id}/orgs/{target_org}/roles",
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'csp-auth-token': ACCESS_TOKEN
                }
            )
            if org_roles is True:
                REDUCTION = {'organizationRoles':None}
            elif service_roles is True:
                REDUCTION = {'serviceRoles':None}
            else:
                DATA.append(RESULT)
                return DATA

            CHK = reduce_json(RESULT, REDUCTION)
            if CHK:
                if not raw:
                    RESULT = reduce_json(RESULT, REDUCTION)
                    DATA.append(RESULT)
                else:
                    DATA.append(RESULT)
            else:
                DATA.append(RESULT)
        except:
            return None
        return DATA
    
    def show_oauth_apps(self, target_org, auth_org='platform', user_profile='default', raw=False):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        P = 0
        DATA = []
        while True:
            try:
                RESULT = curl.get(
                    url=f"{CSP_URL}/csp/gateway/am/api/orgs/{target_org}/oauth-apps?pageStart={P}&pageLimit=15",
                    headers={
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'csp-auth-token': ACCESS_TOKEN
                    }
                )
                REDUCTION = {'id':None}
                CHK = reduce_json(RESULT['results'], REDUCTION)
                if CHK:
                    if not raw:
                        RESULT = reduce_json(RESULT['results'], REDUCTION)
                        DATA.append(RESULT)
                    else:
                        DATA.append(RESULT)
                    P = P + 15
                    continue
                else:
                    break
            except:
                break
        return DATA

    def org_show_sddcs(self, target_org, aws_ready=False, version=False, auth_org='operator', user_profile='default', raw=False):
        TARGET_ID = target_org
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/orgs/{TARGET_ID}/sddcs",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = { 'name':None, 'created':None, 'version':['resource_config','sddc_manifest','vmc_internal_version'], 'id': None,
                        'org_id':None, 'provider': None, 'region':['resource_config', 'region'], 'user_name': None, 'sddc_state': None}
            RESULT = reduce_json(RESULT, REDUCTION)
        if aws_ready:
            FILTERED_RESULT = []
            for SDDC in RESULT:
                if SDDC['sddc_state'] == 'READY' and 'provider' == 'AWS':
                    FILTERED_RESULT.append(SDDC)
            RESULT = FILTERED_RESULT
        if version:
            REDUCTION = { 'id': None, 'version':None }
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT

    def org_show_sddc(self, target_org, sddc_id, auth_org='operator', user_profile='default', raw=False):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/orgs/{TARGET_ID}/sddcs/{sddc_id}",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = { 'name':None, 'created':None, 'version':['resource_config','sddc_manifest','vmc_internal_version'], 'id': None,
                        'org_id':None, 'provider': None, 'region':['resource_config', 'region'], 'user_name': None, 'sddc_state': None}
            RESULT = reduce_json(RESULT, REDUCTION)
        return RESULT

    def org_task_list(self, target_org, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        VMC_URL = self.get_vmc_api_url(user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/orgs/{TARGET_ID}/tasks",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def org_show_task_details(self, task_id, target_org, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/orgs/{TARGET_ID}/tasks/{task_id}",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def org_show_task_summary(self, target_org, auth_org='operator', user_profile='default'):
        TARGET_ID, AUTH_ID = self.get_org_ids(user_profile, target_org, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/tasks/summary",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def user_list_details(self, user_name, auth_org='platform', user_profile='default'):
        AUTH_ID = auth_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{CSP_URL}/csp/gateway/am/api/users/{user_name}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )
        return RESULT

    def user_list_orgs(self, user_name, auth_org='operator', user_profile='default'):
        csp_user_name = self.get_csp_user_name(user_name.split('@')[0], auth_org, user_profile)
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{CSP_URL}/csp/gateway/am/api/users/{csp_user_name}/orgs",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )
        REDUCTION = {'refLinks':None}
        CHK = reduce_json(RESULT, REDUCTION)
        if CHK['refLinks'] != '':
            return RESULT['refLinks']
        else:
            return None

    def org_add_user(self, user_name, user_role, target_org, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ID = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.post(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs/{TARGET_ID}/invitations",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "orgRoleNames": [ user_role ],
                "usernames": [ user_name ]
            }
        )
        return RESULT

    def org_remove_user(self, user_name, target_org, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ID = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.delete(
            url=f"{CSP_URL}/csp/gateway/am/api/orgs/{TARGET_ID}/users",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                 "users": [ { "username": user_name } ]
            }
        )
        return RESULT

    def org_user_role_change(self, user_name, target_org, current_role, new_role, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ID = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.patch(
            url=f"{CSP_URL}/csp/gateway/am/api/users/{user_name}/orgs/{TARGET_ID}/roles",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "roleNamesToAdd": [ new_role ],
                "roleNamesToRemove": [ current_role ]
            }
        )
        return RESULT

    def org_user_to_admin(self, service_id, user_name, target_org, user_role, auth_org='platform', user_profile='default'):
        CSP_SERVICEID = service_id
        os.environ = env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=True)
        CONFIG = Config('csptools')
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ID = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        if user_role == 'operator-sre':
            JSON = {
                "serviceDefinitionLink": f"/csp/gateway/slc/api/definitions/external/{CSP_SERVICEID}",
                "roleNamesToAdd": [
                    "nsx:cloud_auditor",
                    "nsx:cloud_admin",
                    "vmc-user:full",
                    "vmc-operator:config-ro",
                    "vmc-operator:config-rw",
                    "vmc-operator:da-rw",
                    "vmc-operator:brs-admin",
                    "vmc-operator:monitoring-rw",
                    "vmc-operator:org-rw",
                    "vmc-operator:rce-admin",
                    "vmc-operator:ro",
                    "vmc-operator:rts-ro",
                    "vmc-operator:rts-rw",
                    "vmc-operator:rts-sensitive",
                    "vmc-operator:rw",
                    "vmc-operator:sensitive",
                    "vmc-pop:sddc-rw",
                    "vmc-pop:sddc-scoped-access"
                ]
            }
        elif user_role == 'operator-ro':
            JSON = {
                "serviceDefinitionLink": f"/csp/gateway/slc/api/definitions/external/{CSP_SERVICEID}",
                "roleNamesToAdd": [
                    "vmc-operator:da-ro",
                    "nsx:cloud_auditor",
                    "vmc-operator:ro"
                ]
            }
        else:
            JSON = {
                "serviceDefinitionLink": f"/csp/gateway/slc/api/definitions/external/{CSP_SERVICEID}",
                "roleNamesToAdd": [
                    "vmc-user:full",
                    "nsx:cloud_auditor",
                    "nsx:cloud_admin"
                ]
            }
        RESULT = curl.patch(
            url=f"{CSP_URL}/csp/gateway/am/api/users/{user_name}/orgs/{TARGET_ID}/service-roles",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson=JSON
        )
        return RESULT

    def user_list_roles(self, user_name, target_org, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ID = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{CSP_URL}/csp/gateway/am/api/users/{user_name}/orgs/{TARGET_ID}/roles",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def user_list_service_roles(self, user_name, target_org, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ID = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{CSP_URL}/csp/gateway/am/api/users/{user_name}/orgs/{TARGET_ID}/service-roles",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def show_all_features(self, raw=False, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/features",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            REDUCTION = { 'id':None, 'description':None, 'enable':None, 'toggle_type':None, 'type':None, 'category':None, 'namespace':None, 'state':None }
            RESULT = reduce_json(RESULT, REDUCTION, True)
        return RESULT

    def show_all_properties(self, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{VMC_URL}/vmc/api/operator/orgs/properties",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        return RESULT

    def show_registrations(self, filter_definition, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        DATA = []
        RESULT = curl.get(
            url=f'{CSP_URL}/csp/gateway/am/api/idp-registrations',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )
        if filter_definition is not None:
            REDUCTION = {f'{filter_definition}':None}
            CHK = reduce_json(RESULT, REDUCTION)
            if CHK:
                RESULT = reduce_json(RESULT, REDUCTION)
                DATA.append(RESULT)
            else:
                DATA.append(RESULT)
        else:
            DATA.append(RESULT)
        return DATA

    def show_all_users(self, target_org, raw=False, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ORG = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f"{CSP_URL}/csp/gateway/am/api/v2/orgs/{TARGET_ORG}/users",
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )
        if not raw:
            try:
                REDUCTION = { 'firstName': ['user','firstName'], 'lastName': ['user','lastName'], 'username': ['user','username'], 'email': ['user','email'], 'domain': ['user','domain'], 'roles': ['organizationRoles'] }
                RESULT = reduce_json(RESULT['results'], REDUCTION)
            except:
                return None
        return RESULT

    def show_org_account(self, target_org, auth_org, user_profile, raw):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ORG = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f'{VMC_URL}/vmc/api/orgs/{TARGET_ORG}/aws',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            }
        )
        if not raw:
            try:
                RESULT = RESULT['aws_account_number']
            except:
                RESULT = None
        return RESULT

    def show_org_activities(self, target_org, auth_org, user_profile, raw):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        TARGET_ORG = target_org
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        RESULT = curl.get(
            url=f'{VMC_URL}/vmc/activity/api/operator/activities',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            }
        )
        return RESULT

    def user_search(self, search_term, auth_org='platform', user_profile='default'):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        return curl.post(
            url=f'{CSP_URL}/csp/gateway/am/api/v2/users/search',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
            rjson={
                "searchTerm": search_term
            }
        )

    def get_user_id(self, username, auth_org='platform', user_profile='default'):
        RESPONSE = self.user_search(username, auth_org, user_profile)
        if RESPONSE['totalResults'] == 0:
            return None
        elif RESPONSE['totalResults'] == 1:
            return RESPONSE['results'][0]['userId']
        else:
            Log.info('multiple users found')
            for i in range(len(RESPONSE['results'])):
                print(f'{i+1} | {RESPONSE["results"][i]["username"]}')
            while True:
                CHOICE = int(input('input the number representing the user you wish to look-up: '))
                if CHOICE <= len(RESPONSE['results']) or CHOICE >= 1:
                    break
            return RESPONSE['results'][CHOICE]['userId']

    def get_csp_user_name(self, username, auth_org='platform', user_profile='default'):
        RESPONSE = self.user_search(username, auth_org, user_profile)
        if RESPONSE['totalResults'] == 0:
            return None
        elif RESPONSE['totalResults'] == 1:
            return RESPONSE['results'][0]['username']
        else:
            Log.info('multiple users found')
            for i in range(len(RESPONSE['results'])):
                print(f'{i+1} | {RESPONSE["results"][i]["username"]}')
            while True:
                CHOICE = int(input('input the number representing the user you wish to look-up: '))
                if CHOICE <= len(RESPONSE['results']) or CHOICE >= 1:
                    break
            return RESPONSE['results'][CHOICE]['username']

    def get_user_sessions(self, user_id, auth_org, user_profile):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        ACTIVE_SESSIONS = curl.get(
            url=f'{CSP_URL}/csp/gateway/am/api/v2/users/{user_id}/active-sessions',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            }
        )
        MAX_SESSIONS = curl.get(
            url=f'{CSP_URL}/csp/gateway/am/api/v2/users/{user_id}?expandProfile',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            }
        )
        return MAX_SESSIONS, ACTIVE_SESSIONS

    def delete_user_session(self, session_id, auth_org, user_profile):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        return curl.delete(
            url=f'{CSP_URL}/csp/gateway/am/api/users/sessions/{session_id}',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            }
        )

    def user_session_limit(self, user_id, new_limit, auth_org, user_profile):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        return curl.post(
            url=f'{CSP_URL}/csp/gateway/am/api/users/{user_id}/session-limit',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
            rjson={
                "sessionLimit": int(new_limit)
            }
        )

    def get_csp_org_name(self, org_id, auth_org, user_profile):
        AUTH_ID = self.get_org_ids(user_profile, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.get_access_details(AUTH_ID, user_profile)
        return curl.get(
            url=f'{CSP_URL}/csp/gateway/am/api/orgs/{org_id}',
            headers={
                "Content-Type": "application/json",
                "csp-auth-token": ACCESS_TOKEN
            },
        )

    def get_org_ids(self, user_profile, *args):
        IDS = []
        for org in args:
            ID = self.find_org_id(org, user_profile)
            if ID is None:
                ID = org
            IDS.append(ID)
        if len(IDS) == 1:
            return IDS[0]
        elif len(IDS) > 1:
            return IDS
        else:
            return None
