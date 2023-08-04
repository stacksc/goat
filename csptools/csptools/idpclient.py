from .cspclient import CSPclient
from toolbox import curl
from toolbox.jsontools import filter
from toolbox.jsontools import reduce_json
import requests

class idpc():

    def __init__(self, profile):
        self.CSP = CSPclient()
        self.PROFILE = profile

    def add(self, tenant, domains, ticket, public_key, auth_org='platform'):
        AUTH_ID = self.CSP.get_org_ids(self.PROFILE, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.CSP.get_access_details(AUTH_ID, self.PROFILE)
        NAME = tenant.split('.')[0]
        return curl.post(
            url=f'{CSP_URL}/csp/gateway/am/api/idp-registration',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                "idpAuthorizeUri": f"https://{tenant}/SAAS/auth/oauth2/authorize",
                "idpDomains": [ domains ],
                "idpIssuerUri": f"https://{tenant}/SAAS/auth",
                "idpLoginUrl": f"https://{tenant}/login",
                "idpLogoutUrl": f"https://{tenant}/logout",
                "idpPublicKey": public_key,
                "idpScimUri": f"https://{tenant}/SAAS/jersey/manager/api/scim",
                "idpTokenUri": f"https://{tenant}/SAAS/auth/oauthtoken",
                "idpUrl": f"https://{tenant}",
                "serviceDeskId": ticket,
                "idpDisplayName": NAME
            }
        )

    def delete(self, idp_id, force, auth_org='platform'):
        AUTH_ID = self.CSP.get_org_ids(self.PROFILE, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.CSP.get_access_details(AUTH_ID, self.PROFILE)
        if force:
            IDP = f"{idp_id}?force=true"
        else:
            IDP = idp_id
        return curl.delete(
            url=f"{CSP_URL}/csp/gateway/am/api/idp-registration/{IDP}",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            }
        )

    def domains_add(self, idp_id, domains, auth_org='platform'):
        return self.manage_domains('add', idp_id, domains, auth_org)

    def domains_delete(self, idp_id, domains, auth_org='platform'):
        return self.manage_domains('delete', idp_id, domains, auth_org)

    def manage_domains(self, action, idp_id, domains, auth_org='platform'):
        if action == 'add':
            TYPE = 'POST'
        elif action == 'delete':
            TYPE = 'DELETE'
        else:
            return None
        AUTH_ID = self.CSP.get_org_ids(self.PROFILE, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.CSP.get_access_details(AUTH_ID, self.PROFILE)
        return curl.call(
            type=TYPE,
            url=f"{CSP_URL}/csp/gateway/am/api/idp-registrations/{idp_id}/domains",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'csp-auth-token': ACCESS_TOKEN
            },
            rjson={
                 "idpDomains": [ domains ]
            }
        )

    def show(self, filter_definition=None, auth_org='platform'):
        AUTH_ID = self.CSP.get_org_ids(self.PROFILE, auth_org)
        ACCESS_TOKEN, CSP_URL, VMC_URL = self.CSP.get_access_details(AUTH_ID, self.PROFILE)
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

    def get_tenant_names(self, filter_definition, auth_org='platform'):
        RESULTS = self.show(filter_definition, auth_org)
        DATA = []
        for ITEM in RESULTS:
            for I in ITEM:
                IDPURL = I['idpUrl'].ljust(60)
                FILTER = I['idpDisplayName']
                if FILTER:
                    details = IDPURL + "\t" + FILTER
                    DATA.append(details)
                else:
                    FILTER = I['idpId']
                    if FILTER:
                        details = IDPURL + "\t" + FILTER
                        DATA.append(details)
        return DATA

    def get_tenant_ids(self, filter_definition, auth_org='platform'):
        RESULTS = self.show(filter_definition, auth_org)
        DATA = []
        for ITEM in RESULTS:
            for I in ITEM:
                IDPID = I['idpId'].ljust(50)
                FILTER = I['idpDisplayName']
                if FILTER:
                    details = IDPID + "\t" + FILTER
                    DATA.append(details)
        return DATA
