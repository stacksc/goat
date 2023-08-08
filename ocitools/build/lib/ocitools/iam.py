import os, click
from toolbox.logger import Log
from . import iam_ingc, iam_nongc
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

if misc.detect_environment() == 'non-gc':
    iam.add_command(iam_nongc.authenticate)
    iam.add_command(iam_nongc.assume_role)
else:
    iam.add_command(iam_ingc.authenticate)
    iam.add_command(iam_ingc.reset_password)
