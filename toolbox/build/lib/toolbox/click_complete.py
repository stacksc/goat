# these are some examples of click auto completion for projects and slack emoji names
import os, importlib_resources, glob
from pathlib import Path
from configstore.configstore import Config
from toolbox.misc import detect_environment

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
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "emoji.lst")
    with open(DATA) as f:
        CONTENTS = f.read()
        for line in CONTENTS.split('\n'):
            if line:
                EMOJIS.append(line)
    return EMOJIS