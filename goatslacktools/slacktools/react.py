#!/usr/bin/env python3

from . import auth, slack_converter, misc
from slack_sdk import errors
from toolbox.logger import Log

help = "react to a meessage to Slack"

def setup_args(subparser):
    subparser.add_argument(
        "-c", "--channel",
        help='channel or list of channel names (or ids). comma separated',
        required=True,
        dest='CHANNELS'
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
        required=False,
        default='default',
        dest='PROFILE'
        )

def main(args):
    RESPONSE = post_slack_reaction(args.CHANNEL, args.TIMESTAMP, args.EMOJI, args.PROFILE)
    Log.info("Reaction posted succesfully")
    return RESPONSE

def post_slack_reaction(channel_id, target_timestamp, emoji, user_profile='default'):
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

    #try:
    #    RESPONSE = SLACK_CLIENT.reactions_add(
    #        channel = channel_id,
    #        name = emoji,
    #        timestamp = target_timestamp
    #    )
    #    return RESPONSE
    RESPONSE = SLACK_CLIENT.reactions_add(
         channel = channel_id,
         name = emoji,
         timestamp = target_timestamp
    )
    #    return RESPONSE
    #except errors.SlackApiError:
    #    Log.critical("Unknown emoji name. Reaction not posted.")
    #except Exception:
    #    Log.critical("Failed to post a reaction or reaction already posted")

if __name__ == "__main__":
    main()
