import os, getpass
from toolbox.logger import Log
from configstore.configstore import Config
from slack_sdk import WebClient

def get_slack_session(user_profile):
    try:
        SLACK_SESSION = WebClient(token=get_slack_token(user_profile))
    except FileExistsError:
        MSG = 'Unable to connect to Slack. Verify your API token'
        LINK = 'https://github.com/stacksc/goat'
        CMD = None
        TITLE = 'GOAT'
        SUBTITLE = 'CRITICAL'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    return SLACK_SESSION
    '''
    if PROFILE is None or PROFILE['config'] == {}:
        Log.debug(f"Profile '{profile_name}' not found; creating a new profile")
        if jira_url is None:
            Log.warn("Please run the auth command first and setup a jira connection profile")
            sys.exit()
        while auth_mode != 'pass' and auth_mode != 'token':
            auth_mode = input('Please select authentication mode (pass/token): ')
        CONFIGSET = {
           'mode': auth_mode,
            'url': jira_url
        }
        CONFIG.add_profile(profile_name)
        CONFIG.set_config(CONFIGSET, profile_name=profile_name)
        if auth_mode == "pass":
            return setup_jira_pass_auth(profile_name)
        if auth_mode == "token":
            return setup_jira_token_auth(profile_name)
    '''

def get_slack_token(user_profile):
    CONFIG = Config('slacktools')
    PROFILE = CONFIG.get_profile(user_profile)

    if PROFILE is None or PROFILE['config'] == {}:
        Log.debug(f"Profile '{user_profile}' not found; creating a new profile")
        while True:
            if user_profile == 'default':
                ENV_TOKEN = os.getenv('SLACK_BOT_TOKEN')
                if ENV_TOKEN is not None:
                    SLACK_TOKEN = ENV_TOKEN
                    break
                Log.debug("Slack token not present in environmental variables")
            Log.info(f"Please enter the API token for Slack profile '{user_profile}'")
            SLACK_TOKEN = getpass.getpass(prompt="Slack token: ")
            if SLACK_TOKEN != "":
                break
        CONFIGSET = {
            'token': SLACK_TOKEN
        }
        CONFIG.create_profile(user_profile)
        CONFIG.update_config(CONFIGSET, user_profile)
    else:
        try:
            SLACK_TOKEN = PROFILE['config'][user_profile]['token']
        except:
            SLACK_TOKEN = PROFILE['config']['token']
    return SLACK_TOKEN

def get_slackclient_config():
    SLACK_CLIENT = get_slack_session(user_profile='default')
    CONFIG = Config('slacktools')
    RESULT = CONFIG.display_configstore()
    return RESULT
