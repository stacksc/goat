import sys, os
import click, json
from .nexusclient import NexusClient
from .nexus_auth import update_latest_profile
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate

NEXUS = NexusClient()
CONFIG = Config('nexustools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from Nexus",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common Nexus user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False

    if ctx.obj['setup'] == True:
        RESULT = NEXUS.setup_access(ctx.obj['profile'])
        if RESULT:
            Log.info("nexus settings saved succesfully")
            update_latest_profile(ctx.obj['profile'])
    log = Log('nexustools.log', debug)

@show.command('config', help="retrieve the entire content of nexustool's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def nexus_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = NEXUS.display_nexus_config(ctx.obj['profile'])

@show.command('manifests', help="display list of manifests for selected service", context_settings={'help_option_names':['-h','--help']})
@click.argument('service', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_manifests(ctx, service, raw):
    pass

@show.command("services", help='show all VMC services registered in nexus repository', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_services(ctx, raw=False):
    OUTPUT = NEXUS.list_all_services(ctx.obj['profile'], raw)
    if OUTPUT == []:
        Log.critical('unable to find any services')
    else:
        for SERVICE in OUTPUT:
            Log.info(SERVICE)

@show.command("manifests", help='show all VMC manifests registered in nexus repository for a particular service', context_settings={'help_option_names':['-h','--help']})
@click.argument('service', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_manifests(ctx, service, raw=False):
    if service is None:
        Log.info("gathering VMC service names, please wait...")
        OUTPUT = NEXUS.list_all_services(ctx.obj['profile'], raw)
        if OUTPUT == []:
            Log.critical('unable to find any services')
        else:
            INPUT = 'manifest manager'
            CHOICE = runMenu(OUTPUT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            service = CHOICE.split('\t')[0]
            if service:
                Log.info(f"gathering service {service} manifests now, please wait...")
            else:
                Log.critical("please select a service to continue...")
        except:
            Log.critical("please select a service to continue...")
    OUTPUT = NEXUS.list_all_manifests(service, raw)
    for MANIFEST in OUTPUT:
        Log.info(MANIFEST)

@show.command("manifest", help='show VMC manifest details registered in nexus repository for a particular service', context_settings={'help_option_names':['-h','--help']})
@click.argument('service', required=False, default=None)
@click.argument('manifest', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_tags(ctx, service, manifest, raw=False):
    if service is None:
        Log.info("gathering VMC service names, please wait...")
        OUTPUT = NEXUS.list_all_services(ctx.obj['profile'], raw)
        if OUTPUT == []:
            Log.critical('unable to find any services')
        else:
            INPUT = 'manifest manager'
            CHOICE = runMenu(OUTPUT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            service = CHOICE.split('\t')[0]
            if service:
                Log.info(f"gathering service {service} manifests now, please wait...")
            else:
                Log.critical("please select a service to continue...")
        except:
            Log.critical("please select a service to continue...")

    if manifest is None:
        DATA = []
        OUTPUT = NEXUS.list_all_manifests(service, raw)
        for MANIFEST in OUTPUT:
            DATA.append(MANIFEST)
        INPUT = 'manifest manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            manifest = CHOICE.split('\t')[0]
            if manifest:
                Log.info(f"gathering manifest {manifest} details now, please wait...")
            else:
                Log.critical("please select a manifest to continue...")
        except:
            Log.critical("please select a manifest to continue...")

    OUTPUT = NEXUS.list_manifest_details(service, manifest, raw)
    Log.json(json.dumps(OUTPUT, indent=2))

@show.command("tag", help='show VMC tag details registered in nexus repository for a particular service', context_settings={'help_option_names':['-h','--help']})
@click.argument('service', required=False, default=None)
@click.argument('tag', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_tags(ctx, service, tag, raw=False):
    if service is None:
        Log.info("gathering VMC service names, please wait...")
        OUTPUT = NEXUS.list_all_services(ctx.obj['profile'], raw)
        if OUTPUT == []:
            Log.critical('unable to find any services')
        else:
            INPUT = 'tag manager'
            CHOICE = runMenu(OUTPUT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            service = CHOICE.split('\t')[0]
            if service:
                Log.info(f"gathering service {service} tags now, please wait...")
            else:
                Log.critical("please select a service to continue...")
        except:
            Log.critical("please select a service to continue...")
    if tag is None:
        DATA = []
        OUTPUT = NEXUS.list_all_tags(service, raw)
        for TAG in OUTPUT:
            DATA.append(TAG)
        INPUT = 'tag manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            tag = CHOICE.split('\t')[0]
            if tag:
                Log.info(f"gathering tag {tag} details now, please wait...")
            else:
                Log.critical("please select a tag to continue...")
        except:
            Log.critical("please select a tag to continue...")
    OUTPUT = NEXUS.list_tag_details(service, tag, raw)
    Log.json(json.dumps(OUTPUT, indent=2))

@show.command("tags", help='show all VMC tags registered in nexus repository for a particular service', context_settings={'help_option_names':['-h','--help']})
@click.argument('service', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_tags(ctx, service, raw=False):
    if service is None:
        Log.info("gathering VMC service names, please wait...")
        OUTPUT = NEXUS.list_all_services(ctx.obj['profile'], raw)
        if OUTPUT == []:
            Log.critical('unable to find any services')
        else:
            INPUT = 'tag manager'
            CHOICE = runMenu(OUTPUT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            service = CHOICE.split('\t')[0]
            if service:
                Log.info(f"gathering service {service} tags now, please wait...")
            else:
                Log.critical("please select a service to continue...")
        except:
            Log.critical("please select a service to continue...")
    OUTPUT = NEXUS.list_all_tags(service, raw)
    for TAG in OUTPUT:
        Log.info(TAG)

@show.command("repos", help='show all repos registered in nexus', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_all_repos(ctx, raw=False):
    OUTPUT = NEXUS.list_all_repos(raw)
    if OUTPUT == []:
        Log.critical('unable to find any services')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("user", help='show user information registered in nexus for a specific user', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_user(ctx, name, raw=False):
    if name is None:
        DATA = []
        Log.info("gathering nexus user names, please wait...")
        OUTPUT = NEXUS.list_all_users(raw)
        for NAME in OUTPUT:
            DATA.append(NAME['userId'])
        DATA.sort()
        if OUTPUT == []:
            Log.critical('unable to find any nexus users')
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

    OUTPUT = NEXUS.list_user(name, raw)
    if OUTPUT == []:
        Log.critical('unable to find any services')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command("repo", help='show information registered in nexus for a specific repository', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False, default=None)
@click.option('-r', '--raw', 'raw', help="display raw json; dont reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def list_repo(ctx, name, raw=False):
    if name is None:
        DATA = []
        Log.info("gathering VMC repo names, please wait...")
        OUTPUT = NEXUS.list_all_repos(raw)
        for NAME in OUTPUT:
            DATA.append(NAME['url'])

        DATA.sort()
        if OUTPUT == []:
            Log.critical('unable to find any repositories')
        else:
            INPUT = 'repo manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            name = name.split("/")[-1]
            if name:
                Log.info(f"gathering repo {name} information now, please wait...")
            else:
                Log.critical("please select a repo to continue...")
        except:
            Log.critical("please select a repo to continue...")
    OUTPUT = NEXUS.list_repo(name, raw)
    if OUTPUT == []:
        Log.critical('unable to find any services')
    else:
        Log.json(json.dumps(OUTPUT, indent=2))

@show.command('access-token', help='API token for accessing the Nexus functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = NEXUS.get_access_token(user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = NEXUS.get_access_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Nexus Menu: {INPUT}'
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
