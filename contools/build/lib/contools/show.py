import sys, os
import click, json
from .client import Client
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

CONFLUENCE = Client()
CONFIG = Config('confluence')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from Confluence",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    log = Log('confluence.log', debug)

@show.command('config', help="retrieve the entire content of confluence's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def csp_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = CONFLUENCE.display_config(ctx.obj['profile'])

@show.command('access-token', help='API token for accessing the confluence functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = CONFLUENCE.get_access_token(user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = CONFLUENCE.get_access_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Confluence Menu: {INPUT}'
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
