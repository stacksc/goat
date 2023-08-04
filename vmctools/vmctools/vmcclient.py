import uuid, json
from configstore.configstore import Config
from csptools.cspclient import CSPclient
from toolbox.jsontools import reduce_json
from toolbox.logger import Log
from toolbox import curl2
from os import getpid

class vmc():

    def __init__(self, auth, user_profile):
        self.CSP = CSPclient()
        self.AUTH_ID = auth
        self.USER_PROFILE = user_profile
        self.CONFIG = Config('vmctools')
        if self.USER_PROFILE not in self.CONFIG.PROFILES:
            self.CONFIG.create_profile(user_profile)
        self.ACCESS_TOKEN, self.CSP_URL, self.VMC_URL = self.CSP.get_access_details(self.AUTH_ID, self.USER_PROFILE)
        self.WEST_REGION = self.CONFIG.get_metadata('region_west', self.USER_PROFILE)
        self.EAST_REGION = self.CONFIG.get_metadata('region_east', self.USER_PROFILE)

    def sddc_create(self, target_org, sddc_name, host_num='1', provider='AWS', account=None, net_cus=None, net_vpc='10.2.0.0/16', 
                    sddc_type='1NODE', deployment_type='SingleAZ', sddc_size='MEDIUM', host_type='i3.metal', region='west'):
        ORG_ID = target_org
        REGION_ID = self.get_region_id(region)
        REGION_ID = 'GovCloud'
        LINKED_MODE = False
        ORG_PROPERTIES = self.CSP.org_property_list(ORG_ID, auth_org='operator', user_profile=self.USER_PROFILE)
        try:
            if ORG_PROPERTIES[0]['values']['accountLinkingOptional'] == 'false':
                Log.info('deploying in an org with linked AWS account')
                if account is None:
                    Log.critical('aws account is required in this mode')
                if net_cus is None:
                    Log.critical('customer network is required in this mode')
                LINKED_MODE = True
            else:
                LINKED_MODE = False
        except KeyError:
            Log.critical('unable to get accountLinkingOptional value from org properties')
        JSON = self.get_sddc_deploy_json(LINKED_MODE, sddc_name, host_num, provider, account, net_cus, net_vpc, sddc_type, deployment_type, sddc_size, host_type, REGION_ID)
        Log.json(json.dumps(JSON, indent=2))
        RESULT = curl2.post(
            url=f"{self.VMC_URL}/vmc/api/orgs/{ORG_ID}/sddcs",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            json=JSON
        ).json
        return RESULT

    def get_region_id(self,region):
        if region == 'west':
            if self.WEST_REGION is None:
                self.WEST_REGION = self.CONFIG.get_var('region_west', 'metadata', 'REGION', self.USER_PROFILE)
            REGION = self.WEST_REGION
        if region == 'east':
            if self.EAST_REGION is None:
                self.EAST_REGION = self.CONFIG.get_var('region_east', 'metadata', 'EREGION', self.USER_PROFILE)
            REGION = self.EAST_REGION
        return REGION

    def get_org_id(self, target_org):
        ORG_ID = self.CSP.find_org_id(target_org)
        if ORG_ID is None: # if target_org was already an ID then find_org_id would return None
            ORG_ID = target_org
        return ORG_ID

    def get_sddc_deploy_json(self, mode, sddc_name, host_num, provider, account, net_cus, net_vpc, sddc_type, deployment_type, sddc_size, host_type, region):
        if mode is True:
            JSON = {
                "num_hosts": host_num,
                "name": sddc_name,
                "provider": provider,
                "skip_creating_vxlan": 'false',
                "vpc_cidr": net_vpc,
                "sddc_type": sddc_type,
                "one_node_reduced_capacity": 'false',
                "account_link_sddc_config": [{
                    "connected_account_id": account,
                    "customer_subnet_ids": [ net_cus ]
                }],
                "deployment_type": deployment_type,
                "storage_capacity": 0,
                "size": sddc_size,
                "host_instance_type": host_type,
                "region": region
            }
        else:
            JSON = {
                "num_hosts": host_num,
                "name": sddc_name,
                "provider": provider,
                "skip_creating_vxlan": 'false',
                "vpc_cidr": net_vpc,
                "sddc_type": sddc_type,
                "one_node_reduced_capacity": 'false',
                "deployment_type": deployment_type,
                "storage_capacity": 0,
                "size": sddc_size,
                "host_instance_type": host_type,
                "region": region
            }
        return JSON

    def org_sddc_delete(self, target_org, sddc_id, force=False, raw=False):
        ORG_ID = target_org
        SDDC_FACTS = self.CSP.org_show_sddc(target_org, sddc_id, 'operator', user_profile=self.USER_PROFILE)
        if ORG_ID != SDDC_FACTS['org_id'] or sddc_id != SDDC_FACTS['id']:
            Log.critical('org_id and sddc_id dont match; please verify if you entered the right IDs')
        URL = f"{self.VMC_URL}/vmc/api/orgs/{target_org}/sddcs/{sddc_id}"
        if force:
            URL = URL + "?force=true"
        RESULT =  curl2.delete(
            url=URL,
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        if not raw:
            REDUCE = { 'created':None, 'org_id':None, 'sddc_id':['params','SDDC_DELETE_CONTEXT_PARAM',sddc_id], 'task_type':None, 'error_code':None, 'error_messages':None }
            RESULT =  reduce_json(RESULT, REDUCE)
        return RESULT

    def account_delete(self, aws_account_id):
        AWS_ACCOUNTS=curl2.get(
            url=f"{self.VMC_URL}/vmc/api/operator/aws",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        ASSOCIATED_ORG = None
        for AWS_ACCOUNT in AWS_ACCOUNTS:
            if 'aws_account_number' in AWS_ACCOUNT and 'aws_account_state' in AWS_ACCOUNT:
                if AWS_ACCOUNT['id'] == aws_account_id and AWS_ACCOUNT['aws_account_state'] == 'ACTIVE':
                    ASSOCIATED_ORG = AWS_ACCOUNT['org_id']
        if ASSOCIATED_ORG is None:
            Log.critical(f'an active account for id {aws_account_id} was not found')
        self.account_disassociate(aws_account_id, ASSOCIATED_ORG)
        return curl2.delete(
            url=f"{self.VMC_URL}/vmc/api/operator/aws/{aws_account_id}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        )

    def console_notification(self, expireDate, sddc_id, org_id, username):
        uid = uuid.uuid1()
        client_event_id = username + "-" + str(uid)

        JSON = {"tenant_id": org_id,
                "client_event_id": client_event_id,
                "command": "NG:SEND-NOTIFICATION",
                "expiry_date": expireDate,
                "notification_type": "TestVmcConsole::AppBanner",
                "resource_id": sddc_id,
                "resource_type": "SDDC",
                "payload": {
                    "test_id": client_event_id,
                    "test_name": "prod-push-sanity-check",
                    "__ngw_channel": ["VmcConsole"]
                    }
        }
        RESULT = curl2.post(
            url=f"{self.VMC_URL}/vmc/ng/api/operator/orgs/notifications/requests",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            json=JSON
        ).json['task_id']
        return RESULT

    def console_notify_task_verify(self, task_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/ng/api/operator/history/notifications?$filter=payload/__ngw_taskId%20eq%20'{task_id}'",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        return RESULT

    def account_associate_ctrl(self, action, aws_account_id, org_id, raw=False):
        if action == 'associate' or action =='disassociate':
            RESULT = curl2.post(
                url=f"{self.VMC_URL}/vmc/api/operator/aws/{aws_account_id}?action={action}&orgId={org_id}",
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.ACCESS_TOKEN
                }
            ).json
        else:
            Log.critical(f'vmcclient.account_associate_ctrl: incorrect action: {action}')
        if not raw:
            REDUCT = { 'org_id':None, 'aws_account_number':None, 'id':None, 'payer_account_type':None, 'nitro_region_az_mapping':None }
            RESULT = reduce_json(RESULT, REDUCT)
        return RESULT

    def account_associate(self, aws_account_id, org_id, raw=False):
        return self.account_associate_ctrl('associate', aws_account_id, org_id, raw)

    def account_disassociate(self, aws_account_id, org_id, raw=False):
        return self.account_associate_ctrl('disassociate', aws_account_id, org_id, raw)

    def account_import(self, aws_account_number, daily_org, payer_account_type, role_arn):
        DAILY_ORG_ID = self.CSP.get_org_ids(self.USER_PROFILE, daily_org)
        IMPORTED_ACCOUNT_ID = curl2.post(
            url=f"{self.VMC_URL}/vmc/api/operator/aws",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            json={
                "assume_role_arn": {role_arn},
                "aws_account_number": {aws_account_number}
            }
        ).json['id']
        curl2.post(  # associates imported account with the daily org id
            url=f"{self.VMC_URL}/vmc/api/operator/aws/{IMPORTED_ACCOUNT_ID}?action=Associate&orgId={DAILY_ORG_ID}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        )
        VMC_WEST = self.CONFIG.get_var('vmc_west', 'metadata', 'REGION', self.USER_PROFILE)
        VMC_WEST_DC1 = self.CONFIG.get_var('vmc_west_dc1', 'metadata', 'DC_1', self.USER_PROFILE)
        VMC_WEST_DC2 = self.CONFIG.get_var('vmc_west_dc2', 'metadata', 'DC_2', self.USER_PROFILE)
        VMC_WEST_DC4 = self.CONFIG.get_var('vmc_west_dc4', 'metadata', 'DC_4', self.USER_PROFILE)
        PATCHED_ACCOUNT = curl2.patch(
            url=f"{self.VMC_URL}/vmc/api/operator/aws/{IMPORTED_ACCOUNT_ID}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            json={
                "nitro_region_az_mapping": {
                    VMC_WEST: {
                        VMC_WEST_DC4: f"{VMC_WEST}c",
                        VMC_WEST_DC1: f"{VMC_WEST}b",
                        VMC_WEST_DC2: f"{VMC_WEST}a"
                    }
                },
                "payer_account_type": payer_account_type
            }
        )
        return # TBD: self.account_show_details(IMPORTED_ACCOUNT_ID)

    def account_show_details(self, aws_account_id, raw):
        AWS_ACCOUNT_DETAILS = curl2.get(
            url=f"{self.VMC_URL}/vmc/api/operator/aws/{aws_account_id}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        if not raw:
            REDUCE = { 'created':None, 'aws_account_number':None, 'id':None, 'org_id':None, 'aws_account_state':None, 'payer_account_type':None, 'nitro_region_az_mapping':None }
            AWS_ACCOUNT_DETAILS = reduce_json(AWS_ACCOUNT_DETAILS, REDUCE)
        AWS_ACCOUNT_NUMBER = AWS_ACCOUNT_DETAILS['aws_account_number']
        # TBD:
        #AZS = _aws_account_az_id AWS_ACCOUNT_NUMBER
        #ZONE_A = _aws_account_az_id $AZ_A AZS
        #ZONE_B = _aws_account_az_id $AZ_B AZS
        #ZONE_C = _aws_account_az_id $AZ_C AZS
        # echo $OUTPUT | sed -e s/$AZ_A/$ZONE_A/ -e s/$AZ_B/$ZONE_B/ -e s/$AZ_C/$ZONE_C/ | jq '.'
        
    def _aws_account_az_id(self, aws_account_number):
        SDDC_ROLE = self.CONFIG.get_var('sddc_role_arn', 'config', 'SDDC_ROLE', self.USER_PROFILE)
        POWERUSER_ROLE=f"arn:aws-us-gov:iam::{aws_account_number}:role/PowerUser"  
        SDDC_SESSION=f"sddc-crtl-{getpid()}"
        POWERUSER_SESSION=f"poweruser-{getpid()}"
        # TBD: _aws_account_assume_role $SDDC_ROLE $SDDC_SESSION $REGION
        # TBD: _aws_account_assume_role $POWERUSER_ROLE $POWERUSER_SESSION $REGION
        # TBD: aws ec2 describe-availability-zones  --region $REGION | jq -r '.AvailabilityZones[] | "\(.ZoneName)(\(.ZoneId))"'
        # TBD: unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN

    def account_show_all(self, account_state, numbers_only, raw):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/api/operator/aws",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        if not raw:
            if not numbers_only:
                REDUCE = { 'created':None, 'aws_account_number':None, 'id':None, 'org_id':None, 'aws_account_state':None, 'payer_account_type':None }
            else:
                REDUCE = { 'aws_account_number':None, 'aws_account_state':None }
            RESULT = reduce_json(RESULT, REDUCE)
            if account_state is not None:
                FILTERED_RESULT = []
                for ACCOUNT in RESULT:
                    if ACCOUNT['aws_account_state'] == account_state:
                        FILTERED_RESULT.append(ACCOUNT)
                RESULT = FILTERED_RESULT
        return RESULT

    def show_sddc_details(self, sddc_id, raw=False):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/api/operator/sddcs/{sddc_id}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        if not raw:
            REDUCE = { 'name':None, 'created':None, 'version': ['resource_config','sddc_manifest','vmc_internal_version'], 'id':None, 
                        'org_id':None, 'provider':None, 'region':['resource_config','region'], 'user_name':None, 'sddc_state':None }
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def show_sddc_all(self, pattern, state, aws_ready=False, raw=False):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/api/operator/sddcs",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        ).json
        if not raw:
            REDUCE = { 'name':None, 'created':None, 'version': ['resource_config','sddc_manifest','vmc_internal_version'], 'id':None, 
                        'org_id':None, 'provider':None, 'region':['resource_config','region'], 'user_name':None, 'sddc_state':None }
            RESULT = reduce_json(RESULT, REDUCE)
            if aws_ready:
                FILTERED = []
                for SDDC in RESULT:
                    if SDDC['provider'] == 'AWS' and SDDC['sddc_state'] == 'READY':
                        FILTERED.append(SDDC)
                RESULT = FILTERED
            if pattern:
                FILTERED = []
                for SDDC in RESULT:
                    if pattern in SDDC['name']:
                        FILTERED.append(SDDC)
                RESULT = FILTERED
            if state:
                FILTERED = []
                for SDDC in RESULT:
                    if SDDC['sddc_state'] == state:
                        FILTERED.append(SDDC)
                RESULT = FILTERED
        return RESULT

    def draas_prepare_deactivate(self, org_id, sddc_id):
        JSON = { "ticket": "CSCM-12345", "intention": "Push to prod Deactivate DR validation by operator" }
        RESULT = curl2.post(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/prepare-for-deactivate",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            json=JSON,
            expected_codes=[202, 200, 400, 403]
        )
        return RESULT.status_code

    def draas_activate(self, org_id, sddc_id):
        RESULT = curl2.post(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[202, 200, 400, 403]
        )
        return RESULT.status_code

    def draas_deactivate(self, org_id, sddc_id, confirm_code, ticket="CSCM-12345"):
        JSON = { "force": "false", "ticket": ticket, "confirmation_code": confirm_code }
        RESULT = curl2.delete(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            json=JSON,
            expected_codes=[202, 200, 400, 403]
        )
        return RESULT.status_code

    def draas_show_task_details(self, org_id, task_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/tasks/{task_id}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[202, 200, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_hms_tasks_info(self, org_id, sddc_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/hms-tasks-info",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[200, 202, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_plan(self, org_id, sddc_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/recovery-plans-info",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[200, 202, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_get_support_bundle(self, org_id, task_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/support-bundle/{task_id}/download",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[200, 202, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_pairings(self, org_id, sddc_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/pairings",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[200, 202, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_tasks(self, org_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/tasks",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[202, 200, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_details(self, sddc_id, org_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[202, 200, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_versions(self, sddc_id, org_id):
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/versions",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[202, 200, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def draas_show_permissions(self, sddc_id, org_id):
        RESULT = curl2.post(
            url=f"{self.VMC_URL}/vmc/draas/api/orgs/{org_id}/sddcs/{sddc_id}/site-recovery/permissions",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            },
            expected_codes=[202, 200, 400, 403]
        )
        if RESULT:
            return RESULT
        return None

    def pop_show_all(self, sddc_id, org_id):
        DATA = []
        RESULT = curl2.get(
            url=f"{self.VMC_URL}/vmc/api/orgs/{org_id}/delegated-access/pop/sddcs/{sddc_id}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        )
        if RESULT:
            DATA.append(RESULT)
        return DATA

    def pop_request(self, sddc_id, org_id, reason='testing. please ignore', token_access=False):
        if not token_access:
            return curl2.post(
                url=f"{self.VMC_URL}/vmc/api/orgs/{org_id}/delegated-access/pop/sddcs/{sddc_id}",
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.ACCESS_TOKEN
                },
                json={
                    'reason': reason
                },
                expected_codes=[200, 400, 403]
            )
        else:
            return curl2.post(
                url=f"{self.VMC_URL}/vmc/api/orgs/{org_id}/delegated-access/token/ssh",
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.ACCESS_TOKEN
                },
                json={
                    'delegated_access_token': self.ACCESS_TOKEN
                },
                expected_codes=[200, 400, 403]
            )

