import sys, click, getpass
from toolbox.logger import Log
from toolbox.getpass import getCreds
from configstore.configstore import Config
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import pprint
import requests
import datetime

CONFIG = Config('azdev')

@click.command(help="setup or change authentication settings for AZ DevOps", context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--url', help='address of the Organization URL', default='https://dev.azure.com/baxtercu', required=False, type=str)
@click.pass_context
def auth(ctx, url):
    profile = ctx.obj['PROFILE']
    if profile is None:
        profile = 'default'
    get_session(url, profile)

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

def get_session(url=None, profile_name='default'):
    auth_mode = 'pass' # default to pass, it really is a PAT though
    PROFILE = CONFIG.get_profile(profile_name)
    if PROFILE is None or PROFILE['config'] == {}:
        Log.debug(f"Profile '{profile_name}' not found; creating a new profile")
        if url is None:
            Log.warn("Project not found. Please verify it or make sure at least one azdev profile is connected to the right server")
            sys.exit()
        while auth_mode != 'pass':
            auth_mode = 'pass'
        if check_for_registered_default() is False:
            DEFAULT_PROFILE = input('\nIs this going to be your default profile (Y/N)? : ')
        else:
            DEFAULT_PROFILE = 'N'
        CONFIG.create_profile(profile_name)
        CONFIG.update_config(auth_mode, 'mode', profile_name=profile_name)
        CONFIG.update_config(url, 'url', profile_name=profile_name)
        CONFIG.update_config(DEFAULT_PROFILE, 'default', profile_name=profile_name)
        if auth_mode == "pass":
            return setup_pass_auth(profile_name)
    else:
        try:
            URL = CONFIG.get_config('url', profile_name=profile_name)
            MODE = CONFIG.get_config('mode', profile_name=profile_name)
            if MODE == 'pass':
                USER = CONFIG.get_config('user', profile_name=profile_name)
                PASS = CONFIG.get_config('pass', profile_name=profile_name)
                return get_session_pass_auth(URL, USER, PASS)
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

def setup_pass_auth(profile_name):
    while True:
        USER, PASS = getCreds()
        if USER != '' and PASS != '':
            break
    try:
        URL = CONFIG.get_config('url', profile_name=profile_name)
        SESSION = get_session_pass_auth(URL, USER, PASS)
    except:
        MSG = 'Failed to login to AZ DevOps. Please verify your login details, server URL etc.'
        LINK = 'https://github.com/stacksc/goat'
        CMD = None
        TITLE = 'GOAT'
        SUBTITLE = 'CRITICAL'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    CONFIG.update_config(USER, 'user', profile_name=profile_name)
    CONFIG.update_config(PASS, 'pass', profile_name=profile_name)
    cache_facts(SESSION, profile_name)
    return SESSION
   
def get_projects(core_client):
    PROJECTS = []
    try:
        get_projects_response = core_client.get_projects()
        index = 0
        while get_projects_response:
            for project in get_projects_response:
                PROJECTS.append(project.name)
            # Check if there's a continuation token for pagination
            continuation_token = getattr(get_projects_response, 'continuation_token', None)
            if continuation_token:
                get_projects_response = core_client.get_projects(continuation_token=continuation_token)
            else:
                get_projects_response = None
    except Exception as e:
        print(f"Error retrieving projects: {e}")
        return None
    return PROJECTS

def cache_facts(session, profile_name):
    Log.info("Caching some system info now to save time later... please wait")
    PROJECT_KEYS = {}
    PROJECTS = get_projects(session)
    for PROJECT in PROJECTS:
        PROJECT_KEYS[PROJECT] = {}
    CONFIG.update_metadata(PROJECT_KEYS, 'projects', profile_name)
    Log.info("Caching facts complete")

def get_session_pass_auth(url, user, token):
    try:
        CREDENTIALS = BasicAuthentication('', token)
        SESSION = Connection(base_url=url, creds=CREDENTIALS)
        CLIENT = SESSION.clients.get_core_client()
    except Exception as e:
        print(f"Error establishing connection: {e}")
        return None
    return CLIENT

def get_user_creds(user_profile):
    AUTH_MODE = CONFIG.get_config('mode', user_profile)
    if AUTH_MODE == 'pass':
        USERNAME = CONFIG.get_config('user', user_profile)
        PASSWORD = CONFIG.get_config('pass', user_profile)
        return [USERNAME, PASSWORD]

def get_url(userprofile):
    return CONFIG.get_config('url', userprofile)

@click.command(help="manage configuration details for the AZ DevOps server on this profile", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--default', help='mark this profile as the default profile to use for AZ DevOps', is_flag=True)
@click.option('-s', '--show', help='show the entire config for the AZ DevOps server on this profile', is_flag=True)
@click.option('-t', '--token', 'token', help='show the personal access token for the AZ DevOps server on this profile', is_flag=True)
@click.pass_context
def config(ctx, default, show, token):
    profile = ctx.obj['PROFILE']
    if default is True:
        CURRENT_DEFAULT_PROFILE = get_default_profile()
        RESULT = get_default_url()
        set_default_url(profile, CURRENT_DEFAULT_PROFILE)
    else:
        if token:
            RESULT = get_access_token(user_profile=profile)
            Log.info(f"Personal Access Token: {RESULT}")
            RESULT = get_access_token_age(user_profile=profile)
            Log.info(f"Access token has been created {RESULT} minutes ago")
        else:
            RESULT = get_my_config()
    return RESULT

# worker functions required for non-click usage
def get_azdev_config(user_profile='default'):
    RESULT = CONFIG.display_profile(user_profile)
    return RESULT

def get_my_config():
    RESULT = CONFIG.display_configstore()
    return RESULT

def get_session_based_on_key(key):
    PROFILES = get_user_profile_based_on_key(key, False)
    if len(PROFILES) == 0:
        Log.critical('Project key not found on any of the AZ DevOps servers configured across all profiles')
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
    URL = get_url(PROFILE)
    CREDS = get_user_creds(PROFILE)
    SESSION = get_session_pass_auth(URL, CREDS[0], CREDS[1])
    return SESSION, PROFILE

def get_user_profile_based_on_key(key, return_first=True):
    try:
        if type(key) is str:
            PROJECT_KEY = key.split('-')[0]
        else:
            PROJECT_KEY = key[0].split('-')[0]
    except IndexError:
        Log.critical("You must provide a issue key, project key, or a user profile to use azdev")   
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

def get_property(property_name, user_profile='default'):
    CONFIG = Config('azdev')
    AZ_CONFIG = CONFIG.get_config(property_name, user_profile)
    if AZ_CONFIG is None:
        Log.critical('please setup azdev - auth setup - before proceeding with this option')
    return AZ_CONFIG

def get_access_token(user_profile='default'):
    TOKEN_DATA = get_property('pass', user_profile)
    return TOKEN_DATA

def get_access_token_age(user_profile='default'):
    CREATED_ON = float(CONFIG.get_metadata('created_at', user_profile))
    TIME_NOW = float(datetime.datetime.now().timestamp())
    RESULT = TIME_NOW - CREATED_ON
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    return RESULT

