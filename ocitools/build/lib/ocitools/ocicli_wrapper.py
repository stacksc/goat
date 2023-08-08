import click, os, subprocess, tempfile
from toolbox.logger import Log
from .oci_config import OCIconfig
from . import iam_nongc
from . import iam_ingc
from configstore.configstore import Config
from toolbox.misc import set_terminal_width, detect_environment

CONFIG = Config('ocitools')
LATEST = CONFIG.get_profile('latest')

if LATEST is None:
    LATEST = 'default'
else:
    LATEST = LATEST['config']['role']

@click.command(help="run any ocicli (oci) command while leveraging ocitools profile functionality", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('ocicli_command', nargs=-1, type=str, required=True)
@click.option('-r', '--region', 'oci_region', help='OCI region to authenticate against', required=False, default='us-ashburn-1')
@click.pass_context
def cli(ctx, ocicli_command, oci_region):
    profile_name = ctx.obj['PROFILE']
    OCI = get_OCIcli(oci_profile_name, oci_region)
    CMD = ' '.join(ocicli_command) # convert tuple to string
    RESULT = OCI.run_cmd(f"oci --region {oci_region} {CMD}")
    print(RESULT)

class OCIcli():
    def __init__(self, profile_name, in_boundary, region='us-ashburn-1'):
        self.INB = detect_environment()
        self.OCI_PROFILE = profile_name
        self.OCI_REGION = region
        self.CONFIG = OCIconfig()
        #if self.CONFIG.profile_or_role(oci_profile_name):
        #    self.SESSION = iam_nongc._authenticate(oci_profile_name, oci_region)
        #else:
        #    self.SESSION = iam_nongc._assume_role(oci_profile_name=oci_profile_name)[0]

    def run_cmd(self, cmd):
        self.CONFIG.unset_oci_profile()
        RESULT = run_command(cmd)
        return RESULT

def get_OCIcli(profile_name, oci_region='us-ashburn-1'):
    try:
        DOMAIN = os.getenv('USER').split('@')[1]
        ENVS = {
            "admins.vmwarefed.com": 'gc-prod',
            "vmwarefedstg.com": 'gc-stg',
            "vmware.smil.mil": 'ohio-sim'
        }
        inb = True
        RESULT = ENVS[DOMAIN]
        return OCIcli(oci_profile_name, inb, oci_region)
    except:
        inb = False
        return OCIcli(oci_profile_name, inb, oci_region)

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
    
