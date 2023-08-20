import click, os, subprocess, tempfile, re
from toolbox.logger import Log
from .oci_config import OCIconfig
from . import iam_nongc
from configstore.configstore import Config
from toolbox.misc import set_terminal_width, detect_environment

CONFIG = Config('ocitools')
LATEST = CONFIG.get_profile('latest')

if LATEST is None:
    LATEST = 'default'
else:
    LATEST = LATEST['config']['name']

CONTEXT_SETTINGS = {'help_option_names':['-h'], 'max_content_width': set_terminal_width(), 'ignore_unknown_options': True, 'allow_extra_args': True}

@click.command(help="run any ocicli (oci) command while leveraging ocitools profile functionality; append --help for usage on cli commands", context_settings=CONTEXT_SETTINGS)
@click.argument('ocicli_command', nargs=-1, type=str, required=False)
@click.option('-r', '--region', 'region', help='OCI region to authenticate against', required=False, default='us-ashburn-1', type=str)
@click.option('-i', '--interactive', 'interactive', help='spawn the interactive shell', is_flag=True, required=False, default=False)
@click.pass_context
def cli(ctx, ocicli_command, region, interactive):
    profile_name = ctx.obj['PROFILE']
    OCI = get_OCIcli(profile_name, region)
    CMD = ' '.join(ocicli_command) # convert tuple to string
    if interactive is True:
        try:
            os.system(f"oci --profile {profile_name} --region {region} -i")
        except:
            Log.critical(f'unable to launch oci -i for interactive use; please install the latest OCI CLI.')
    elif not CMD:
        try:
            os.system(f"oci --profile {profile_name} --region {region} -i")
        except:
            Log.critical(f'unable to launch oci -i for interactive use; please install the latest OCI CLI.')
    else:
        RESULT = OCI.run_cmd(f"oci --profile {profile_name} --region {region} {CMD}")
        print(RESULT)

class OCIcli():
    def __init__(self, profile_name, region='us-ashburn-1'):
        self.OCI_PROFILE = profile_name
        self.OCI_REGION = region
        self.CONFIG = OCIconfig()

    def run_cmd(self, cmd):
        RESULT = run_command(cmd)
        return RESULT

def get_OCIcli(profile_name, region='us-ashburn-1'):
    return OCIcli(profile_name, region)

def run_command(command):
    TEMP = tempfile.NamedTemporaryFile(delete=False)
    TEMP.close()
    PATH = TEMP.name
    CMD = command + " 1> " + PATH + " 2>" + PATH
    PROC = subprocess.run(CMD, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    with open(PATH, 'r') as f:
        DATA = f.read()
    os.unlink(PATH)
    return DATA
    
