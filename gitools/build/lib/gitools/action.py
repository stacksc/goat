import sys, os
import click, json
from .client import Client
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

GIT = Client()
CONFIG = Config('gitools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="action tasks for Gitlab",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common Gitlab user actions", is_flag=True)
@click.pass_context
def action(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    log = Log('gitools.log', debug)

@action.command('clone', help="easily clone a repository using the HTTP repo url", context_settings={'help_option_names':['-h','--help']})
@click.argument('repo_url', type=str, required=False)
@click.option('-a', '--all', 'all', help="clone all repositories from base group selected", is_flag=True, required=False, default=False)
@click.pass_context
def clone(ctx, repo_url, all):
    raw = False
    if repo_url is None:
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
            base = CHOICE.split('\t')[0].strip()
            if name:
                Log.info(f"gathering group {name} details now, please wait...")
            else:
                Log.critical("please select a group name to continue...")
        except:
            Log.critical("please select a group name to continue...")
        if all is True:
            GIT.clone_repo(base, all=all, user_profile=ctx.obj['profile'])
        else:
            OUTPUT = GIT.list_group(name, raw=raw, user_profile=ctx.obj['profile'])
            DATA = []
            for I in OUTPUT:
                for LINE in I:
                    URL = LINE["ssh_url_to_repo"].ljust(80)
                    NAME = LINE["name"]
                    STR = URL + "\t" + NAME
                    DATA.append(STR)
            DATA.sort(reverse=True)
            if DATA == []:
                Log.critical('unable to find group-level repositories')
            else:
                INPUT = 'Repo Manager'
                CHOICE = runMenu(DATA, INPUT)
            try:
                CHOICE = ''.join(CHOICE)
                repo_url = CHOICE.split('\t')[0].strip()
                if name:
                    Log.info(f"gathering repository {repo_url} details now, please wait...")
                else:
                    Log.critical("please select a repository name to continue...")
            except:
                Log.critical("please select a repository name to continue...")
            GIT.clone_repo(repo_url, user_profile=ctx.obj['profile'])

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
