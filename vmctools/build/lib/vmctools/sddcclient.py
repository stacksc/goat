from os import environ
from .vmcclient import vmc
from toolbox import curl
from .vmc_rts import rts
from toolbox.jsontools import reduce_json
from toolbox.logger import Log

class sddc():
    
    def __init__(self, sddc_id, auth, user_profile, host_org=None):
        self.ID = sddc_id
        if host_org is not None:
            print(host_org)
            self.ORG = vmc.get_org_id(host_org)
        self.VMC = vmc(auth, user_profile)

    def show_sddc(self):
        return curl.get(
            url = f"{self.VMC.VMC_URL}/vmc/api/operator/sddcs/{self.ID}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.VMC.ACCESS_TOKEN
            }
        )

    def esx_show_names(self):
        SDDC = self.show_sddc()
        RESULT = []
        CLUSTERS = SDDC['resource_config']['clusters']
        for CLUSTER in CLUSTERS:
            CLUSTER_HOSTS = CLUSTER['esx_host_list']
            for HOST in CLUSTER_HOSTS:
                REDUCE = { 'name':None }
                HOST = reduce_json(HOST, REDUCE)
                RESULT.append(HOST)
        return RESULT

    def nsx_show_names(self):
        SDDC = self.show_sddc()
        RESULT = []
        CLUSTERS = SDDC['resource_config']
        REDUCE = {'nsx_controller_ips':None}
        DATA = reduce_json(CLUSTERS, REDUCE)
        return DATA

    def esx_show_all(self, raw):
        SDDC = self.show_sddc()
        if not raw:
            ID = SDDC['id']
            NAME = SDDC['name']
            RESULT = {'id': ID, 'name': NAME}
            CLUSTERS = SDDC['resource_config']['clusters']
            RESULT['hosts'] = []
            for CLUSTER in CLUSTERS:
                CLUSTER_HOSTS = CLUSTER['esx_host_list']
                for HOST in CLUSTER_HOSTS:
                    SUBNETS = []
                    REDUCE = { 'name':None,'hostname':None,'provider':None,'esx_state':None,'availability_zone':None,'instance_id':None }
                    HOST = reduce_json(HOST, REDUCE)
                    try:
                        for ITEM in HOST['eni_list']:
                            SUBNETS.append(ITEM['subnet_id'])
                        HOST['subnets'] = SUBNETS
                    except:
                        pass
                    RESULT['hosts'].append(HOST)
        else:
            RESULT = SDDC['resource_config']['clusters']
        return RESULT

    def esx_show_details(self, esx_name, raw):
        CLUSTERS = self.esx_show_all(True)
        for CLUSTER in CLUSTERS:
            CLUSTER_HOSTS = CLUSTER['esx_host_list']
            for HOST in CLUSTER_HOSTS:
                if HOST['name'] == esx_name:
                    if not raw:
                        SUBNETS = []
                        try:
                            for ITEM in HOST['eni_list']:
                                SUBNETS.append(ITEM['subnet_id'])
                            REDUCE = { 'name':None,'hostname':None,'provider':None,'esx_state':None,'availability_zone':None,'instance_id':None }
                            HOST = reduce_json(HOST, REDUCE)
                            HOST['subnets'] = SUBNETS
                        except:
                            pass
                        return HOST
                    else:
                        return HOST
        return CLUSTERS            

    def nsx_show_credentials(self):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_mgr_url':None, 'nsx_mgr_management_ip':None, 'nsx_controller_ips':None, 'nsx_manager_username':None, 'nsx_manager_password':None, 'root_nsx_controller_password':None, 'root_nsx_edge_password':None}
        DATA = reduce_json(SDDC['resource_config'], REDUCE)
        RESULT['nsx'].append(DATA)
        return RESULT

    def nsx_show_all(self, raw):
        SDDC = self.show_sddc()
        RESULT = {}
        for DATA in SDDC['resource_config']:
            if 'nsx' in DATA:
                RESULT[DATA] = SDDC['resource_config'][DATA]
        return RESULT

    def nsx_status(self, reason, raw):
        DATA = {"requestBody":f"scriptId:nsx_edge_status,sddc-id:{self.ID},edge:nsxt_edges,reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'status':None, 'data':['params','SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT


    def nsx_cluster_status(self, raw):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_api_public_endpoint_url':None}
        try:
            DATA = reduce_json(SDDC['resource_config'], REDUCE)
        except:
            return RESULT
        RESULT['nsx'].append(DATA)
        NSX_ENDPOINT = SDDC['resource_config']['nsx_api_public_endpoint_url']
        RETURN = curl.get(
            url = f"{NSX_ENDPOINT}/api/v1/cluster/status",
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.VMC.ACCESS_TOKEN
            }
        )
        if RETURN:
            RESULT['nsx'].append(RETURN)
        return RESULT

    def nsx_policy_status(self, raw):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_api_public_endpoint_url':None}
        try:
            DATA = reduce_json(SDDC['resource_config'], REDUCE)
        except:
            return RESULT
        RESULT['nsx'].append(DATA)
        NSX_ENDPOINT = SDDC['resource_config']['nsx_api_public_endpoint_url']
        NSX_ENDPOINT = NSX_ENDPOINT.replace('sks-nsxt-manager','policy')

        JSON = {
                "primary": {
                    "resource_type": "BgpNeighborConfig"
                    },
                }

        RETURN = curl.post(
            url = f"{NSX_ENDPOINT}/api/v1/search/aggregate?page_size=250&cursor=0&sort_by=display_name&sort_ascending=true",
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.VMC.ACCESS_TOKEN
            },
            rjson=JSON
        )
        if RETURN:
            RESULT['nsx'].append(RETURN)
        return RESULT

    def nsx_node_status(self, raw):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_api_public_endpoint_url':None}
        try:
            DATA = reduce_json(SDDC['resource_config'], REDUCE)
        except:
            return RESULT
        RESULT['nsx'].append(DATA)
        NSX_ENDPOINT = SDDC['resource_config']['nsx_api_public_endpoint_url']
        RETURN = curl.get(
            url = f"{NSX_ENDPOINT}/api/v1/node/status",
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.VMC.ACCESS_TOKEN
            }
        )
        if RETURN:
            RESULT['nsx'].append(RETURN)
        return RESULT

    def nsx_vpn_sessions(self, raw):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_api_public_endpoint_url':None}
        try:
            DATA = reduce_json(SDDC['resource_config'], REDUCE)
        except:
            return RESULT
        RESULT['nsx'].append(DATA)
        NSX_ENDPOINT = SDDC['resource_config']['nsx_api_public_endpoint_url']
        try:
            RETURN = curl.get(
                url = f"{NSX_ENDPOINT}/api/v1/vpn/ipsec/sessions",
                headers = {
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                     'csp-auth-token': self.VMC.ACCESS_TOKEN
                }
            )
        except:
            return RESULT
        if RETURN:
            RESULT['nsx'].append(RETURN)
        return RESULT

    def nsx_vpn_endpoints(self, type, raw):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_api_public_endpoint_url':None}
        try:
            DATA = reduce_json(SDDC['resource_config'], REDUCE)
        except:
            return RESULT
        RESULT['nsx'].append(DATA)
        NSX_ENDPOINT = SDDC['resource_config']['nsx_api_public_endpoint_url']
        try:
            RETURN = curl.get(
                url = f"{NSX_ENDPOINT}/api/v1/vpn/ipsec/{type}-endpoints",
                headers = {
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                     'csp-auth-token': self.VMC.ACCESS_TOKEN
                }
            )
        except:
            return RESULT
        if type == 'local':
            if RETURN:
                RESULT['nsx'].append(RETURN)
        else:
            for I in RETURN['results']:
                ID = I['id']
                if not ID:
                    continue
                RETURN = curl.get(
                    url = f"{NSX_ENDPOINT}/api/v1/vpn/ipsec/{type}-endpoints/{ID}",
                    headers = {
                        'Content-type': 'application/json',
                        'Accept': 'application/json',
                        'csp-auth-token': self.VMC.ACCESS_TOKEN
                    }
                )
                RESULT['nsx'].append(RETURN)
        return RESULT

    def nsx_show_logical_routers(self, type, raw):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['nsx'] = []
        REDUCE = {'nsx_api_public_endpoint_url':None}
        DATA = reduce_json(SDDC['resource_config'], REDUCE)
        RESULT['nsx'].append(DATA)
        NSX_ENDPOINT = SDDC['resource_config']['nsx_api_public_endpoint_url']
        RETURN = curl.get(
            url = f"{NSX_ENDPOINT}/api/v1/logical-routers",
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.VMC.ACCESS_TOKEN
            }
        )
        if RETURN:
            REDUCE = {'router_type':None, 'id':None}
            DATA = reduce_json(RETURN['results'], REDUCE)
            for D in DATA:
                if D['router_type'] == type or type == 'ALL':
                    ID = D['id']
                    RETURN = curl.get(
                        url = f"{NSX_ENDPOINT}/api/v1/logical-routers/{ID}",
                        headers = {
                            'Content-type': 'application/json',
                            'Accept': 'application/json',
                            'csp-auth-token': self.VMC.ACCESS_TOKEN
                        }
                    )
                    RESULT['nsx'].append(RETURN)
        if RESULT['nsx']:
            return RESULT
        return RETURN

    def esx_show_credentials(self):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None}
        RESULT = reduce_json(SDDC, REDUCE)
        RESULT['hosts'] = []
        for HOST in SDDC['resource_config']['esx_hosts']:
            REDUCE = { 'name':None, 'hostname':None }
            HOST = reduce_json(HOST, REDUCE)
            HOST['esx_credential'] = []
            for AGENT in SDDC['resource_config']['agents']:
                REDUCE = { 'key_pair':['key_pair', 'key_material'] }
                KEY_PAIR = reduce_json(AGENT, REDUCE)
                HOST['esx_credential'].append(KEY_PAIR)
            if len(HOST['esx_credential']) == 1:
                HOST['esx_credential'] = HOST['esx_credential'][0]
            RESULT['hosts'].append(HOST)
        return RESULT

    def esx_show_witness(self):
        CLUSTERS = self.esx_show_all(True)
        WITNESS_HOSTNAMES= []
        for CLUSTER in CLUSTERS:
            if 'vsan_witness' in CLUSTER:
                if CLUSTER['vsan_witness'] is not None:
                    WITNESS_HOSTNAMES.append(CLUSTER['vsan_witness']['hostname'])
                else:
                    WITNESS_HOSTNAMES.append("")
            else:
                WITNESS_HOSTNAMES.append("")
        if len (WITNESS_HOSTNAMES) == 1:
            WITNESS_HOSTNAMES = WITNESS_HOSTNAMES[0]
        return WITNESS_HOSTNAMES

    def nsx_show_active_edge(self, reason, raw=False):
        DATA = {"requestBody":f"scriptId:nsx.get_active_edges,sddc-id:{self.ID},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'data':['SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def nsx_show_standby_edge(self, reason, raw=False):
        DATA = {"requestBody":f"scriptId:nsx.get_standby_edges,sddc-id:{self.ID},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'data':['SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def nsx_show_node_details(self, reason, raw=False):
        DATA = {"requestBody":f"scriptId:nsx.workflow_get_details,sddc-id:{self.ID},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'data':['SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def nsx_show_vpn_info(self, reason, raw=False, vpn='L2'):
        script_id = 'nsx.workflow_get_vpn_info'
        DATA = {"requestBody":f"scriptId:{script_id},sddc-id:{self.ID},vpn_type:{vpn},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'status':None, 'data':['params','SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def nsx_ssh_toggle(self, node_type, action, reason, raw=False):
        script_id = 'nsxt_mgr_edge_controller_ssh_toggle'
        DATA = {"requestBody":f"scriptId:{script_id},sddc-id:{self.ID},node_type:{node_type},script_action:{action},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'status':None, 'data':['params','SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def nsx_maintenance(self, node_id, reason, mode, raw=False):
        if mode == 'enter':
            script_id = 'nsx.enter_transport_node_maintenance_mode'
        elif mode == 'exit':
            script_id = 'nsx.exit_transport_node_maintenance_mode'
        DATA = {"requestBody":f"scriptId:{script_id},sddc-id:{self.ID},node_id:{node_id},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        return RESULT

    def esx_ssh_toggle(self, esx_name, action, reason, raw=False):
        script_id = 'esx_ssh_toggle'
        DATA = {"requestBody":f"scriptId:{script_id},sddc-id:{self.ID},esx:{esx_name},action:{action},reason:{reason}"}
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'status':None, 'data':['params','SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return RESULT

    def vcenter_show_credentials(self):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None }
        RESULT = reduce_json(SDDC, REDUCE)
        CONFIG = SDDC['resource_config']
        RESULT = self._try_assign(CONFIG, RESULT, 'vc_url')
        RESULT = self._try_assign(CONFIG, RESULT, 'vc_management_ip')
        RESULT = self._try_assign(CONFIG, RESULT, 'admin_username')
        RESULT = self._try_assign(CONFIG, RESULT, 'admin_password')
        RESULT = self._try_assign(CONFIG, RESULT, 'vc_ssh_credential')
        return RESULT

    def vcenter_show_url(self):
        SDDC = self.show_sddc()
        REDUCE = { 'name':None, 'id':None }
        RESULT = reduce_json(SDDC, REDUCE)
        CONFIG = SDDC['resource_config']
        RESULT = self._try_assign(CONFIG, RESULT, 'vc_url')
        RESULT = self._try_assign(CONFIG, RESULT, 'vc_management_ip')
        RESULT = self._try_assign(CONFIG, RESULT, 'vc_public_ip')
        return RESULT

    def _try_assign(self, input, output, field):
        try:
            output[field] = input[field]
        except KeyError:
            output[field] = ""
        return output

    def vcenter_ui(self, reason, user, target_org):
        if user is None:
            VC_USER = environ['USER']
            ORG_ID = self.show_sddc()['org_id']
            OUTPUT = curl.post(
                url=f"{self.VMC.VMC_URL}/vmc/api/orgs/{ORG_ID}/delegated-access/vcenter/sddcs/{self.ID}",
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.VMC.ACCESS_TOKEN
                },
                rjson={
                    "reason": reason,
                    "user_type": "ROOT_ADMIN"
                }
            )
            if VC_USER not in OUTPUT:
                Log.warn('failed to get vCenter access')
                return []
            for x in range(0,10):
                RESULT = curl.get(
                    url=f"{self.VMC.VMC_URL}/vmc/api/orgs/{ORG_ID}/delegated-access/vcenter/sddcs/{self.ID}",
                    headers={
                        'Content-type': 'application/json',
                        'Accept': 'application/json',
                        'csp-auth-token': self.VMC.ACCESS_TOKEN
                    }
                )
                if 'vcenter_html_url' in RESULT:
                    break
            if 'vcenter_html_url' not in RESULT:
                Log.warn('failed to get vCenter access')
                return []
            VC_URL = RESULT['vcenter_html_url']
            VC_TOKEN = RESULT['agent_login_token']
        else:
            ORG_ID = target_org
            RESULT = curl.get(
                url=f"{self.VMC.VMC_URL}/vmc/api/orgs/{ORG_ID}/delegated-access/vcenter/sddcs/{self.ID}",
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.VMC.ACCESS_TOKEN
                }
            )
            VC_TOKEN = curl.get(
                url=f"{self.VMC.VMC_URL}/vmc/api/operator/sddcs/{self.ID}/agent/login-token",
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.VMC.ACCESS_TOKEN
                }
            )
            VC_URL = RESULT['vc_url']
        VC_AUTH_URL = f"{VC_URL}/request-auth?login_token={VC_TOKEN}"
        VC_UI_URL = f"{VC_URL}/ui/?idp=local"
        REDUCE = { 'name':None,'id':None,'admin_username':None }
        RESULT = reduce_json(RESULT, REDUCE)
        RESULT['auth_url'] = VC_AUTH_URL
        RESULT['vc_url'] = VC_UI_URL
        return RESULT

    def vcenter_ssh_toggle(self, action, reason, raw=False):
        DATA = {
            "requestBody": {
                "scriptId": "vcenter_ssh_toggle",
                "sddc-id": self.ID,
                "action": action,
                "reason": reason
            }
        }
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'status':None, 'sddc_id': ['params','script_task_parameters','params','sddc_id'], 'scriptId': ['script_task_parameters','params','scriptId'], 'data':['SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return REDUCE

    def vcenter_ssh_verify(self, reason, raw=False):
        DATA = {
            "requestBody": {
                "scriptId": "vcenter_ssh_verify",
                "sddc-id": self.ID,
                "reason": reason
            }
        }
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA)
        if not raw:
            REDUCE = {'status':None, 'sddc_id': ['params','script_task_parameters','params','sddc_id'], 'scriptId': ['script_task_parameters','params','scriptId'], 'data':['SCRIPTDATA','data']}
            RESULT = reduce_json(RESULT, REDUCE)
        return REDUCE

    def backup(self):
        DATA = {
            "sddc_id": self.ID, 
            "name": "BACKUPTEST",
            "backup_type": "USER",
            "meta_data":{} 
        }
        RTS = rts(self.VMC)
        RESULT = RTS.run(DATA,f'/vmc/backuprestore/sddc/{self.ID}/backup')
        return RESULT

    def backup_show(self, name_only):

        RTS = rts(self.VMC)
        BACKUP_LIST = RTS.run(None, f'/vmc/backuprestore/sddc/{self.ID}/backup/info')
        print(BACKUP_LIST)
        if name_only:
            REDUCE = { 'name':None }
        else:
            REDUCE = { "name":None, "creation_date":None, "sddc_name": [ "metadata","user_metadata","sddc.name" ] }
        BACKUP_LIST = reduce_json(BACKUP_LIST, REDUCE)
        return BACKUP_LIST
