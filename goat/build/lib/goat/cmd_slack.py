#!/usr/bin/env python3
import click
from slacktools.auth import get_slackclient_config
from slacktools.post import post_slack_message
from slacktools.react import post_slack_reaction
from slacktools.unpost import delete_slack_message
from slacktools.unreact import delete_slack_reaction
from slacktools.channel import channel_set_topic, channel_user_add, channel_user_delete, channel_create, channel_archive, channel_unarchive
from toolbox.logger import Log
from toolbox.click_complete import complete_emojis
from toolbox import misc

MESSAGE="Slack CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + 'DEFAULT' + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', help='User profile to use for connecting to Slack', required=False, default='default', type=str)
@click.pass_context
def slack(ctx, profile):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile
    pass

@slack.command(help='post a meessage to a given channel(s)', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('channel', nargs=-1, type=str, required=True)
@click.option('-m', '--message', help='Text to include in the message', required=True, type=str)
@click.option('-r', '--reply', help='TS of the message to reply to', required=False, type=str)
@click.pass_context
def post(ctx, channel, message, reply):
    profile = ctx.obj['PROFILE']
    RESPONSES = post_slack_message(channel, message, reply, profile)
    for RESPONSE in RESPONSES:
        Log.info(f"Message sent at {RESPONSE['ts']}")

@slack.command(help='post a reaction to a given message in specific channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('channel', nargs=-1, type=str, required=True)
@click.option('-t', '--timestamp', help='timestamp of the target message', required=True, type=str)
@click.option('-e', '--emoji', help='emoji name to react with', required=True, type=str, shell_complete=complete_emojis)
@click.pass_context
def react(ctx, channel, timestamp, emoji):
    profile = ctx.obj['PROFILE']
    post_slack_reaction(channel, timestamp, emoji, profile)
    Log.info("Reaction posted")

@slack.command(help='delete a meessage in a given channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('channel', nargs=-1, type=str, required=True)
@click.option('-t', '--timestamp', help='Text to include in the message', required=True, type=str)
@click.pass_context
def unpost(ctx, channel, timestamp):
    profile = ctx.obj['PROFILE']
    delete_slack_message(channel, timestamp, profile)
    Log.info(f"Message deleted")

@slack.command(help='remove a reaction to a given message in a specific channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('channel', nargs=-1, type=str, required=True)
@click.option('-t', '--timestamp', help='timestamp of the target message', required=True, type=str)
@click.option('-e', '--emoji', help='emoji name to react with', required=True, type=str)
@click.pass_context
def unreact(ctx, channel, timestamp, emoji):
    profile = ctx.obj['PROFILE']
    delete_slack_reaction(channel, timestamp, emoji, profile)
    Log.info("Reaction removed")

@click.group(help='manage Slack channels; create, archive, invite users etc', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def channel(ctx):
    pass

@channel.command('create', help='create a new slack channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-n', '--name', help='name for the new channel', required=False, type=str)
@click.option('-p', '--private', help='should the new channel be private', required=False, default=False, type=bool)
@click.pass_context
def create(ctx, name, private):
    profile = ctx.obj['PROFILE']
    channel_create(name,private, profile)

@channel.command('adduser', help='add (invite) new user to the channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-i', '--id', help='target channel', required=False, type=str)
@click.option('-u', '--user', help='user id to invite to the channel', required=False, type=str)
@click.pass_context
def adduser(ctx, id, user):
    profile = ctx.obj['PROFILE']
    channel_user_add(id,user, profile)

@channel.command('deluser', help='delete (kick) a user from the channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-i', '--id', help='target channel', required=False, type=str)
@click.option('-u', '--user', help='user id to kick from the channel', required=False, type=str)
@click.pass_context
def deluser(ctx, id, user):
    profile = ctx.obj['PROFILE']
    channel_user_delete(id,user, profile)

@channel.command('archive', help='set channel status to "archived"', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-i', '--id', help='target channel', required=False, type=str)
@click.pass_context
def archive(ctx, id):
    profile = ctx.obj['PROFILE']
    channel_archive(id, profile)

@channel.command('unarchive', help='remove "archived" status from channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-i', '--id', help='target channel', required=False, type=str)
@click.pass_context
def unarchive(ctx, id):
    profile = ctx.obj['PROFILE']
    channel_unarchive(id, profile)

@channel.command('topic', help='set the topic message for the channel', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-i', '--id', help='target channel', required=False, type=str)
@click.option('-t', '--topic', help='what to put in the topic channel', required=False, type=str)
@click.pass_context
def topic(ctx, id, topic):
    profile = ctx.obj['PROFILE']
    channel_set_topic(id, topic, profile)

@slack.command(help="retrieve the entire content of slacktools's configstore", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def config(ctx):
    RESULT = get_slackclient_config()
    return RESULT

slack.add_command(post)
slack.add_command(react)
slack.add_command(unpost)
slack.add_command(unreact)
slack.add_command(channel)
