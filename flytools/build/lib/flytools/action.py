import sys, os
import click, json
from .client import Client
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

FLY = Client()
CONFIG = Config('flytools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="action tasks for concourse runway",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def action(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    log = Log('flytools.log', debug)

@action.command('trigger', help="trigger a runway post-deploy job with it's service team name", context_settings={'help_option_names':['-h','--help']})
@click.argument('team', type=str, required=True)
@click.pass_context
def trigger(ctx, team):
    if not team:
        Log.critical("please provide the team argument")
    RESULT = FLY.trigger_post_deploy_job(team, user_profile=ctx.obj['profile'])
    if RESULT:
        Log.info(RESULT)
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')
    return RESULT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Concourse Menu: {INPUT}'
    for data in DATA:
        COUNT = COUNT + 1
        RESULTS = []
        RESULTS.append(data)
        FINAL.append(RESULTS)
    SUBTITLE = f'showing {COUNT} available object(s)'
    JOINER = '\t\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, SUBTITLE)
    CHOICE = FINAL_MENU.display()
    return CHOICE
