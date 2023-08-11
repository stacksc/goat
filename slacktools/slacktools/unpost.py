#!/usr/bin/env python3

from . import auth, slack_converter, misc
from toolbox.logger import Log

help = "delete a meessage from Slack"

def setup_args(subparser):
    subparser.add_argument(
        "-c", "--channelid",
        help='target channels ID',
        required=True,
        dest='CHANNELS'
        )
    subparser.add_argument(
        "-t", "--timestamp",
        required=True,
        help='timestamp of the target message',
        dest='TIMESTAMP'
        )
    subparser.add_argument(
        "-p", "--profile",
        help='name of the user profile to use',
        required=False,
        default='default',
        dest='PROFILE'
        )

def main(args):
    RESPONSE = delete_slack_message(args.CHANNEL, args.TIMESTAMP, args.PROFILE)
    Log.info(f"Message {RESPONSE['ts']} deleted")
    return RESPONSE

def delete_slack_message(channel_id, target_timestamp, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)

    try:
        channel_id = slack_converter.convert_slack_names(channel_id)
    except:
        pass

    # convert channel and emoji to strings
    if(type(channel_id)) is tuple:
        channel_id = misc.convertTuple(channel_id)
    elif(type(channel_id)) is list:
        channel_id = ' '.join(channel_id)

    try:
        RESPONSE = SLACK_CLIENT.chat_delete(
                    channel = channel_id,
                    ts = target_timestamp
        )
        return RESPONSE
    except FileNotFoundError:
        Log.critical("Failed to delete the message")

if __name__ == "__main__":
    main()
