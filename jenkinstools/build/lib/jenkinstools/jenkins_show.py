import sys, os, re
import click, json
import xml.etree.ElementTree as ET
from .jenkinsclient import JenkinsClient
from .jenkins_auth import update_latest_profile
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from toolbox.menumaker import Menu
from tabulate import tabulate
from toolbox.misc import detect_environment

JENKINS = JenkinsClient()
CONFIG = Config('jenkinstools')
os.environ['NCURSES_NO_UTF8_ACS'] = '1'

@click.group(help="retrieve information from Jenkins",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common Jenkins user actions", is_flag=True)
@click.pass_context
def show(ctx, debug, menu):
    user_profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False

    if ctx.obj['setup'] == True:
        RESULT = JENKINS.setup_access(ctx.obj['profile'])
        if RESULT:
            Log.info("jenkins settings saved succesfully")
            update_latest_profile(ctx.obj['profile'])
    log = Log('jenkinstools.log', debug)

@show.command('config', help="retrieve the entire content of jenkinstool's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def display_config(ctx):
    user_profile = ctx.obj['profile']
    OUTPUT = JENKINS.display_jenkins_config(ctx.obj['profile'])

@show.command('access-token', help='API token for accessing the Jenins functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = JENKINS.get_access_token(user_profile=ctx.obj['profile'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = JENKINS.get_access_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

@show.command('crumb-token', help='API crumb for accessing the Jenins functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_crumb_token(ctx):
    RESULT = JENKINS.get_crumb_token(user_profile=ctx.obj['profile'])
    Log.info(f"Crumb token:\n{RESULT}")
    return RESULT

@show.command('crumb-token-age', help='how long the current crumb token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_crumb_token_age(ctx):
    RESULT = JENKINS.get_crumb_token_age(user_profile=ctx.obj['profile'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Crumb token has been created {RESULT} minutes ago")
    return RESULT

@show.command('credentials', help="display system credentials available for jobs", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--description', 'description', help="display description of credentials in the output", is_flag=True, required=False, default=False)
@click.pass_context
def credentilas(ctx, description):
    RESULT = JENKINS.get_creds(ctx.obj['profile'])
    DATA = []
    if ctx.obj['profile'] == 'atlas' or ctx.obj['profile'] == 'default':
        for LINE in RESULT:
            DATA_DICT = {}
            LINE = re.sub("<.*?>"," ",LINE)
            LINE = ' '.join(LINE.split())
            if 'prod' in detect_environment():
                CRED = LINE.split(" ")[2]
            else:
                CRED = LINE.split(" ")[0]
            CRED = CRED[:75] + (CRED[75:] and '..')
            DATA_DICT['credential'] = CRED
            if description is True:
                if 'prod' in detect_environment():
                    DESC = LINE.split(" ")[3:]
                else:
                    DESC = LINE.split(" ")[1:]
                DESC = ' '.join([str(elem) for elem in DESC])
                DESC = DESC[:75] + (DESC[75:] and '..')
                DATA_DICT['description'] = DESC
            DATA.append(DATA_DICT)
    else:
        C = 1
        for LINE in RESULT:
            DATA_DICT = {}
            LINE = re.sub("<.*?>"," ",LINE)
            LINE = re.sub('\s\s+','\n',LINE)
        for I in LINE.split('\n'):
            DATA_DICT = {}
            if C == 0:
                if I:
                    CRED = I.strip()
                    DATA_DICT['credential'] = CRED
                    DATA.append(DATA_DICT)
                C = C + 1
            if 'global' in I:
                C = 0
    Log.info(f"\n{tabulate(DATA, headers='keys', tablefmt='rst')}")

def get_credentials(ctx, name):
    RESULT = JENKINS.get_creds(ctx.obj['profile'])
    if ctx.obj['profile'] == 'atlas' or ctx.obj['profile'] == 'default':
        for LINE in RESULT:
            LINE = re.sub("<.*?>"," ",LINE)
            LINE = ' '.join(LINE.split())
            if 'prod' in detect_environment():
                CRED = LINE.split(" ")[2]
            else:
                CRED = LINE.split(" ")[0]
            if name == CRED:
                return name
        return None
    else:
        C = 1
        for LINE in RESULT:
            DATA_DICT = {}
            LINE = re.sub("<.*?>"," ",LINE)
            LINE = re.sub('\s\s+','\n',LINE)
        for I in LINE.split('\n'):
            DATA_DICT = {}
            if C == 0:
                if I:
                    CRED = I.strip()
                    if name == CRED:
                        return name
                C = C + 1
            if 'global' in I:
                C = 0

@show.group(help="display information about Jenkins users", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def user(ctx):
    pass

@user.command('details', help="display user details for a selected user from Jenkins", context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def details(ctx, name, raw):
    if name:
        RESULT = JENKINS.get_user_details(name, ctx.obj['profile'], url=False)
        Log.json(json.dumps(RESULT, indent=2))
        sys.exit(0)
    else:
        DATA = []
        RESULT = JENKINS.get_users(ctx.obj['profile'])
        for I in RESULT['users']:
            USER = I['user']['fullName'].ljust(30)
            URL = I['user']['absoluteUrl'].rjust(50)
            STRING = USER + '\t' + URL
            DATA.append(STRING)
        if DATA == []:
            Log.critical('unable to find any users in Jenkins')
        else:
            INPUT = 'user manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[1].strip()
            if name:
                Log.info(f"gathering username {name} details now, please wait...")
            else:
                Log.critical("please select a username to continue...")
        except:
            Log.critical("please select a username to continue...")
    RESULT = JENKINS.get_user_details(name, raw, ctx.obj['profile'], url=True)
    Log.json(json.dumps(RESULT, indent=2))

@user.command('who', help="display list of users from Jenkins", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def who(ctx):
    RESULT = JENKINS.get_users(ctx.obj['profile'])
    SAVE = []
    for I in RESULT['users']:
        DATA = {}
        DATA['user'] = I['user']['fullName']
        DATA['url'] = I['user']['absoluteUrl']
        SAVE.append(DATA)
    Log.info(f"\n{tabulate(SAVE, headers='keys', tablefmt='rst')}")

@user.command('whoami', help="simple LDAP verification against Jenkins", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def whoami(ctx):
    RESULT = JENKINS.get_whoami(ctx.obj['profile'])
    Log.info(RESULT['id'])
    Log.info(RESULT['fullName'])
    Log.info(RESULT['absoluteUrl'])

@show.group(help="display information about Jenkins job names", context_settings={'help_option_names':['-h','--help']})
@click.option('-p', '--pattern', 'pattern', help="pattern to search on due to the number of job names", type=str, required=False, default=None)
@click.pass_context
def jobs(ctx, pattern):
    ctx.obj['pattern'] = pattern
    pass

@jobs.command('config', help='show XML configuration of a specific job from jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_job_details(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering job name {name} configuration now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")
    RESULT = JENKINS.get_job_config(name, user_profile=ctx.obj['profile'])
    element = ET.XML(RESULT)
    Log.info(ET.tostring(element, encoding='unicode'))

@jobs.command('last-failed', help='get the last failed build of a specific job from jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_last_failed_build(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"checking last failed job name {name} build now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")

    RESULT = JENKINS.last_failed_build(name, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2))

@jobs.command('last-success', help='get the last successful build of a specific job from jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_last_good_build(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"checking last successful job name {name} build now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")

    RESULT = JENKINS.last_good_build(name, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2))

@jobs.command('details', help='show details of a specific job from jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_job_details(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering job name {name} urls now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")
    RESULT = JENKINS.get_job_info(name, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2))

@jobs.command('console', help='show console output of a specific job build number from jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_console(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering job name {name} console now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")

    RESULT = JENKINS.job_history(name, user_profile=ctx.obj['profile'])
    RESULT.sort(reverse=True)
    if RESULT == []:
        Log.critical('unable to find any job URL(s)')
    else:
        INPUT = 'job manager'
        CHOICE = runMenu(RESULT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            url = CHOICE.split('\t')[0]
            if url:
                Log.info(f"gathering job {url} console now, please wait...")
            else:
                Log.critical("please select a job url to continue...")
        except:
            Log.critical("please select a job url to continue...")

    RESULT = JENKINS.get_console_output(url, raw, user_profile=ctx.obj['profile'])
    for RESULT in RESULT.split("\n"):
        print(RESULT)

@jobs.command('names', help='show all job names from jenkins', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_all_jobs(ctx):
    RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
    for JOB in RESULT:
        Log.info(JOB)
    return RESULT

@jobs.command('last', help='show the last build information for a specific job in jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_job_last(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering job name {name} urls now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")
    RESULT = JENKINS.last_job_history(name, raw, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2))
    return RESULT

@jobs.command('urls', help='show last 100 build urls for a specific job in jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.pass_context
def show_job_urls(ctx, name):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering job name {name} urls now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")
    RESULT = JENKINS.job_history(name, user_profile=ctx.obj['profile'])
    RESULT.sort(reverse=True)
    for I in RESULT:
        Log.info(I)
    return RESULT

@jobs.command('info', help='show details for a specific build and job name in jenkins', context_settings={'help_option_names':['-h','--help']})
@click.argument('name', required=False)
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.pass_context
def show_job_info(ctx, name, raw):
    DATA = []
    if not name:
        RESULT = JENKINS.job_names(pattern=ctx.obj['pattern'], user_profile=ctx.obj['profile'])
        for JOB in RESULT:
            DATA.append(JOB)
        if DATA == []:
            Log.critical('unable to find any jobs')
        else:
            INPUT = 'job manager'
            CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering job name {name} urls now, please wait...")
            else:
                Log.critical("please select a job name to continue...")
        except:
            Log.critical("please select a job name to continue...")
    RESULT = JENKINS.job_history(name, user_profile=ctx.obj['profile'])
    RESULT.sort(reverse=True)
    if RESULT == []:
        Log.critical('unable to find any job URL(s)')
    else:
        INPUT = 'job manager'
        CHOICE = runMenu(RESULT, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            url = CHOICE.split('\t')[0]
            if url:
                Log.info(f"gathering job {url} details now, please wait...")
            else:
                Log.critical("please select a job url to continue...")
        except:
            Log.critical("please select a job url to continue...")
    RESULT = JENKINS.job_details(url, raw, user_profile=ctx.obj['profile'])
    Log.json(json.dumps(RESULT, indent=2))
    return RESULT

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Jenkins Menu: {INPUT}'
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
