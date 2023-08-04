import time, click, json
from csptools.cspclient import CSPclient
from toolbox.logger import Log
from toolbox import curl
from .vmc_misc import get_operator_context
from configstore.configstore import Config
from toolbox.menumaker import Menu

CONFIG = Config('csptools')

@click.group('rts', help='run and manage RTS tasks', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def _rts(ctx):
    pass

@_rts.command('run', help='run ad-hoc RTS script', context_settings={'help_option_names':['-h','--help']})
@click.argument('path_to_rts_json_file', required=True)
@click.pass_context
def _run(ctx, path_to_rts_json_file):
    AUTH, PROFILE = get_operator_context(ctx)
    with open(path_to_rts_json_file, 'r') as RTS_JSON:
        DATA = json.loads(RTS_JSON.read())
    RTS = rts(None, AUTH, PROFILE, None)
    Log.info(RTS.run(DATA))

@_rts.command('status', help='check status of a given RTS task', context_settings={'help_option_names':['-h','--help']})
@click.argument('rts_task_id', required=True)
@click.pass_context
def _status(ctx, rts_task_id):
    AUTH, PROFILE = get_operator_context(ctx)
    RTS = rts(None, AUTH, PROFILE, None)
    Log.info(RTS.get_task_status(rts_task_id))

@_rts.command('details', help='get details about a specific RTS task', context_settings={'help_option_names':['-h','--help']})
@click.argument('rts_task_id', required=True)
@click.pass_context
def _details(ctx, rts_task_id):
    AUTH, PROFILE = get_operator_context(ctx)
    RTS = rts(None, AUTH, PROFILE, None)
    Log.info(RTS.get_task(rts_task_id))

class rts():

    def __init__(self, vmc_object=None, auth_org=None, user_profile=None, rts_endpoint=None):
        if vmc_object is not None:
            self.CONFIG = vmc_object.CONFIG
            self.ACCESS_TOKEN = vmc_object.ACCESS_TOKEN
            if rts_endpoint is not None:
                self.endpoint = rts_endpoint
            else:
                # TESTING
                #self.endpoint = self.CONFIG.get_var('rts_endpoint', 'metadata', 'INTERNAL_URL', vmc_object.USER_PROFILE)
                self.endpoint = 'https://internal.vmc-us-gov.vmware.com'
        else:
            CSP = CSPclient()
            self.ACCESS_TOKEN = CSP.get_org_access_token(auth_org, user_profile, user_profile)
            if rts_endpoint is not None:
                self.endpoint = rts_endpoint
            else:
                # TESTING
                #self.endpoint = self.CONFIG.get_var('rts_endpoint', 'metadata', 'INTERNAL_EDPOINT', user_profile)
                self.endpoint = 'https://internal.vmc-us-gov.vmware.com'

    def run(self, data, api=None):
        if api is None:
            try:
                TASK_ID = curl.post(
                    url=f"{self.endpoint}/vmc/rts/api/operator/script",
                    headers={
                        'Content-type': 'application/json',
                        'Accept': 'application/json',
                        'csp-auth-token': self.ACCESS_TOKEN
                    },
                    rjson=data
                )['id']
            except:
                return None
            FINISHED = False
            print('INFO: running', end=' ', flush=True)
            while not FINISHED:
                print('.', end=' ', flush=True)
                time.sleep(2)
                try:
                    if self.get_task_status(TASK_ID) is not None and self.get_task_status(TASK_ID) != 'STARTED':
                        FINISHED = True
                        print()
                except:
                    continue
            RESULT = self.get_task(TASK_ID)
            return RESULT
        else:
            RESULT = curl.post(
                url=f'{self.endpoint}{api}',
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                    'csp-auth-token': self.ACCESS_TOKEN
                },
                rjson=data
            )
            return RESULT

    def get_task(self, task_id):
        return curl.get(
            url=f"{self.endpoint}/vmc/rts/api/operator/tasks/{task_id}",
            headers={
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'csp-auth-token': self.ACCESS_TOKEN
            }
        )

    def get_task_status(self, task_id):
        return self.get_task(task_id)['status']
