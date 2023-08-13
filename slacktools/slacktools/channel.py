#!/usr/bin/env python3

from . import auth
from slack_sdk.errors import SlackApiError
from toolbox.logger import Log

help = "manage channels on Slack"

def setup_args(subparser):
    subparser.add_argument(
        "-a", "--action",
        choices=["create", "addusers", "delusers", "archive", "topic", "unarchive"],
        help='action to take',
        required=True,
        dest='ACTION'
        )
    subparser.add_argument(
        "-n", "--name",
        help='name of the channel to create',
        required=False,
        dest='NAME'
        )
    subparser.add_argument(
        "-c", "--channelid",
        help = 'target channel ID',
        required=False,
        dest='ID'
        )
    subparser.add_argument(
        "-p", "--private",
        action='store_true',
        help='should the new channel be private',
        default=False,
        required=False,
        dest='PRIVATE'
        )
    subparser.add_argument(
        "-u", "--user",
        help='id of the target user',
        required=False,
        dest='USER'
        )
    subparser.add_argument(
        "-t", "--topic",
        help='body of the topic message',
        required=False,
        dest='TOPIC'
        )
    subparser.add_argument(
        "--profile",
        help='name of the user profile to use',
        default='default',
        required=False,
        dest='PROFILE'
        )
    
def main(args):
    SUBCOMMAND = {
        "create": channel_create(args.NAME,args.PRIVATE, args.PROFILE),
        "addusers": channel_user_add(args.ID, args.USER, args.PROFILE),
        "delusers": channel_user_delete(args.ID, args.USER, args.PROFILE),
        "archive": channel_archive(args.ID, args.PROFILE),
        "topic": channel_set_topic(args.ID, args.TOPIC, args.PROFILE),
        "unarchive": channel_unarchive(args.ID, args.PROFILE)
    }
    try: 
        return SUBCOMMAND[args.ACTION]
    except:
        Log.critical(f"Failed to perform action: {args.ACTION}")

def channel_create(channel_name, private, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    try:
        RESPONSE = SLACK_CLIENT.conversations_create(
            name = channel_name,
            is_private = private
        )
        NAME = RESPONSE['channel']['name']
        Log.info(f"created channel {NAME}")
        return RESPONSE
    except SlackApiError:
        Log.critical("Your account/token doesn't have the permission to do that")
    except:
        Log.critical("Failed to create channel")

def channel_user_add(channel_id, user_name, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    try:
        RESPONSE = SLACK_CLIENT.conversations_invite(
            channel = channel_id,
            users = user_name
        )
        NAME = RESPONSE['channel']['name']
        Log.info(f"Invited user to channel {NAME}")
        return RESPONSE
    except SlackApiError:
        Log.critical("Your account/token doesn't have the permission to do that")
    except:
        Log.critical("Failed to add user to channel") 

def channel_user_delete(channel_id, user_name, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    try:
        RESPONSE = SLACK_CLIENT.conversations_kick(
            channel = channel_id,
            user = user_name
        )
        NAME = RESPONSE['channel']['name']
        Log.info(f"Kicked user out of channel {NAME}")
        return RESPONSE
    except:
        Log.critical("Failed to kick user")

def channel_archive(channel_id, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    try:
        RESPONSE = SLACK_CLIENT.conversations_archive(channel = channel_id)
        NAME = RESPONSE['channel']['name']
        Log.info(f"Archived channel {NAME}")
        return RESPONSE
    except SlackApiError:
        Log.critical("Your account/token doesn't have the permission to do that")
    except:
        Log.critical("Failed to archive channel")

def channel_unarchive(channel_id, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    try:
        RESPONSE = SLACK_CLIENT.conversations_unarchive(channel = channel_id)
        NAME = RESPONSE['channel']['name']
        Log.info(f"Un-archived channel {NAME}")
        return RESPONSE
    except SlackApiError:
        Log.critical("Your account/token doesn't have the permission to do that")
    except:
        Log.critical("Failed to unarchive channel")

def channel_set_topic(channel_id, channel_topic, user_profile='default'):
    SLACK_CLIENT = auth.get_slack_session(user_profile)
    try:
        RESPONSE = SLACK_CLIENT.conversations_setTopic(
            channel = channel_id,
            topic = channel_topic
        )
        NAME = RESPONSE['channel']['name']
        Log.info(f"channel topic set to: {channel_topic} in {NAME}")
        return RESPONSE
    except SlackApiError:
        Log.critical("Your account/token doesn't have the permission to do that")
    except:
        Log.critical("Failed to set the channel topic")

if __name__ == "__main__":
    main()
