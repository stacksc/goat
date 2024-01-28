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
    AZDEV.get_session(url, profile)

@auth.command(help="manage configuration details for the AZ DevOps server on this profile", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--default', help='mark this profile as the default profile to use for AZ DevOps', is_flag=True)
@click.option('-s', '--show', help='show the entire config for the AZ DevOps server on this profile', is_flag=True)
@click.option('-t', '--token', 'token', help='show the personal access token for the AZ DevOps server on this profile', is_flag=True)
@click.pass_context
def config(ctx, default, show, token):
    profile = ctx.obj['PROFILE']
    if default is True:
        CURRENT_DEFAULT_PROFILE = AZDEV.get_default_profile()
        RESULT = AZDEV.get_default_url()
        AZDEV.set_default_url(profile, CURRENT_DEFAULT_PROFILE)
    else:
        if token:
            RESULT = AZDEV.get_access_token(user_profile=profile)
            Log.info(f"Personal Access Token: {RESULT}")
            RESULT = AZDEV.get_access_token_age(user_profile=profile)
            Log.info(f"Access token has been created {RESULT} minutes ago")
        else:
            RESULT = get_azdev_config(profile)
    return RESULT

# worker functions required for non-click usage
def get_azdev_config(user_profile='default'):
    RESULT = CONFIG.display_profile(user_profile)
    return RESULT

