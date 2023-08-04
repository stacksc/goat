# these were pulled from comms
# save for later because pyps does not have permissions to create channels yet

#@comms.command(help='initiate code-red comms (P0/P1)', context_settings={'help_option_names':['-h','--help']})
#@click.option('-s', '--summary', help="title of the ticket", type=str, required=True)
#def code_red(summary):
#    TICKET = issue.create(CODE_RED['project'], summary)
#    NAME = f"{TICKET['key']}{CODE_RED['channel']}"
#    CHANNEL = channel.channel_create(NAME, True)
#    for USER in CODE_RED['team']:
#        channel.channel_user_add(CHANNEL['id'],USER)
#    channel.channel_set_topic(CHANNEL['id'],summary)
#
#def generate_text(change, collection, template):
#    return f"{collection[template]} {change}"
