import sys, os, re
import click, json
from .client import Client
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

ARTIFACTS = Client()
CONFIG = Config('jfrogtools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from jfrog artifacts",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    log = Log('artifacts.log', debug)

@show.command('config', help="retrieve the entire content of artifact's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def csp_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = ARTIFACTS.display_config(ctx.obj['profile'])

@show.command('access-token', help='API token for accessing the jfrog artifacts functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = ARTIFACTS.get_access_token(user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = ARTIFACTS.get_access_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

@show.command('repos', help='display repositories found in JFROG', context_settings={'help_option_names':['-h','--help']})
@click.option('-p', '--pattern', 'pattern', required=False, default=None, type=str)
@click.pass_context
def list_all_repos(ctx, pattern):
    RESULT = ARTIFACTS.list_all_repos(pattern, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
    return RESULT

@show.command('repo', help='display packages per repository selected in JFROG', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-p', '--pattern', 'pattern', required=False, default=None, type=str)
@click.pass_context
def list_repo(ctx, name, pattern):
    if name is None:
        DATA = []
        Log.info("gathering JFROG repository names, please wait...")
        RESULT = ARTIFACTS.list_all_repos(pattern, user_profile=ctx.obj['profile'])
        for I in RESULT:
            KEY = I["key"]
            DATA.append(KEY)
        DATA.sort()
        if DATA == []:
            Log.critical('unable to find any repository names')
        else:
            INPUT = 'JFROG manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0].strip()
            if name:
                Log.info(f"gathering repository {name} details now, please wait...")
            else:
                Log.critical("please select a repository to continue...")
        except:
            Log.critical("please select a repository to continue...")
    OUTPUT = ARTIFACTS.list_repo_details(name, user_profile=ctx.obj['profile'])
    if OUTPUT:
        Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
    OUTPUT = ARTIFACTS.list_artifacts(name, user_profile=ctx.obj['profile'])
    if OUTPUT:
        OUTPUT.sort()
        if OUTPUT == []:
            Log.critical('unable to find any repository names')
        INPUT = 'JFROG manager'
        CHOICE = runMenu(OUTPUT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            new = CHOICE.split('\t')[0].strip()
            if new:
                full = name + '/' + new
                Log.info(f"gathering repository {full} details now, please wait...")
            else:
                Log.critical("please select a repository to continue...")
        except:
            Log.critical("please select a repository to continue...")
    OUTPUT = ARTIFACTS.list_artifacts(full, user_profile=ctx.obj['profile'])
    if OUTPUT:
        for I in OUTPUT:
            Log.info(I)

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'JFROG Menu: {INPUT}'
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
