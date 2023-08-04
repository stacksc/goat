import sys, os, re
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

@click.group(help="retrieve information from concourse runway",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common Runway user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False
    log = Log('flytools.log', debug)

@show.command('config', help="retrieve the entire content of flytool's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def csp_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = FLY.display_config(ctx.obj['profile'])

@show.command('access-token', help='API token for accessing the concourse runway functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = FLY.get_access_token(user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = FLY.get_access_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

@show.command('teams', help='display teams found in Concourse', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', help="pattern to search on due to the number of teams", type=str, required=False, default=None)
@click.pass_context
def list_all_teams(ctx, raw, pattern):
    RESULT = FLY.list_all_teams(pattern, raw, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
    return RESULT

@show.command('pipelines', help='display pipelnes found in Concourse', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', help="pattern to search on due to the number of pipelines", type=str, required=False, default=None)
@click.pass_context
def list_all_pipelines(ctx, raw, pattern):
    RESULT = FLY.list_all_pipelines(pattern, raw, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
    return RESULT

@show.command('post-deploy', help="get post-deploy results per selected team in Concourse", context_settings={'help_option_names':['-h','--help']})
@click.argument('team', type=str, required=False)
@click.option('-p', '--pattern', 'pattern', help="pattern to search on due to the number of pipelines", type=str, required=False, default=None)
@click.option('-l', '--last', 'last', help="get the last build only from the post-deploy job", is_flag=True, required=False, default=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def get_post_deploy_results(ctx, team, pattern, last, raw):
    if not team:
        DATA = []
        Log.info("gathering Concourse team names, please wait...")
        RESULT = FLY.list_all_teams(pattern, raw, user_profile=ctx.obj['profile'])
        for I in RESULT:
            KEY = str(I["id"])
            NAME = I["name"].ljust(40)
            STR = NAME + '\t' + KEY
            DATA.append(STR)
        DATA.sort(reverse=True)
        if DATA == []:
            Log.critical('unable to find any team names')
        else:
            INPUT = 'Concourse manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            team = CHOICE.split('\t')[0].strip()
            if team:
                Log.info(f"gathering team {team} details now, please wait...")
            else:
                Log.critical("please select a team name to continue...")
        except:
            Log.critical("please select a team name to continue...")
    else:
        if 'http' in team:
            team = team.split('/')[4]
    RESULT = FLY.get_post_deploy_results(team, user_profile=ctx.obj['profile'])
    if RESULT:
        if last:
            for I in RESULT:
                Log.json(json.dumps(I, indent=2, sort_keys=True))
                break
        else:
            Log.json(json.dumps(RESULT, indent=2))
    else:
        Log.critical(f'unexpected result while calling the API: HTTPS response: {RESULT.status_code}')
    return RESULT

@show.command('jobs', help='display pipeline jobs per pipeline selected in Concourse', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', help="pattern to search on due to the number of pipelines", type=str, required=False, default=None)
@click.pass_context
def list_jobs(ctx, raw, pattern):
    DATA = []
    Log.info("gathering Concourse team names, please wait...")
    RESULT = FLY.list_all_teams(pattern, raw, user_profile=ctx.obj['profile'])
    for I in RESULT:
        KEY = str(I["id"])
        NAME = I["name"].ljust(40)
        STR = NAME + '\t' + KEY
        DATA.append(STR)
    DATA.sort(reverse=True)
    if DATA == []:
        Log.critical('unable to find any team names')
    else:
        INPUT = 'Concourse manager'
        CHOICE = runMenu(DATA, INPUT)
    try:
        CHOICE = ''.join(CHOICE)
        name = CHOICE.split('\t')[0].strip()
        if name:
            Log.info(f"gathering team {name} details now, please wait...")
        else:
            Log.critical("please select a team name to continue...")
    except:
        Log.critical("please select a team name to continue...")
    # first grab all pipelines based on the team selected
    OUTPUT = FLY.list_pipeline_details(name, pipeline=None, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT:
        DATA = []
        for I in OUTPUT:
            KEY = str(I["id"])
            NAME = I["name"].ljust(40)
            STR = NAME + "\t" + KEY
            DATA.append(STR)
        DATA.sort()
        if DATA == []:
            Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
        else:
            INPUT = 'Concourse manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            pipeline = CHOICE.split('\t')[0].strip()
            if name:
                Log.info(f"gathering pipeline {pipeline} details now, please wait...")
            else:
                Log.critical("please select a pipeline to continue...")
        except:
            Log.critical("please select a pipeline to continue...")
    OUTPUT = FLY.list_jobs(name, pipeline=pipeline, raw=raw, user_profile=ctx.obj['profile'])
    print(OUTPUT)

@show.command('job', help='display pipeline job details per pipeline selected in Concourse', context_settings={'help_option_names':['-h','--help']})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-p', '--pattern', 'pattern', help="pattern to search on due to the number of pipelines", type=str, required=False, default=None)
@click.pass_context
def list_job(ctx, raw, pattern):
    DATA = []
    Log.info("gathering Concourse team names, please wait...")
    RESULT = FLY.list_all_teams(pattern, raw, user_profile=ctx.obj['profile'])
    for I in RESULT:
        KEY = str(I["id"])
        NAME = I["name"].ljust(40)
        STR = NAME + '\t' + KEY
        DATA.append(STR)
    DATA.sort(reverse=True)
    if DATA == []:
        Log.critical('unable to find any team names')
    else:
        INPUT = 'Concourse manager'
        CHOICE = runMenu(DATA, INPUT)
    try:
        CHOICE = ''.join(CHOICE)
        name = CHOICE.split('\t')[0].strip()
        if name:
            Log.info(f"gathering team {name} details now, please wait...")
        else:
            Log.critical("please select a team name to continue...")
    except:
        Log.critical("please select a team name to continue...")
    # first grab all pipelines based on the team selected
    OUTPUT = FLY.list_pipeline_details(name, pipeline=None, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT:
        DATA = []
        for I in OUTPUT:
            KEY = str(I["id"])
            NAME = I["name"].ljust(40)
            STR = NAME + "\t" + KEY
            DATA.append(STR)
        DATA.sort()
        if DATA == []:
            Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
        else:
            INPUT = 'Concourse manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            pipeline = CHOICE.split('\t')[0].strip()
            if name:
                Log.info(f"gathering pipeline {pipeline} details now, please wait...")
            else:
                Log.critical("please select a pipeline to continue...")
        except:
            Log.critical("please select a pipeline to continue...")
    # next grab pipeline details with the provided team name and pipeline selected above
    OUTPUT = FLY.list_pipeline_details(name, pipeline=pipeline, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT:
        DATA = []
        for I in OUTPUT:
            INFO = OUTPUT[I]
            # jobs exist in a list
            if str(INFO).startswith("[") and str(INFO).endswith("]"):
                # rip thru the list and find the job names
                for ITEM in INFO:
                    JOBS = ITEM["jobs"]
                    for J in JOBS:
                        DATA.append(J)
        # sort before proceeding
        DATA.sort()
        # dump and exit if not found
        if DATA == []:
            Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
            sys.exit()
        else:
            INPUT = 'Concourse manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            job = CHOICE.split('\t')[0].strip()
            if job:
                Log.info(f"gathering job {job} details now, please wait...")
            else:
                Log.critical("please select a job to continue...")
        except:
            Log.critical("please select a job to continue...")

    # now list the build details associated with the job/pipeline/team
    OUTPUT = FLY.list_builds(name, job=job, pipeline=pipeline, raw=raw, user_profile=ctx.obj['profile'])
    OUTPUT.reverse()
    DATA = []
    for ITEM in OUTPUT:
        if ITEM['name'].isdigit():
            DATA.append(ITEM['name'])
    # process the results now
    if DATA:
        INPUT = 'Concourse manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            build = CHOICE.split('\t')[0].strip()
            if build:
                Log.info(f"gathering build {build} details now, please wait...")
            else:
                Log.critical("please select a build name to continue...")
        except:
            Log.critical("please select a build name to continue...")

    OUTPUT = FLY.list_build(name, build=build, job=job, pipeline=pipeline, raw=raw, user_profile=ctx.obj['profile'])
    if OUTPUT != []:
        Log.json(json.dumps(OUTPUT, indent=2))
    else:
        Log.critical(f"unable to list build details for build: {build}")

def get_relevant_jobs(item):
    names = item[0]
    return names

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
