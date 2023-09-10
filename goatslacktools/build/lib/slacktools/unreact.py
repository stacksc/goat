#!/usr/bin/env python3

from . import auth, slack_converter, misc
from toolbox.logger import Log
from slack_sdk import errors

help = "remove a reaction from a meessage in Slack"

def setup_args(subparser):
    subparser.add_argument(
        "-c", "--channelid",
        help='target channel ID',
        required=True,
        dest='CHANNEL'
        )
    subparser.add_argument(
        "-t", "--timestamp",
        help='timestamp of the target message',
        required=True,
        dest='TIMESTAMP'
        )
    subparser.add_argument(
        "-e", "--emoji",
        help='name of the emoji to use',
        required=True,
        dest='EMOJI'
        )
    subparser.add_argument(
        "-p", "--profile",
        help='name of the user profile to use',
        default='default',
        required=False,
        dest='PROFILE'
        )

def main(args):
    RESPONSE = delete_slack_reaction(args.CHANNEL, args.TIMESTAMP, args.EMOJI, args.PROFILE)
    Log.info("Reaction deleted succesfully")
    return RESPONSE

def delete_slack_reaction(channel_id, target_timestamp, emoji, user_profile='default'):
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

    if(type(emoji)) is tuple:
        emoji = misc.convertTuple(emoji)
    try:
        RESPONSE = SLACK_CLIENT.reactions_remove(
            channel = channel_id,
            name = emoji,
            timestamp = target_timestamp
        )
        return RESPONSE
    except errors.SlackApiError as e:
        Log.critical(f"Unknown emoji name. Reaction couldn't be removed: {e}")
    except:
        Log.critical("Failed to remove a reaction or reaction already removed")


if __name__ == "__main__":
    main()
