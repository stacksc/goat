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

@click.group(help="action tasks for Confluence",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def action(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    log = Log('confluence.log', debug)

@action.command('upload', help='upload CSV content to confluence space by Page ID', context_settings={'help_option_names':['-h','--help']})
@click.argument('file', type=click.Path(exists=True))
@click.option('-i', '--id', type=int, required=True, help='page ID for upload')
@click.option('-t', '--title', type=str, required=True, help='page title for upload')
@click.option('-n', '--name', type=str, required=True, help='name for the content to upload')
@click.pass_context
def upload_content(ctx, file, id, title, name):
    if id:
        SPACE, PAGES = CONFLUENCE.get_space_by_id(id, user_profile=ctx.obj['profile'])
        if SPACE:
            Log.info(f"uploading information to space: {SPACE}")
    else:
        Log.critical("please select at least one argument")
    RESULT = CONFLUENCE.upload_csv_file(file, name, id, title, ctx.obj['profile'])
    if RESULT:
        Log.json(json.dumps(RESULT, indent=2))
    return RESULT

def global_uploader(ctx, file, id, title, name):
    if id:
        SPACE, PAGES = CONFLUENCE.get_space_by_id(id, user_profile=ctx.obj['profile'])
        if SPACE:
            Log.info(f"uploading information to space: {SPACE}")
    else:
        Log.critical("please select at least one argument")
    RESULT = CONFLUENCE.upload_csv_file(file, name, id, title, ctx.obj['profile'])
    if RESULT:
        Log.json(json.dumps(RESULT, indent=2))
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
