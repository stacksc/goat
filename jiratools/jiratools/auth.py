import sys, click, getpass
from jira import JIRA
from toolbox.logger import Log
from toolbox.getpass import getCreds
from configstore.configstore import Config
from toolbox.click_complete import complete_jira_profiles

CONFIG = Config('jiratools')

@click.command(help="setup or change authentication settings for JIRA", context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--url', help='address of the jira server', required=True, type=str)
@click.option('-m', '--mode', help="choose authentication mode", required=False, default='pass', type=click.Choice(['token', 'pass']))
@click.pass_context
def auth(ctx, url, mode):
    profile = ctx.obj['PROFILE']
    if profile is None:
        profile = 'default'
    get_jira_session(url, mode, profile)

def set_default_url(profile, current):
    for PROFILE in CONFIG.PROFILES:
        if profile == PROFILE:
            CONFIG.update_config('Y', 'default', PROFILE)
            try:
                VAL = CONFIG.get_config('default', PROFILE)
                URL = CONFIG.get_config('url', PROFILE)
                if VAL == 'Y':
                    Log.info(f'{profile} has been updated to default')
                    CONFIG.update_config('N', 'default', current)
                else:
                    Log.critical(f'{profile} was not updated to default due to an error in configstore')
            except:
                Log.critical(f'{profile} was not updated to default due to an error in configstore')

def get_default_profile():
    PROFILE = 'default'
    for PROFILE in CONFIG.PROFILES:
        VAL = CONFIG.get_config('default', PROFILE)
        if VAL == 'Y' or VAL == 'y':
            return PROFILE
    return PROFILE

def get_default_url():
    URL = 'default'
    for PROFILE in CONFIG.PROFILES:
        VAL = CONFIG.get_config('default', PROFILE)
        if VAL == 'Y' or VAL == 'y':
            URL = CONFIG.get_config('url', PROFILE)
            return URL
    return URL

def check_for_registered_default():
    for PROFILE in CONFIG.PROFILES:
        VAL = CONFIG.get_config('default', PROFILE)
        if VAL == 'Y':
            return True
    return False

def get_jira_session(jira_url=None, auth_mode=None, profile_name='default'):
    PROFILE = CONFIG.get_profile(profile_name)
    if PROFILE is None or PROFILE['config'] == {}:
        Log.debug(f"Profile '{profile_name}' not found; creating a new profile")
        if jira_url is None:
            Log.warn("Project not found. Please verify it or make sure at least one goat/jiratools profile is connected to the right server")
            sys.exit()
        while auth_mode != 'pass' and auth_mode != 'token':
            auth_mode = input('\nPlease select authentication mode (pass/token): ')
        if check_for_registered_default() is False:
            DEFAULT_PROFILE = input('\nIs this going to be your default profile (Y/N)? : ')
        else:
            DEFAULT_PROFILE = 'N'
        CONFIG.create_profile(profile_name)
        CONFIG.update_config(auth_mode, 'mode', profile_name=profile_name)
        CONFIG.update_config(jira_url, 'url', profile_name=profile_name)
        CONFIG.update_config(DEFAULT_PROFILE, 'default', profile_name=profile_name)
        if auth_mode == "pass":
            return setup_jira_pass_auth(profile_name)
        if auth_mode == "token":
            return setup_jira_token_auth(profile_name)
    else:
        try:
            JIRA_URL = CONFIG.get_config('url', profile_name=profile_name)
            JIRA_MODE = CONFIG.get_config('mode', profile_name=profile_name)
            if JIRA_MODE == 'pass':
                JIRA_USER = CONFIG.get_config('user', profile_name=profile_name)
                JIRA_PASS = CONFIG.get_config('pass', profile_name=profile_name)
                return get_jira_session_pass_auth(JIRA_URL, JIRA_USER, JIRA_PASS)
            if JIRA_MODE == 'token':
                JIRA_TOKEN = CONFIG.get_config('token', profile_name=profile_name)
                return get_jira_session_token_auth(JIRA_URL, JIRA_TOKEN)
            else:
                Log.critical("something went wrong")
        except:
            Log.warn(f"Profile {profile_name} might be corrupted. Would you like to delete it?")
            CHOICE = ""
            while CHOICE != "Y" and CHOICE != "y" and CHOICE != "N" and CHOICE != "n":
                CHOICE = input("Delete profile? (Y/N): ")
            if CHOICE == "Y" or CHOICE == "y":
                CONFIG.clear_profile(profile_name)
                Log.info(f"Profile {profile_name} has been deleted. Please try again.")
                sys.exit()
            else:
                Log.warn(f"Profile {profile_name} not deleted. Please verify it manually and try again")

def setup_jira_pass_auth(profile_name):
    while True:
        JIRA_USER, JIRA_PASS = getCreds()
        if JIRA_USER != '' and JIRA_PASS != '':
            break
    try:
        JIRA_URL = CONFIG.get_config('url', profile_name=profile_name)
        JIRA_SESSION = get_jira_session_pass_auth(JIRA_URL, JIRA_USER, JIRA_PASS)
    except:
        MSG = 'Failed to login to Jira. Please verify your login details, server URL etc.'
        LINK = 'https://github.com/stacksc/goat'
        CMD = None
        TITLE = 'GOAT'
        SUBTITLE = 'CRITICAL'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    CONFIG.update_config(JIRA_USER, 'user', profile_name=profile_name)
    CONFIG.update_config(JIRA_PASS, 'pass', profile_name=profile_name)
    cache_jira_facts(JIRA_SESSION, profile_name)
    return JIRA_SESSION
    
def setup_jira_token_auth(profile_name):
    while True:
        JIRA_TOKEN = getpass.getpass("JIRA API Token: ")
        if JIRA_TOKEN != '':
            break
    try:
        JIRA_URL = CONFIG.get_config('url', profile_name=profile_name)
        JIRA_SESSION = get_jira_session_token_auth(JIRA_URL, JIRA_TOKEN)
    except:
        MSG = 'Failed to login to Jira. Please verify your login details, server URL etc.'
        LINK = 'https://github.com/stacksc/goat'
        CMD = None
        TITLE = 'GOAT'
        SUBTITLE = 'CRITICAL'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    CONFIG.update_config(JIRA_TOKEN, 'token', profile_name=profile_name)
    cache_jira_facts(JIRA_SESSION, profile_name)
    return JIRA_SESSION

def cache_jira_facts(jira_session, profile_name):
    Log.info("Caching some system info now to save time later... please wait")
    PROJECTS = jira_session.projects()
    PROJECT_KEYS = {}
    for PROJECT in PROJECTS:
        PROJECT_KEYS[PROJECT.key] = {}
    CONFIG.update_metadata(PROJECT_KEYS, 'projects', profile_name)
    Log.info("Caching facts complete")

def get_jira_session_pass_auth(jira_url, jira_user, jira_pass):
    SESSION = JIRA(
        basic_auth=(jira_user, jira_pass),
        options={'server': jira_url}
    )
    return SESSION

def get_jira_session_token_auth(jira_url, jira_token):
    SESSION = JIRA(
        token_auth=jira_token,
        options={'server': jira_url}
    )
    return SESSION

def get_jira_user_creds(user_profile):
    JIRA_AUTH_MODE = CONFIG.get_config('mode', user_profile)
    if JIRA_AUTH_MODE == 'pass':
        JIRA_USERNAME = CONFIG.get_config('user', user_profile)
        JIRA_PASSWORD = CONFIG.get_config('pass', user_profile)
        return [JIRA_USERNAME, JIRA_PASSWORD]
    if JIRA_AUTH_MODE == 'token':
        JIRA_USERNAME = CONFIG.get_config('user', user_profile)
        JIRA_TOKEN = CONFIG.get_config('token', user_profile)
        return [JIRA_USERNAME, JIRA_TOKEN]

def get_jira_url(userprofile):
    return CONFIG.get_config('url', userprofile)

@click.command(help="manage configuration details for the Jira server on this profile", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--default', help='mark this profile as the default profile to use for JIRA', is_flag=True)
@click.option('-s', '--show', help='show the entire config for the JIRA server on this profile', is_flag=True)
@click.pass_context
def config(ctx, default, show):
    profile = ctx.obj['PROFILE']
    if default is True:
        CURRENT_DEFAULT_PROFILE = get_default_profile()
        RESULT = get_default_url()
        set_default_url(profile, CURRENT_DEFAULT_PROFILE)
    else:
        RESULT = get_jira_config(profile)
    return RESULT

# worker functions required for non-click usage
def get_jira_config(user_profile='default'):
    RESULT = CONFIG.display_profile(user_profile)
    return RESULT

def get_jiraclient_config():
    RESULT = CONFIG.display_configstore()
    return RESULT

def get_jira_session_based_on_key(key):
    PROFILES = get_user_profile_based_on_key(key, False)
    if len(PROFILES) == 0:
        Log.critical('Project key not found on any of the Jira servers configured across all profiles')
    elif len(PROFILES) == 1:
        PROFILE = PROFILES[0]
    else:
        Log.info(f"Found multiple profiles for project key {key}")
        for INDEX in range(len(PROFILES)):
            Log.info(f"{INDEX}: {PROFILES[INDEX]['user_profile']}")
        while True:
            PROFILE_CHOICE = input('Please input the ID of the profile to use: ')
            if PROFILE_CHOICE != "":
                break
        try:
            PROFILE = PROFILES[PROFILE_CHOICE]
        except:
            Log.critical('Invalid profile choice. Exiting')
    JIRA_URL = get_jira_url(PROFILE)
    JIRA_CREDS = get_jira_user_creds(PROFILE)
    JIRA_SESSION = get_jira_session_pass_auth(JIRA_URL, JIRA_CREDS[0], JIRA_CREDS[1])
    return JIRA_SESSION, PROFILE

def get_user_profile_based_on_key(key, return_first=True):
    try:
        if type(key) is str:
            PROJECT_KEY = key.split('-')[0]
        else:
            PROJECT_KEY = key[0].split('-')[0]
    except IndexError:
        Log.critical("You must provide a issue key, project key, or a user profile to use jiratools")   
    FOUND_PROFILES = []
    for PROFILE in CONFIG.PROFILES:
        CACHED_PROJECTS = CONFIG.get_metadata('projects', PROFILE)
        if CACHED_PROJECTS is not None:
            for CACHED_PROJECT in CACHED_PROJECTS:
                if PROJECT_KEY == CACHED_PROJECT:
                    FOUND_PROFILES.append(PROFILE)
    if return_first:
        try:
            return FOUND_PROFILES[0]
        except IndexError:
            return None
    else:
        return FOUND_PROFILES

