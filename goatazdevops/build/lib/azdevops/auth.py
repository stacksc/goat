import sys, click, getpass
from toolbox.logger import Log
from toolbox.getpass import getCreds
from configstore.configstore import Config
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azdevops.azdevclient import AzDevClient
import pprint
import requests
import datetime
from toolbox import misc

CONFIG = Config('azdev')
AZDEV = AzDevClient()

@click.group(help="perform authentication operations for AZ DevOps", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def auth(ctx, debug):
    log = Log('azdev.log', debug)

@auth.command(help="setup or change authentication settings for AZ DevOps", context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--url', help='address of the Organization URL', default='https://dev.azure.com/baxtercu', required=False, type=str)
@click.pass_context
def setup(ctx, url):
    profile = ctx.obj['PROFILE']
    if profile is None:
        profile = 'default'
    AZDEV.get_session(url, profile, force=True)

def get_user_profile_based_on_key(key, return_first=True):
    if not key:
        return None
    try:
        if type(key) is str:
            PROJECT_KEY = key
        else:
            PROJECT_KEY = key[0]
    except IndexError:
        Log.critical("You must provide a issue key, project key, or a user profile to use jiratools")
    FOUND_PROFILES = []
    for PROFILE in CONFIG.PROFILES:
        CACHED_PROJECTS = CONFIG.get_metadata('projects', PROFILE)
        if CACHED_PROJECTS is not None:
            for CACHED_PROJECT in CACHED_PROJECTS:
                if PROJECT_KEY == CACHED_PROJECT:
                    FOUND_PROFILES.append(PROFILE)
    if return_first:
        try:
            return FOUND_PROFILES[0]
        except IndexError:
            return None
