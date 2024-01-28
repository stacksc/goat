# these are some examples of click auto completion for projects and slack emoji names
import os, glob
from pathlib import Path
from configstore.configstore import Config
from toolbox.misc import detect_environment
try:
    import importlib_resources as resources
except:
    from importlib import resources

def complete_oci_profiles(ctx, param, incomplete):
    CONFIG = Config('ocitools')
    DATA = []
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        if 'latest' not in PROFILE:
            NAMES.append(PROFILE.strip())
    if NAMES:
        return [k for k in NAMES if k.startswith(incomplete)]
    else:
        return None

def complete_aws_profiles(ctx, param, incomplete):
    CONFIG = Config('awstools')
    DATA = []
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        if 'latest' not in PROFILE:
            NAMES.append(PROFILE.strip())
    if NAMES:
        return [k for k in NAMES if k.startswith(incomplete)]
    else:
        return None

def complete_aws_regions(ctx, param, incomplete):
    CONFIG = Config('awstools')
    DATA = []
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        if 'latest' not in PROFILE:
            NAMES.append(PROFILE.strip())
    for PROFILE in NAMES:
        try:
            for ENTRY in CONFIG.PROFILES[PROFILE]['metadata']['cached_regions']:
                DATA_ENTRY = {}
                if ENTRY != 'last_cache_update':
                    DATA.append(ENTRY)
        except:
            pass
    if DATA:
        return [k for k in DATA if k.startswith(incomplete)]
    else:
        return None

def complete_oci_regions(ctx, param, incomplete):
    CONFIG = Config('ocitools')
    DATA = []
    NAMES = []
    for PROFILE in CONFIG.PROFILES:
        if 'latest' not in PROFILE:
            NAMES.append(PROFILE.strip())
    for PROFILE in NAMES:
        try:
            for ENTRY in CONFIG.PROFILES[PROFILE]['metadata']['cached_regions']:
                DATA_ENTRY = {}
                if ENTRY != 'last_cache_update':
                    DATA.append(ENTRY)
        except:
            pass
    if DATA:
        return [k for k in DATA if k.startswith(incomplete)]
    else:
        return None

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
    for KEY in glob.glob(HOME + "/goat/.*key"):
        if os.path.isfile(KEY):
            KEY = str(Path(KEY).stem.replace(".",""))
            BASE = os.path.basename(KEY)
            NAMES.append(str(BASE))
    return [k for k in NAMES if k.startswith(incomplete)]

def complete_azdev_projects(ctx, param, incomplete):
    from azdevops.azdevclient import AzDevClient
    AZDEV = AzDevClient()
    CONFIG = Config('azdev')
    CACHED_PROJECTS = {}
    CACHED_PROJECTS.update(CONFIG.get_metadata('projects', AZDEV.get_default_profile()))
    return [k for k in CACHED_PROJECTS if k.startswith(incomplete)]

def complete_projects(ctx, param, incomplete):
    from jiratools.auth import get_default_profile
    CONFIG = Config('jiratools')
    CACHED_PROJECTS = {}
    CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
    return [k for k in CACHED_PROJECTS if k.startswith(incomplete)]

def complete_emojis(ctx, param, incomplete):
    EMOJIS = {}
    EMOJIS = listAllEmojis()
    return [k for k in EMOJIS if k.startswith(incomplete)]

def listAllEmojis():
    EMOJIS = []
    MY_RESOURCES = resources.files("toolbox")
    DATA = (MY_RESOURCES / "emoji.lst")
    with open(DATA) as f:
        CONTENTS = f.read()
        for line in CONTENTS.split('\n'):
            if line:
                EMOJIS.append(line)
    return EMOJIS
