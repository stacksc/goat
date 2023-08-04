import click, getpass, os
from .cspclient import CSPclient, env_from_sourcing
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox import misc

CSP = CSPclient()

@click.group(help="perform authentication operations against CSP", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-u', '--usage', help='provide usage instructions to setup access to CSP tools', is_flag=True)
@click.pass_context
def auth(ctx, debug, usage):
    os.environ = env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=True)
    OPERATOR = os.environ['ORG_OPERATOR']
    PLATFORM = os.environ['ORG_PLATFORM']
    if usage:
        print(f"""
INFO: the following can help users get started with getting access tp CSP using the CLI:
      pyps csp -p operator auth setup -i {OPERATOR} -n \"VMC Gov Cloud Operator Org PRD\"
      pyps csp -p platform auth setup -i {PLATFORM} -n \"Platform org\"
        """)
    log = Log('csptools.log', debug)

def get_latest_profile():
    CONFIGSTORE = Config('csptools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        CSP_PROFILE = 'default'
    else:
        CSP_PROFILE = LATEST['config']['role']
    return CSP_PROFILE

@auth.command(help='ad-hoc convert a refresh token to an access token', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def convert_token(ctx):
    while True:
        REFRESH_TOKEN = getpass.getpass('Refresh token: ')
        if REFRESH_TOKEN != "":
            break
    RESULT = CSP.generate_access_token(REFRESH_TOKEN, ctx.obj['profile'])
    Log.info(f"access token:\n{RESULT['token']}")
    return RESULT

@auth.command(help='update the default profile', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def update_profile(ctx):
    CONFIGSTORE = Config('csptools')
    update_latest_profile(ctx.obj['profile'])

@auth.command(help='setup your API access to a given CSP org', context_settings={'help_option_names':['-h','--help']})
@click.option('-i', '--id', 'org_id', help="ID of the target CSP org", type=str, required=False, default=None)
@click.option('-n', '--name', 'org_name', help="name of the target CSP org", type=str, required=False, default=None)
@click.pass_context
def setup(ctx, org_id, org_name):
    RESULT = CSP.setup_org_access(org_id, org_name, ctx.obj['profile'])
    if RESULT:
        Log.info("Org settings saved succesfully")
        update_latest_profile(ctx.obj['profile'])
    return RESULT

def get_csp_url(profile='default'):
    CONFIG = Config('csptools')
    URL = CONFIG.get_metadata('CSP_URL', 'preset')
    if URL:
        return URL
    return profile

def get_vmc_url(profile='default'):
    CONFIG = Config('csptools')
    URL = CONFIG.get_metadata('VMC_URL', 'preset')
    if URL:
        return URL
    return profile

def update_latest_profile(profile_name):
    BASICS = Config('csptools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')

