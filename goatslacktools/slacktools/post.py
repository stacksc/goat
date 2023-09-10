#!/usr/bin/env python3

from . import auth, slack_converter
from toolbox.logger import Log

help = "post a meessage to Slack"

def setup_args(subparser):
    subparser.add_argument(
        "-c", "--channel",
        help='channel or list of channel names (or ids). comma separated',
        required=True,
        dest='CHANNELS'
        )
    subparser.add_argument(
        "-m", "--messagetext",
        help='body of the message to send',
        required=True,
        dest='TEXT'
        )
    subparser.add_argument(
        "-r", "--replyto",
        help='timestamp of the message to reply to',
        required=False,
        dest='REPLY'
        )
    subparser.add_argument(
        "-p", "--profile",
        help='name of the user profile to use',
        required=False,
        default='default',
        dest='PROFILE'
        )

def main(args):
    RESPONSES = post_slack_message(args.CHANNELS, args.TEXT, args.REPLY, args.PROFILE)
    for RESPONSE in RESPONSES:    
        Log.info(f"Message sent at {RESPONSE['ts']}")
    return RESPONSES

def post_slack_message(target_channels, message_text, thread_timestamp="", user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    TARGET_CHANNELS = []

    try:
        TARGET_CHANNELS = slack_converter.convert_slack_names(target_channels)
    except:
        TARGET_CHANNELS = target_channels

    RESPONSES = []
    if post_prereq(target_channels, thread_timestamp):
        for TARGET_CHANNEL in TARGET_CHANNELS:
            try:
                RESPONSE = SLACK_CLIENT.chat_postMessage(
                    channel = TARGET_CHANNEL,
                    text = message_text,
                    thread_ts = thread_timestamp
                )
                RESPONSES.append(RESPONSE)
            except Exception as e:
                Log.critical(f"Failed to post the message: {e}")
        return RESPONSES
    else:
        Log.critical("Can't reply to a message in multiple channels")

def post_prereq(channels, reply):
# makes sure channels contains just a single channel ID when reply var is set
# as it is impossible to reply to a single message in multiple threads
    if reply == "":
        return True
    else:
        if type(channels) is list:
            return False
        else:
            return True

if __name__ == "__main__":
    main()
