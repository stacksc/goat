import os, click
from toolbox.logger import Log
from . import iam_nongc
import toolbox.misc as misc
from configstore.configstore import Config
from .oci_config import OCIconfig

@click.group('iam', help='manage and switch between OCI profiles for all realms', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def iam():
    pass

def get_latest_profile():

    CONFIGSTORE = Config('ocitools')
    LATEST = CONFIGSTORE.get_profile('latest')
    if LATEST is None:
        PROFILE = 'default'
    else:
        PROFILE = LATEST['config']['name']
    return PROFILE

def get_latest_region(profile_name):
    CONFIG = OCIconfig()
    REGION = CONFIG.get_from_config('config', 'region', profile_name=profile_name)
    if REGION is None:
        return 'us-ashburn-1'
    return REGION

iam.add_command(iam_nongc.authenticate)
