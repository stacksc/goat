import sys, click, json, os, datetime, re, time, fnmatch, in_place, random
from toolbox.logger import Log
from gitools.auth import get_latest_profile
from gitools.client import Client as GiClient
from jfrogtools.client import Client as JfrogClient
from flytools.client import Client as FlyClient 
from toolbox.click_complete import complete_profile_names, complete_bucket_names, complete_jira_profiles
from configstore.configstore import Config
from toolbox.menumaker import Menu
from jenkinstools.jenkinsclient import JenkinsClient
from toolbox.passwords import PasswordstateLookup
from toolbox.getpass import getOtherToken
from toolbox import misc
from tabulate import tabulate
from jiratools.search import run_jql_query

GIT = GiClient()
JFROG = JfrogClient()
FLY = FlyClient()
MESSAGE="PUBSECSRE Remediation" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group('security', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110}, invoke_without_command=True)
@click.pass_context
def security(ctx):
    user_profile = get_latest_profile()
    ctx.obj['profile'] = user_profile

@security.command(help='get the latest tag for photon3 from photonos-docker-local repository', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.option('-u', '--url', help='override the default url', default='https://artifactory.eng.vmware.com/artifactory/photonos-docker-local/photon3/', required=False, show_default=True)
@click.option('-m', '--modify', help='modify the tag in the repository', is_flag=True, required=False, show_default=True, default=False)
@click.pass_context
def get_latest_tag(ctx, url, modify):
    PART = '/'.join(url.split('/')[4:])
    TAG = _get_latest_tag(PART, url, ctx.obj['profile'], modify=modify)
    return TAG

def _get_latest_tag(PART, url, profile, modify=False):
    OUTPUT = JFROG.list_artifacts(PART, user_profile=profile)
    if OUTPUT:
        REG = re.compile("[0-9]{4}[0-9]{2}[0-9]{2}/")
        LIST = []
        for I in OUTPUT:
            SEARCH = re.match(REG, I)
            if SEARCH:
                LIST.append(I.replace("/",""))
    LIST.sort()
    TAG = listToStringWithoutBrackets(LIST[-1:])
    Log.info(f"latest tag matching url {url}: {TAG}")
    if modify:
        compare_tag(TAG, modify=modify)
    else:
        compare_tag(TAG, modify=modify)
    return TAG

@security.command(help='clone all git repositories to prepare for remediation', context_settings={'help_option_names':['-h','--help']})
@click.option('-u', '--url', 'url', required=False, default=None, type=str)
@click.pass_context
def pull_repo(ctx, url):
    LIST = ['git@gitlab.eng.vmware.com:govcloud-ops/fedrampinventory.git', 'git@gitlab.eng.vmware.com:govcloud-ops/govops-util.git', 'git@gitlab.eng.vmware.com:govcloud-ops/pop-govops.git']
    if url is None:
        for REPO in LIST:
            REGEX = REPO.split(':')[-1:]
            REGEX = listToStringWithoutBrackets(REGEX).replace('.git','')
            CHK = GIT.check_local_repo(REGEX, user_profile=ctx.obj['profile'])
            if CHK is False:
                GIT.clone_repo(REPO, user_profile=ctx.obj['profile'])
            else:
                GIT.pull_repo(REPO, user_profile=ctx.obj['profile'])
    else:
        REGEX = REPO.split(':')[-1:]
        REGEX = listToStringWithoutBrackets(REGEX).replace('.git','')
        CHK = GIT.check_local_repo(url, user_profile=ctx.obj['profile'])
        if CHK is False:
            GIT.clone_repo(url, user_profile=ctx.obj['profile'])
        else:
            GIT.pull_repo(url, user_profile=ctx.obj['profile'])

@security.command(help='get the latest pipeline job status in runway for all 3 images', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.option('-p', '--pipeline', 'pipeline', required=False, default='postcommit', type=click.Choice(['postcommit', 'cscm-ticket-automation']))
@click.option('-l', '--last', 'last', required=False, default='1', type=int)
@click.pass_context
def check_pipeline(ctx, pipeline, last):
    _check_pipeline(pipeline, last, ctx.obj['profile'])

def _check_pipeline(pipeline, last, profile):
    TEAMS = ['govcloud-ops-pop-govops', 'govcloud-ops-fedrampinventory', 'govcloud-ops-govops-util']
    PIPELINE = pipeline
    if PIPELINE == 'postcommit':
        JOB = 'govcloud-stg-candidate-promoter'
    elif PIPELINE == 'cscm-ticket-automation':
        JOB = 'govcloud-cscm-ticket'
    raw = False
    HEADER = ['id', 'team_name', 'name', 'status', 'api_url', 'job_name', 'pipeline_id', 'pipeline_name', 'start_time', 'end_time']
    for TEAM in TEAMS:
        print('\n' + misc.MYBLUE + misc.UNDERLINE + TEAM.upper() + misc.RESET)
        OUTPUT = FLY.list_builds(TEAM, job=JOB, pipeline=PIPELINE, raw=raw, user_profile=profile)
        VALID = []
        CNT = 0
        if OUTPUT is not None:
            for I in OUTPUT:
                try:
                    I['start_time'] = datetime.datetime.fromtimestamp(I['start_time']).strftime('%Y-%m-%d %H:%M:%S')
                    I['end_time'] = datetime.datetime.fromtimestamp(I['end_time']).strftime('%Y-%m-%d %H:%M:%S')
                    VALID.append([I['id'], I['team_name'], I['name'], I['status'], I['api_url'], I['job_name'], I['pipeline_id'], I['pipeline_name'], I['start_time'], I['end_time']])
                    CNT = CNT + 1
                    if CNT >= last:
                        break
                except:
                    pass
            VALID.reverse()
            print(tabulate([*[[line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9]] for line in VALID]], headers=HEADER, tablefmt='rst'))

@security.command(help='trigger the runway job to cut CSCM tickets per image being remediated', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.pass_context
def cut_ticket(ctx):
    TEAMS = ['govcloud-ops-pop-govops', 'govcloud-ops-fedrampinventory', 'govcloud-ops-govops-util']
    raw = False
    for TEAM in TEAMS:
        print('\n' + misc.MYBLUE + misc.UNDERLINE + TEAM.upper() + misc.RESET)
        OUTPUT = FLY.trigger_cscm_ticket_automation(TEAM, user_profile=ctx.obj['profile'])
        if OUTPUT != []:
            Log.json(json.dumps(OUTPUT, indent=2))

@security.command(help='launch a text menu interface to perform remediation tasks in order', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.pass_context
def menu(ctx):
    URL = 'https://artifactory.eng.vmware.com/artifactory/photonos-docker-local/photon3/'
    LIST = ['git@gitlab.eng.vmware.com:govcloud-ops/fedrampinventory.git', 'git@gitlab.eng.vmware.com:govcloud-ops/govops-util.git', 'git@gitlab.eng.vmware.com:govcloud-ops/pop-govops.git']
    OPTIONS = ['Pull Repositories', 'Photon3 Tag Check', 'Photon3 Update & MR', 'Check postcommit Pipeline', 'Launch CSCM Ticket Pipeline', 'Check cscm-ticket-automation Pipeline', 'Docker Image & Ticket Check', 'Docker Image Update & MR', 'Quit']
    OPTION = ''
    while OPTION != 'Quit':
        DATA = []
        for OPTION in OPTIONS:
            STR = OPTION.ljust(60)
            DATA.append(STR)
        INPUT = 'Security Remediation'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            OPTION = CHOICE.split('\t')[0].strip()
            if OPTION and OPTION != 'Quit':
                Log.info(f"launching {OPTION} tasks now, please wait...")
            else:
                if OPTION == 'Quit':
                    break
                else:
                    Log.critical("please select an option to continue...")
        except:
            Log.critical("please select an option to continue...")
        if 'Pull' in OPTION:
            for REPO in LIST:
                REGEX = REPO.split(':')[-1:]
                REGEX = listToStringWithoutBrackets(REGEX).replace('.git','')
                CHK = GIT.check_local_repo(REGEX, user_profile=ctx.obj['profile'])
                if CHK is False:
                    GIT.clone_repo(REPO, user_profile=ctx.obj['profile'])
                else:
                    GIT.pull_repo(REPO, user_profile=ctx.obj['profile'])
        elif 'Tag Check' in OPTION:
            PART = '/'.join(URL.split('/')[4:])
            TAG = _get_latest_tag(PART, URL, ctx.obj['profile'], modify=False)
        elif 'Photon3 Update' in OPTION:
            PART = '/'.join(URL.split('/')[4:])
            TAG = _get_latest_tag(PART, URL, ctx.obj['profile'], modify=True)
        elif 'postcommit' in OPTION:
            RESULT = _check_pipeline('postcommit', 1, ctx.obj['profile'])
        elif 'Launch' in OPTION:
            TEAMS = ['govcloud-ops-pop-govops', 'govcloud-ops-fedrampinventory', 'govcloud-ops-govops-util']
            raw = False
            for TEAM in TEAMS:
                print('\n' + misc.MYBLUE + misc.UNDERLINE + TEAM.upper() + misc.RESET)
                OUTPUT = FLY.trigger_cscm_ticket_automation(TEAM, user_profile=ctx.obj['profile'])
                if OUTPUT != []:
                    Log.json(json.dumps(OUTPUT, indent=2))
        elif 'cscm-ticket-automation' in OPTION:
            RESULT = _check_pipeline('cscm-ticket-automation', 1, ctx.obj['profile'])
        elif 'Docker Image & Ticket Check' in OPTION:
            RESULT = _resource_versions('postcommit', 'govcloud-stg-semver', 1, False, ctx.obj['profile'], ctx.obj['profile'])
        elif 'Docker Image Update' in OPTION:
            RESULT = _resource_versions('postcommit', 'govcloud-stg-semver', 1, True, ctx.obj['profile'], ctx.obj['profile'])
        time.sleep(2)
        print()
        ANS = input('press ENTER to continue: ')
        print()

@security.command(help='list the new resource versions per image', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.option('-p', '--pipeline', 'pipeline', required=False, default='postcommit', type=str, show_default=True)
@click.option('-r', '--resource', 'resource', required=False, default='govcloud-stg-semver', type=str, show_default=True)
@click.option('-l', '--last', 'last', required=False, default='1', type=int, show_default=True)
@click.option('-m', '--modify', help='compare the latest resource versions/tickets and update as necessary', is_flag=True, required=False, show_default=True, default=False)
@click.option('-j', '--jira_profile', help='specify the name of jiraclient profile to use', default='default', required=False, shell_complete=complete_jira_profiles, show_default=True)
@click.pass_context
def resource_versions(ctx, pipeline, resource, last, modify, jira_profile):
    RESULT = _resource_versions(pipeline, resource, last, modify, ctx.obj['profile'], jira_profile)

def _resource_versions(pipeline, resource, last, modify, profile, jira_profile):
    TEAMS = ['govcloud-ops-pop-govops', 'govcloud-ops-fedrampinventory', 'govcloud-ops-govops-util']
    for TEAM in TEAMS:
        print('\n' + misc.MYBLUE + misc.UNDERLINE + TEAM.upper() + misc.RESET)
        MYTEAM = TEAM.split()
        # get the latest ticket matching this team
        SEARCH_DATA = run_jql_query(['CSCM'],None,None,None,None,None,MYTEAM,None,None,1,False,False,False,False,None,False,True,jira_profile,True)
        for I in SEARCH_DATA:
            KEY = I['key']
        SUB = TEAM.replace('govcloud-ops-','').strip()
        if modify:
            compare_key_version(SUB, KEY, modify=True)
        else:
            compare_key_version(SUB, KEY, modify=False)
        CNT = 0
        OUTPUT = FLY.list_resource_versions(TEAM, pipeline, resource, user_profile=profile)
        if OUTPUT != []:
            for I in OUTPUT:
                try:
                    VERSION = I['version']['number']
                    SUB = TEAM.replace('govcloud-ops-','').strip()
                    if modify:
                        compare_resource_version(SUB, VERSION, modify=True)
                    else:
                        compare_resource_version(SUB, VERSION, modify=False)
                except:
                    break
                CNT = CNT + 1
                if CNT >= last:
                    break

def merge(dict1, dict2):
    RES = {**dict1, **dict2}
    return RES

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Main Menu: {INPUT}'
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

def MenuResults(ctx):

    DATA = []
    IDP = IDPclient(ctx)
    user_profile = ctx.obj['profile']
    OUTPUT = IDP.list_users()

    if OUTPUT == []:
        Log.critical(f'unable to find any users for tenant {user_profile}')
    else:
        for i in OUTPUT:
            ID = i['id']
            USERNAME = i['username'].ljust(50)
            STR = USERNAME + "\t" + ID
            DATA.append(STR)
        DATA.sort()
        INPUT = 'IDP User Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            USERNAME = CHOICE.split('\t')[0].strip()
            USER_ID = CHOICE.split('\t')[1].strip()
            if USERNAME:
                Log.info(f"gathering {USERNAME} details now, please wait...")
            else:
                Log.critical("please select a username to continue...")
        except:
            Log.critical("please select a username to continue...")
    return USERNAME, USER_ID

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace("{","").replace("}","")

def compare_key_version(repo, key, modify=False):

    REPO = os.environ['HOME'] + f'/repos/govcloud-ops/{repo}'
    misc.pushd(REPO)
    CMD = 'git checkout main >/dev/null 2>&1 && git pull >/dev/null 2>&1'
    os.system(CMD)

    for YAML in find_files(REPO, 'version.yml'):
        if os.path.isfile(YAML):
            with open(YAML, 'r') as f:
                LINE = f.readline()
                while LINE != '':
                    if 'change-ticket' in LINE:
                        TICKET = LINE.split(':')[1].strip().split(' ')[0]
                        if TICKET == key:
                            print()
                            SUCCESS = misc.MOVE2 + misc.GREEN + misc.UNDERLINE + 'SUCCESS' + misc.RESET
                            Log.info(f"ticket from repository matches the latest CSCM ticket: {SUCCESS}")
                            Log.info(f"repository key: {TICKET}")
                            Log.info(f"latest key:     {key}")
                        else:
                            FAILURE = misc.MOVE2 + misc.RED + misc.UNDERLINE + 'FAILURE' + misc.RESET
                            print()
                            Log.info(f"ticket from repository does not match the latest CSCM ticket: {FAILURE}")
                            Log.info(f"repository key: {TICKET}")
                            Log.info(f"latest key:     {key}")
                            if modify:
                                replace_version(YAML, TICKET, key)
                    LINE = f.readline()
    misc.popd()

def compare_resource_version(repo, resource_version, modify=False):
    REPO = os.environ['HOME'] + f'/repos/govcloud-ops/{repo}'
    for YAML in find_files(REPO, 'version.yml'):
        if os.path.isfile(YAML):
            with open(YAML, 'r') as f:
                LINE = f.readline()
                while LINE != '':
                    if 'docker-image-tag' in LINE:
                        VERSION = LINE.split(':')[1].strip().split(' ')[0]
                        if VERSION == resource_version:
                            print()
                            SUCCESS = misc.MOVE2 + misc.GREEN + misc.UNDERLINE + 'SUCCESS' + misc.RESET
                            Log.info(f"version from repository matches the latest resource version: {SUCCESS}")
                            Log.info(f"repository resource: {VERSION}")
                            Log.info(f"latest resource:     {resource_version}")
                        else:
                            FAILURE = misc.MOVE2 + misc.RED + misc.UNDERLINE + 'FAILURE' + misc.RESET
                            print()
                            Log.info(f"version from repository does NOT match the latest resource version: {FAILURE}")
                            Log.info(f"repository resource: {VERSION}")
                            Log.info(f"latest resource:     {resource_version}")
                            if modify:
                                replace_version(YAML, VERSION, resource_version)
                                RANDOM = random.randint(10,1000)
                                Log.info(f"checking out a new branch 'update-version-{VERSION}-{RANDOM}' in {repo} with {resource_version}")
                                misc.pushd(REPO)
                                CMD = 'git pull'
                                os.system(CMD)
                                merge_resource_change(resource_version, YAML, RANDOM)
                                misc.popd()
                    LINE = f.readline()

def compare_tag(tag, modify=False):
    REPOS = ['fedrampinventory', 'pop-govops', 'govops-util']
    for repo in REPOS:
        print('\n' + misc.MYBLUE + misc.UNDERLINE + repo.upper() + misc.RESET)
        REPO = os.environ['HOME'] + f'/repos/govcloud-ops/{repo}'
        misc.pushd(REPO)
        CMD = 'git checkout main >/dev/null 2>&1 && git pull >/dev/null 2>&1'
        os.system(CMD)
        for DOCKERFILE in find_files(REPO, 'Dockerfile'):
            if os.path.isfile(DOCKERFILE):
                with open(DOCKERFILE, 'r') as f:
                    LINE = f.readline()
                    while LINE != '':
                        if 'ARG VERSION' in LINE:
                            VERSION = LINE.split('=')[1].strip()
                            if VERSION == tag:
                                print()
                                SUCCESS = misc.MOVE2 + misc.GREEN + misc.UNDERLINE + 'SUCCESS' + misc.RESET
                                Log.info(f"photon3 version from repository matches the latest tag: {SUCCESS}")
                                Log.info(f"repository tag: {VERSION}")
                                Log.info(f"latest tag:     {tag}")
                            else:
                                FAILURE = misc.MOVE2 + misc.RED + misc.UNDERLINE + 'FAILURE' + misc.RESET
                                print()
                                Log.info(f"photon3 version from repository is different from the latest tag: {FAILURE}")
                                Log.info(f"repository tag: {VERSION}")
                                Log.info(f"latest tag:     {tag}")
                                if modify:
                                    RANDOM = random.randint(10,1000)
                                    replace_version(DOCKERFILE, VERSION, tag)
                                    Log.info(f"checking out a new branch 'update-version-{tag}-{RANDOM}' in {repo} repository")
                                    CMD = 'git pull'
                                    os.system(CMD)
                                    merge_docker_change(tag, DOCKERFILE, RANDOM)
                        LINE = f.readline()
        misc.popd()

def find_files(directory, pattern):
    for ROOT, DIRS, FILES in os.walk(directory):
        for BASENAME in FILES:
            if fnmatch.fnmatch(BASENAME, pattern):
                FILENAME = os.path.join(ROOT, BASENAME)
                yield FILENAME

def replace_version(file, old_tag, new_tag):
    with in_place.InPlace(file) as f:
        for line in f:
            line = line.replace(old_tag, new_tag)
            f.write(line)

def merge_docker_change(version, dockerfile, random):
    CMD = f'git checkout -b "update-version-{version}-{random}" >/dev/null 2>&1;'
    os.system(CMD)
    CMD = f'git add {dockerfile}'
    os.system(CMD)
    CMD = f'git commit -am "INFO: updating repository for monthly remediation scans using version {version}" >/dev/null 2>&1'
    os.system(CMD)
    CMD = f'git push --set-upstream origin "update-version-{version}-{random}" -o merge_request.create'
    os.system(CMD)

def merge_resource_change(resource_version, yaml, random):
    CMD = f'git checkout -b "update-version-{resource_version}-{random}" >/dev/null 2>&1;'
    os.system(CMD)
    CMD = f'git add {yaml}'
    os.system(CMD)
    CMD = f'git commit -am "INFO: updating repository for monthly remediation scans using version {resource_version}" >/dev/null 2>&1'
    os.system(CMD)
    CMD = f'git push --set-upstream origin "update-version-{resource_version}-{random}" -o merge_request.create'
    os.system(CMD)
