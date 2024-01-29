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

