import click, getpass, os
from .client import Client
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox import misc

FLY = Client()

@click.group(help="perform authentication operations against Concourse Runway", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def auth(ctx, debug):
    log = Log('flytools.log', debug)

def get_latest_profile():
    CONFIGSTORE = Config('flytools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        PROFILE = 'default'
    else:
        PROFILE = LATEST['config']['role']
    return PROFILE

@auth.command(help='setup your API access to concourse runway', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def setup(ctx):
    RESULT = FLY.setup_access(ctx.obj['profile'])
    if RESULT:
        Log.info("concourse runway settings saved succesfully")
        update_latest_profile(ctx.obj['profile'])
    return RESULT

def get_url(profile='default'):
    CONFIG = Config('flytools')
    URL = CONFIG.get_metadata('CONCOURSE_URL', 'preset')
    if URL:
        return URL
    return profile

def update_latest_profile(profile_name):
    BASICS = Config('flytools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')

