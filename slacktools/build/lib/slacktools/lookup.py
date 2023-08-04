#!/usr/bin/env python3

# DO NOT USE. THIS IS VERY, VERY SLOW AND HAS UNKNOWN RESULT. 
# FURTHER TESTING REQUIRED ON NON-PROD SLACK

from . import auth
from toolbox.logger import Log

help = "find an ID for a given channel name (warning, it can be slow!)"

def setup_args(subparser):
    subparser.add_argument(
        "-c", "--channelname",
        help='channel name to use',
        required=True,
        dest='CHANNEL'
        )
    subparser.add_argument(
        "-p", "--profile",
        help='name of the user profile to use',
        required=False,
        default='default',
        dest='PROFILE'
        )
    
def main(args):
    RESPONSE = lookupChannel(args.CHANNEL, args.PROFILE)
    Log.info(f"Found channel name: {RESPONSE['id']}")
    return RESPONSE

def lookupChannel(channel_name, profilename='default'):
    SLACK_CLIENT = auth.get_slack_session(profilename)
    try:
        ALL_CHANNELS = SLACK_CLIENT.conversations_list()
        for CHANNEL in ALL_CHANNELS:
            if CHANNEL['name'] == channel_name:
                return CHANNEL
    except:
        Log.critical("Failed to lookup the channel ID")

if __name__ == "__main__":
    main()