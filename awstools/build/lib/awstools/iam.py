import os, click
from toolbox.logger import Log
from . import iam_nongc
import toolbox.misc as misc
from configstore.configstore import Config
from .aws_config import AWSconfig

@click.group('iam', help='manage and switch between AWS profiles in GC and SIM regions', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def iam():
    pass

def get_latest_profile():

    CONFIGSTORE = Config('awstools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        AWS_PROFILE = 'default'
    else:
        AWS_PROFILE = LATEST['config']['role']
    return AWS_PROFILE

def get_latest_region(profile_name):
    CONFIG = AWSconfig()
    REGION = CONFIG.get_from_config('creds', 'region', profile_name=profile_name)
    if REGION is None:
        return 'us-east-1'
    return REGION

if misc.detect_environment() == 'non-gc':
    iam.add_command(iam_nongc.authenticate)
