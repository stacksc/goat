import sys, os
import click, json
from .client import Client
from .auth import update_latest_profile
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

GIT = Client()
CONFIG = Config('gitools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from Git",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common Git user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False

    if ctx.obj['setup'] == True:
        RESULT = GIT.setup_access(ctx.obj['profile'])
        if RESULT:
            Log.info("git settings saved succesfully")
            update_latest_profile(ctx.obj['profile'])
    log = Log('gitools.log', debug)

@show.command('config', help="retrieve the entire content of gitools' configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def git_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = GIT.display_config(ctx.obj['profile'])

@show.command("repos", help='show all repos registered in git', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_repos(ctx, raw=False):
    OUTPUT = GIT.list_all_repos(raw)
    if OUTPUT == []:
        Log.critical('unable to find any repositories')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("user", help='show user information registered in git for a specific user', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_user(ctx, name, raw=False):
    if name is None:
        DATA = []
        Log.info("gathering git user names, please wait...")
        OUTPUT = GIT.list_all_users(raw)
        for NAME in OUTPUT:
            DATA.append(NAME['userId'])
        DATA.sort()
        if OUTPUT == []:
            Log.critical('unable to find any git users')
        else:
            INPUT = 'user manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering user {name} information now, please wait...")
            else:
                Log.critical("please select a user-id to continue...")
        except:
            Log.critical("please select a user-id to continue...")

    OUTPUT = GIT.list_user(name, raw)
    if OUTPUT == []:
        Log.critical('unable to find any services')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("projects", help='list all projects in Gitlab that you have access to', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', required=False, default=None, type=str)
@click.pass_context
def list_projects(ctx, raw, pattern):
    OUTPUT = GIT.list_my_projects(pattern, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT == []:
        Log.critical('unable to find any project information')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("groups", help='list all groups in Gitlab that you have access to', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', required=False, default=None, type=str)
@click.pass_context
def list_groups(ctx, raw, pattern):
    OUTPUT = GIT.list_my_groups(pattern, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT == []:
        Log.critical('unable to find any group information')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("group", help='list a specific group in Gitlab that you have access to', context_settings={'help_option_names':['-h','--help']})
@click.argument("name", required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_groups(ctx, name, raw):
    if name is None:
        DATA = []
        Log.info("gathering Git group names, please wait...")
        RESULT = GIT.list_my_groups(None, raw=raw, user_profile=ctx.obj['profile'])
        for I in RESULT:
            NAME = str(I["name"])
            URL = I["web_url"].ljust(80)
            STR = URL + '\t' + NAME
            DATA.append(STR)
        DATA.sort(reverse=True)
        if DATA == []:
            Log.critical('unable to find any group names')
        else:
            INPUT = 'Group Manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[1].strip()
            if name:
                Log.info(f"gathering group {name} details now, please wait...")
            else:
                Log.critical("please select a group name to continue...")
        except:
            Log.critical("please select a group name to continue...")
    OUTPUT = GIT.list_group(name, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT == []:
        Log.critical('unable to find any group information')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("namespaces", help='list all namespaces in Gitlab that you have access to', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', required=False, default=None, type=str)
@click.pass_context
def list_namespaces(ctx, raw, pattern):
    OUTPUT = GIT.list_my_namespaces(pattern, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT == []:
        Log.critical('unable to find any namespace information')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command('access-token', help='API token for accessing the GIT functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = GIT.get_access_token(user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = GIT.get_access_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'GIT Menu: {INPUT}'
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
