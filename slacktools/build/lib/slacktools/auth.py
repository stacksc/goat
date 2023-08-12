import os, getpass
from toolbox.logger import Log
from configstore.configstore import Config
from slack_sdk import WebClient
from toolbox.getpass import getOtherToken

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
            SLACK_TOKEN = getOtherToken("Slack")
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
