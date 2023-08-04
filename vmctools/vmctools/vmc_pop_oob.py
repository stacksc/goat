# oob - out of bounds - POP is accessible directly

import click, json, os
from .vmcclient import vmc
from toolbox.logger import Log
from csptools.cspclient import CSPclient

@click.group(help="connect to, manage and view info about SDDC's POP instance", context_settings={'help_option_names':['-h','--help']})
@click.option('-a', '--auth', 'auth_org', help="org id/name to use for authentication", type=str, required=False, default='operator')
@click.pass_obj
def pop(ctx, auth_org):
    ctx['auth_org'] = auth_org
    pass

@pop.command('request', help='request access to POP for an SDDC')
@click.argument('target_org', required=True)
@click.argument('sddc_id', required=True)
@click.option('-r', '--reason', help='supply a reason for POP access (required in prod)', default=None, required=False)
@click.option('-t', '--token_access', help='use a token to request access to POP and ESX', default=False, is_flag=True, required=False)
@click.pass_obj
def pop_request(ctx, sddc_id, target_org, reason, token_access):
    if reason is None:
        if detect_environment() == 'gc-prod':
            Log.critical('reason is required in production environment')
        else:
            reason = 'testing. please ignore'
    ctx = verify_context(ctx)
    user_profile = ctx['profile']
    auth_org = ctx['auth_org']
    ORG_ID = lookup_org(user_profile, target_org)
    VMC = vmc(user_profile, auth_org)
    RESULT = VMC.pop_request(sddc_id, target_org, reason, token_access)
    if RESULT.status_code == 200:
        Log.info(RESULT)
    elif RESULT.status_code == 400:
        Log.critical(f'{sddc_id} SDDC in {target_org} is not in a healthy state')
    elif RESULT.status_code == 403:
        Log.critical(f'you are missing permissions for POP for {sddc_id} SDDC in {target_org}')

@pop.command('connect', help='connect to POP associated with a specific SDDC')
@click.argument('sddc_id', required=True)
@click.pass_obj
def pop_connect(ctx, sddc_id):
    ctx = verify_context(ctx)
    user_profile = ctx['profile']
    auth_org = ctx['auth_org']
    VMC = vmc(user_profile, auth_org)
    pass

@pop.group('show', help='show info about POP')
def pop_show():
    pass

@pop_show.command('details', help='show details about a POP instance for a given SDDC in a specific org')
@click.argument('target_org', required=True)
@click.argument('sddc_id', required=True)
@click.pass_obj
def pop_show_all(ctx, sddc_id, org_id):
    ctx = verify_context(ctx)
    user_profile = ctx['profile']
    auth_org = ctx['auth_org']
    VMC = vmc(user_profile, auth_org)
    RESULT = VMC.pop_show_all(sddc_id, org_id)
    if RESULT.status_code == 200:
        Log.info(json.loads(RESULT.json, ident=4))
    elif RESULT.status_code == 204:
        Log.critical('no active access exists for the operator')
    elif RESULT.status_code == 401 or RESULT.status_code == 403:
        Log.critical('operator is not authorised to use this POP instance')
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')
    
def verify_context(ctx):
    if ctx is None:
        ctx = {}
        ctx['profile'] = input('please provide name of the profile to use, or press enter to accept default value')
        if ctx['profile'] == "":
            ctx['profile'] = 'default'
    return ctx

def detect_environment():
    try:
        DOMAIN = os.getenv('USER').split('@')[1]
        ENVS = {
            "vmwarefed.com": 'gc-prod',
            "vmwarefedstg.com": 'gc-stg',
            "vmware.smil.mil": 'ohio-sim'
        }
        RESULT = ENVS[DOMAIN]
    except:
        Log.debug('Unable to get user domain; assuming non-gc environment (ie VMware issued macbook)')
        return 'non-gc'
    return RESULT

def lookup_org(user_profile, target_org):
    CSP = CSPclient()
    ORG_ID = CSP.get_org_ids(user_profile, target_org)
    return ORG_ID