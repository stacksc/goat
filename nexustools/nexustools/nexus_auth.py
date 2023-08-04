import click, getpass, os
from .nexusclient import NexusClient, env_from_sourcing
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox import misc

NEXUS = NexusClient()

@click.group(help="perform authentication operations against Nexus", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-u', '--usage', help='provide usage instructions to setup access to Nexus tools', is_flag=True)
@click.pass_context
def auth(ctx, debug, usage):
    os.environ = env_from_sourcing(file_to_source_path='/usr/local/bin/govops-vmc-tools.cfg', include_unexported_variables=True)
    log = Log('nexustools.log', debug)

def get_latest_profile():
    CONFIGSTORE = Config('nexustools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        NEXUS_PROFILE = 'default'
    else:
        NEXUS_PROFILE = LATEST['config']['role']
    return NEXUS_PROFILE

@auth.command(help='setup your API access to nexus', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def setup(ctx):
    RESULT = NEXUS.setup_access(ctx.obj['profile'])
    if RESULT:
        Log.info("nexus settings saved succesfully")
        update_latest_profile(ctx.obj['profile'])
    return RESULT

def get_nexus_url(profile='default'):
    CONFIG = Config('nexustools')
    URL = CONFIG.get_metadata('NEXUS_URL', 'preset')
    if URL:
        return URL
    return profile

def update_latest_profile(profile_name):
    BASICS = Config('nexustools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')

