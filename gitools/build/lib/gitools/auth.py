import click, getpass, os
from .client import Client
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox import misc

GIT = Client()

@click.group(help="perform authentication operations against git", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-u', '--usage', help='provide usage instructions to setup access to git tools', is_flag=True)
@click.pass_context
def auth(ctx, debug, usage):
    log = Log('gitools.log', debug)

def get_latest_profile():
    CONFIGSTORE = Config('gitools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        GIT_PROFILE = 'default'
    else:
        GIT_PROFILE = LATEST['config']['role']
    return GIT_PROFILE

@auth.command(help='setup your API access to git', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def setup(ctx):
    RESULT = GIT.setup_access(ctx.obj['profile'])
    if RESULT:
        Log.info("git settings saved succesfully")
        update_latest_profile(ctx.obj['profile'])
    return RESULT

def get_git_url(profile='default'):
    CONFIG = Config('gitools')
    URL = CONFIG.get_metadata('GIT_URL', 'preset')
    if URL:
        return URL
    return profile

def update_latest_profile(profile_name):
    BASICS = Config('gitools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')

