import click, os, subprocess, tempfile
from toolbox.logger import Log
from .aws_config import AWSconfig
from . import iam_nongc
from . import iam_ingc
from toolbox.click_complete import complete_profile_names
from configstore.configstore import Config
from toolbox.misc import set_terminal_width, detect_environment

CONFIG = Config('awstools')
LATEST = CONFIG.get_profile('latest')

if LATEST is None:
    LATEST = 'default'
else:
    LATEST = LATEST['config']['role']

@click.command(help="run any awscli (aws) command while leveraging awstools profile functionality", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('awscli_command', nargs=-1, type=str, required=True)
@click.option('-r', '--region', 'aws_region', help='AWS region to authenticate against', required=False, default='us-gov-west-1')
@click.pass_context
def cli(ctx, awscli_command, aws_region):
    aws_profile_name = ctx.obj['PROFILE']
    if aws_profile_name == 'default':
        check_env()
    AWS = get_AWScli(aws_profile_name, aws_region)
    CMD = ' '.join(awscli_command) # convert tuple to string
    RESULT = AWS.run_cmd(f"aws --region {aws_region} {CMD}")
    print(RESULT)

class AWScli():
    def __init__(self, aws_profile_name, in_boundary, aws_region='us-gov-west-1'):
        self.INB = detect_environment()
        self.AWS_PROFILE = aws_profile_name
        self.AWS_REGION = aws_region
        self.CONFIG = AWSconfig()
        self.CONFIG.unset_aws_profile()
        if 'prod' in self.INB:
            MINS = iam_ingc.check_time(self.AWS_PROFILE)
            if MINS >= 30 or MINS is False:
                IDP_URL = CONFIG.get_config('IDP_URL', 'IDP')
                RESULT, self.AWS_PROFILE = iam_ingc._authenticate(IDP_URL, aws_region=self.AWS_REGION, aws_output='json', aws_profile_name=self.AWS_PROFILE, menu=False)
                if RESULT is not None:
                    ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_access_key_id', 'string', 'aws_access_key_id', self.AWS_PROFILE)
                    SECRET_ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_secret_access_key', 'string', 'aws_secret_access_key', self.AWS_PROFILE)
                    TOKEN = self.CONFIG.get_from_config('creds', 'aws_session_token', 'string', 'aws_session_token', self.AWS_PROFILE)
                    self.SESSION = iam_ingc.get_role_session(ACCESS_KEY, SECRET_ACCESS_KEY, TOKEN)
            else:
                ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_access_key_id', 'string', 'aws_access_key_id', self.AWS_PROFILE)
                SECRET_ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_secret_access_key', 'string', 'aws_secret_access_key', self.AWS_PROFILE)
                TOKEN = self.CONFIG.get_from_config('creds', 'aws_session_token', 'string', 'aws_session_token', self.AWS_PROFILE)
                self.SESSION = iam_ingc.get_role_session(ACCESS_KEY, SECRET_ACCESS_KEY, TOKEN)
        else:
            if self.CONFIG.profile_or_role(aws_profile_name):
                self.SESSION = iam_nongc._authenticate(aws_profile_name, aws_region)
            else:
                self.SESSION = iam_nongc._assume_role(aws_profile_name=aws_profile_name)[0]

    def get_session_creds(self):
        CREDS = self.SESSION.get_credentials()
        CREDS = CREDS.get_frozen_credentials()
        ACCESS_KEY = CREDS.access_key
        SECRET_KEY = CREDS.secret_key
        TOKEN = CREDS.token
        return ACCESS_KEY, SECRET_KEY, TOKEN
    
    def creds_to_env(self):
        KEY, SECRET, TOKEN = self.get_session_creds()
        os.environ['AWS_ACCESS_KEY_ID'] = KEY
        os.environ['AWS_SECRET_ACCESS_KEY'] = SECRET
        if TOKEN is not None:
            os.environ['AWS_SESSION_TOKEN'] = TOKEN
    
    def run_cmd(self, cmd):
        self.CONFIG.unset_aws_profile()
        self.creds_to_env()
        RESULT = run_command(cmd)
        return RESULT

def get_AWScli(aws_profile_name, aws_region='us-gov-west-1'):
    try:
        DOMAIN = os.getenv('USER').split('@')[1]
        ENVS = {
            "admins.vmwarefed.com": 'gc-prod',
            "vmwarefedstg.com": 'gc-stg',
            "vmware.smil.mil": 'ohio-sim'
        }
        inb = True
        RESULT = ENVS[DOMAIN]
        return AWScli(aws_profile_name, inb, aws_region)
    except:
        inb = False
        return AWScli(aws_profile_name, inb, aws_region)

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
    
def check_env(): # ensure none of the AWS env variables is set
    COUNT = 0
    try:
        os.environ['AWS_SECRET_KEY_ID'] 
    except KeyError:
        COUNT = COUNT + 1
    try:
        os.environ['AWS_SECRET_ACCESS_KEY']
    except KeyError:
        COUNT = COUNT + 1
    try:
        os.environ['AWS_SESSION_TOKEN']
    except KeyError:
        COUNT = COUNT + 1
    if COUNT != 3:    
        Log.critical('Please unset AWS_SECRET_KEY_ID, AWS_SECRET_ACCESS_KEY and/or AWS_SESSION_TOKEN before proceeding')
