# these are some examples of click auto completion for projects and slack emoji names
import os, importlib_resources, glob
from pathlib import Path
from configstore.configstore import Config
from toolbox.misc import detect_environment

def complete_profile_names(ctx, param, incomplete):
    NAMES = {}
    NAMES = listAwsProfiles()
    return [k for k in NAMES if k.startswith(incomplete)]

def complete_idp_profiles(ctx, param, incomplete):
    CONFIG = Config('idptools')
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        NAMES.append(PROFILE)
    return [k for k in NAMES if k.startswith(incomplete)]

def complete_csp_profiles(ctx, param, incomplete):
    CONFIG = Config('csptools')
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        NAMES.append(PROFILE)
    return [k for k in NAMES if k.startswith(incomplete)]

def complete_jenkins_profiles(ctx, param, incomplete):
    CONFIG = Config('jenkinstools')
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        NAMES.append(PROFILE)
    return [k for k in NAMES if k.startswith(incomplete)]

def complete_jira_profiles(ctx, param, incomplete):
    CONFIG = Config('jiratools')
    CACHED_PROFILES = []
    for PROFILE in CONFIG.PROFILES:
        CACHED_PROFILES.append(PROFILE)
    return [k for k in CACHED_PROFILES if k.startswith(incomplete)]

def complete_configstore_names(ctx, param, incomplete):
    NAMES = []
    HOME = str(Path.home())
    for KEY in glob.glob(HOME + "/.*key"):
        if os.path.isfile(KEY):
            KEY = str(Path(KEY).stem.replace(".",""))
            BASE = os.path.basename(KEY)
            NAMES.append(str(BASE))
    return [k for k in NAMES if k.startswith(incomplete)]

def complete_projects(ctx, param, incomplete):
    from jiratools.auth import get_default_profile
    CONFIG = Config('jiratools')
    CACHED_PROJECTS = {}
    CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
    return [k for k in CACHED_PROJECTS if k.startswith(incomplete)]

def complete_db_names(ctx, param, incomplete):
    from awstools.aws_config import AWSconfig
    CONFIG = AWSconfig()
    CONFIGSTORE = Config('awstools')
    LATEST = CONFIGSTORE.get_profile('latest')
    PROFILE = LATEST['config']['role']
    DATA = {}
    DATA.update(CONFIGSTORE.PROFILES[PROFILE]['metadata']['cached_rds_instances'])
    return [k for k in DATA if k.startswith(incomplete)]

def complete_bucket_names(ctx, param, incomplete):
    CONFIG = Config('awstools')
    LATEST = CONFIG.get_profile('latest')
    PROFILE = LATEST['config']['role']
    CACHED_BUCKETS = {}
    CACHED_BUCKETS.update(CONFIG.get_metadata('cached_buckets', PROFILE))
    return [k for k in CACHED_BUCKETS if k.startswith(incomplete)]

def complete_emojis(ctx, param, incomplete):
    EMOJIS = {}
    EMOJIS = listAllEmojis()
    return [k for k in EMOJIS if k.startswith(incomplete)]

def complete_slack_names(ctx, param, incomplete):
    NAMES = {}
    NAMES = listAllSlackNames()
    return [k for k in NAMES if k.startswith(incomplete)]

def listAllEmojis():
    EMOJIS = []
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "emoji.lst")
    with open(DATA) as f:
        CONTENTS = f.read()
        for line in CONTENTS.split('\n'):
            if line:
                EMOJIS.append(line)
    return EMOJIS

def listAllSlackNames():
    NAMES = []
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "slack_channels.lst")
    with open(DATA) as f:
        CONTENTS = f.read()
        for line in CONTENTS.split('\n'):
            if line:
                NAMES.append(line.split(",")[0])
    return NAMES

def listAwsProfiles():
    CONFIG = Config('awstools')
    RESULT = detect_environment()
    NAMES = []
    MY_RESOURCES = importlib_resources.files("toolbox")
    if RESULT == 'gc-prod':
        for PROFILE in CONFIG.PROFILES:
            if PROFILE == 'latest' or PROFILE == 'IDP':
                continue
            NAMES.append(PROFILE)
    else:
        DATA = (MY_RESOURCES / "stage_accounts.lst")
        with open(DATA) as f:
            CONTENTS = f.read()
            for line in CONTENTS.split('\n'):
                if line:
                    NAMES.append(line.split(",")[0])
    return NAMES
