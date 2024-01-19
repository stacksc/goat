import click, getpass, os, json, jenkins
from .jenkinsclient import JenkinsClient
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox import misc

JENKINS = JenkinsClient()

@click.group(help="perform authentication operations against Jenkins", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def auth(ctx, debug):
    log = Log('jenkinstools.log', debug)

def get_latest_profile():
    CONFIGSTORE = Config('jenkinstools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        JENKINS_PROFILE = 'default'
    else:
        JENKINS_PROFILE = LATEST['config']['role']
    return JENKINS_PROFILE

@auth.command(help='update the default profile', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def update_profile(ctx):
    CONFIGSTORE = Config('jenkinstools')
    update_latest_profile(ctx.obj['profile'])

@auth.command(help='setup your API access to jenkins', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def setup(ctx):
    RESULT = JENKINS.setup_access(ctx.obj['profile'])
    if RESULT:
        Log.info("jenkins settings saved succesfully")
        update_latest_profile(ctx.obj['profile'])
    return RESULT

def get_jenkins_url(profile='default'):
    CONFIG = Config('jenkinstools')
    URL = CONFIG.get_metadata('JENKINS_URL', profile)
    if URL:
        return URL
    else:
        return profile

def update_latest_profile(profile_name):
    BASICS = Config('jenkinstools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'role', 'latest')
    else:
        BASICS.update_config(profile_name, 'role', 'latest')

def get_jenkins_session(url, username, password):
    SESSION = jenkins.Jenkins(url,
        username=username,
        passsword=password
    )
    return SESSION

