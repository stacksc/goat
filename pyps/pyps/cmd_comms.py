#!/usr/bin/env python3
import click, datetime, os, re, json, sys
from slacktools import post, react
from toolbox.logger import Log
from jiratools.issue import add_comment as comment, get_inb_data, global_assign, extract_data_from_issue, get_runway_job
from jiratools.transitions import transition_issue, get_status_id, transition_wizard
from jiratools.auth import get_user_profile_based_on_key, get_jira_session_based_on_key
from jiratools.search import get_comms_data, build_url, search_issues, runMenu, create_link
from flytools.client import Client
from toolbox.click_complete import complete_slack_names, complete_emojis, complete_projects
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import set_terminal_width, detect_environment
from jenkinstools.jenkins_show import get_credentials
from jenkinstools.jenkinsclient import JenkinsClient

JENKINS = JenkinsClient()
CONFIG = Config('jctools')

@click.group(help="Communicate changes to JIRA & Slack, with pipeline tasks initiated in-boundary", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()}, invoke_without_command=True)
@click.pass_context
def jc(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = 'default'
    pass

@jc.command(help='kick off change notification to JIRA & Slack, with pipeline tasks initiated in-boundary', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('channel', nargs=-1, type=str, required=False, shell_complete=complete_slack_names)
@click.option('-k', '--key', help="JIRA ticket number (key) to post a comment on; i.e. PUBSECSRE-123", type=str, required=False, default=None, multiple=True)
@click.option('-p', '--project', help="JIRA project to search for tickets to transition; i.e. PUBSECSRE", type=str, required=False, default=None, shell_complete=complete_projects)
@click.pass_context
def start(ctx, key, project, channel=None):
    SPOOL = {}
    if key:
        for k in key:
            profile = get_user_profile_based_on_key(k)
            SPOOL[k] = profile
    elif project:
        profile = get_user_profile_based_on_key(project)
    else:
        Log.critical("One of the following fields is required: key, project, profile. Searching across profiles is not yet supported")
    if project:
        key = setup_project(project, profile)
        SPOOL[key] = profile
    if not key:
        Log.critical("no issue key found")

    if SPOOL:
        for key in SPOOL:
            profile = SPOOL[key]
            if profile:
                ANS = input(f"WARN: would you like to start change {key} now? (y/n): ")
                if ANS != 'y' and ANS != 'Y':
                    Log.warn(f"continuing and will not start change {key}")
                    continue
                RESPONSE = get_comms_data(key, profile)
                ISSUES = []
                key = (key,)
                for ISSUE in RESPONSE:
                    ISSUE_DICT = {}
                    ISSUE_DICT['key'] = str(ISSUE.key)
                    ISSUE_DICT['summary'] = str(ISSUE.fields.summary)
                    ISSUE_DICT['status'] = str(ISSUE.fields.status)
                    ISSUE_DICT['assignee'] = str(ISSUE.fields.assignee)
                    ISSUE_DICT['reporter'] = str(ISSUE.fields.reporter)
                    ISSUES.append(ISSUE_DICT)
                    TEMPLATE = build_slack_message(ISSUE.fields.summary, build_url(str(ISSUE.key), profile), ISSUE.fields.reporter) 
                COMMENT = TEMPLATE.replace("```","")

            # make sure the ticket is assigned to the user running the script
            USERNAME = os.environ["LOGNAME"].split("@")[0]
            RESULT = global_assign(key, USERNAME, profile)
            # comment the ticket now
            RESULT = comment(key, COMMENT, profile)
            if RESULT:
                Log.info(f'ticket commented successfully, and change notification in progress')
            # save the rollback transaction ID
            data_key = "Rollback Transaction-ID"
            ROLLBACK_ID = extract_data_from_issue(key, data_key, False, profile)
            if ROLLBACK_ID:
                Log.info(f'rollback transition-ID found in ticket: {ROLLBACK_ID}')
            # convert key back to tuple and transition ticket to In Progress
            key = convertTuple(key)
            TARGET_STATUS_NAME = 'In Progress'
            TRANSITION_PAYLOAD = None
            TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, profile)
            RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, profile)
            if RESULT:
                Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                if detect_environment() == 'non-gc':
                    if TEMPLATE:
                        TIMESTAMP = post.post_slack_message(channel, TEMPLATE)
            else:
                Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')

            # break with a slack message only if we are non-prod
            if detect_environment() == 'non-gc':
                for result in TIMESTAMP:
                    ts = result["ts"]
                    Log.info(f'Operation succesfull; slack message TS: {result["ts"]}')
                    PROFILE = CONFIG.get_profile(key)
                    if PROFILE is None or PROFILE['config'] == {}:
                        Log.debug(f"Profile '{key}' not found; creating a new profile")
                        CONFIG.create_profile(key)
                        CONFIG.update_config(ts, "start", key)
                    else:
                        CONFIG.update_config(ts, "start", key)
            else:
                # perform more work only if we are in-production
                ct = datetime.datetime.now()
                ts = ct.timestamp()
                PROFILE = CONFIG.get_profile(key)
                if PROFILE is None or PROFILE['config'] == {}:
                    Log.debug(f"Profile '{key}' not found; creating a new profile")
                    CONFIG.create_profile(key)
                    CONFIG.update_config(ts, "start", key)
                else:
                    CONFIG.update_config(ts, "start", key)
                Log.info("searching for credentials and build url now, please wait.")
                # gather information to build the job
                key = convertTuple(key)
                URL, CREDENTIALS = get_inb_data(key)
                DATA = []
                # dictionarify our data
                if URL != [] and CREDENTIALS != []:
                    JSONDICT = {}
                    DOTCOM = re.sub(r'/job.*$', '', URL)
                    BASE = re.sub(r'/parambuild.*$', '', URL)
                    JOB = re.sub(r'^.*/job/', '', BASE)
                    PARAMS = re.sub(r'^.*?\?', '', URL).split("&")
                    for PARAM in PARAMS:
                        VAR = PARAM.split("=")[0]
                        VAL = PARAM.split("=")[1]
                        JSONDICT[VAR] = VAL
                    # initiate fallback creds
                    FALLBACK = 'zeus-secrets-default'
                    # verify our jenkins profile based on the URL
                    if 'atlas' in URL:
                        ctx.obj['profile'] = 'atlas'
                    else:
                        ctx.obj['profile'] = 'delta'
                    Log.info(f"please see the following build information:")
                    print()
                    Log.info(f'url: ->\n\t{DOTCOM}')
                    Log.info(f'job: ->\n\t{JOB}')
                    for CREDENTIAL in CREDENTIALS:
                        CHK = get_credentials(ctx, CREDENTIAL)
                        if CHK is not None:
                            Log.info(f'creds: ->\n\t{CREDENTIAL} FOUND')
                        else:
                            Log.info(f'creds: ->\n\t{CREDENTIAL} NOT FOUND')
                    JSONDICT["HELM_CREDENTIAL"] = CREDENTIAL
                    Log.info(f'params: ->\n\t{JSONDICT}')
                    print()
                elif URL is not None:
                    JSONDICT = {}
                    DOTCOM = re.sub(r'/job.*$', '', URL)
                    BASE = re.sub(r'/parambuild.*$', '', URL)
                    JOB = re.sub(r'^.*/job/', '', BASE)
                    PARAMS = re.sub(r'^.*?\?', '', URL).split("&")
                    for PARAM in PARAMS:
                        VAR = PARAM.split("=")[0]
                        VAL = PARAM.split("=")[1]
                        JSONDICT[VAR] = VAL
                    # verify our jenkins profile based on the URL
                    if 'atlas' in URL:
                        ctx.obj['profile'] = 'atlas'
                    else:
                        ctx.obj['profile'] = 'delta'
                    Log.info(f"please see the following build information:")
                    print()
                    Log.info(f'url: ->\n\t{DOTCOM}')
                    Log.info(f'job: ->\n\t{JOB}')
                    Log.info(f'params: ->\n\t{JSONDICT}')
                    print()
                else:
                    Log.critical("no build URL and/or credentials found, exiting.")
                # now submit the build to jenkins with the correct data and wait for results
                if CREDENTIALS:
                    ANS = input(f"would you like to trigger the build with {CREDENTIAL}? (y/n): ")
                else:
                    ANS = input(f"would you like to trigger the build url without defined credentials(y/n): ")
                if ANS == 'y' or ANS == 'Y':
                    CONFIG.update_config(JOB, "job", key)
                    CONFIG.update_config(JSONDICT, "params", key)
                    MYURL = JENKINS.build_url(JOB, JSONDICT, user_profile=ctx.obj['profile'])
                    RESULT = JENKINS.launch_job(JOB, JSONDICT, wait=True, interval=30, time_out=7200, user_profile=ctx.obj['profile'])
                    print()
                    if RESULT:
                        try:
                            Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
                            Log.info(f"full URL: {MYURL}")
                        except:
                            Log.info(f"result:   {RESULT}")
                            Log.info(f"full URL: {MYURL}")
                        print()
                        CONFIG.update_config(RESULT, "result", key)
                    else:
                        Log.warn("the launch job returned an empty string. Please look into this job in Jenkins console.")
                else:
                    CONFIG.update_config(JOB, "job", key)
                    CONFIG.update_config(JSONDICT, "params", key)
                    CONFIG.update_config("skipping", "result", key)
                    Log.info("skipping build now...")

@jc.command(help='send comms about finishing the work on a change via JIRA & Slack', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.argument('channel', nargs=-1, type=str, required=False, shell_complete=complete_slack_names)
@click.option('-k', '--key', help="JIRA ticket number (key) to post a comment on; i.e. PUBSECSRE-123", type=str, required=False, default=None, multiple=True)
@click.option('-p', '--project', help="JIRA project to search for tickets to transition; i.e. PUBSECSRE", type=str, required=False, default=None)
@click.option('-e', '--emoji', help='emoji name to react with', required=False, type=str, shell_complete=complete_emojis, default='white_check_mark')
@click.pass_context
def stop(ctx, channel, key, project, emoji):
    SPOOL = {}
    if key:
        for k in key:
            profile = get_user_profile_based_on_key(k)
            SPOOL[k] = profile
    elif project:
        profile = get_user_profile_based_on_key(project)
    else:
        Log.critical("One of the following fields is required: key, project.")

    if project:
        key = setup_project(project, profile)
        SPOOL[key] = profile

    if not key:
        Log.critical("no issue key found")

    if detect_environment() == 'non-gc':
        if not emoji:
            Log.critical("please provide the apprpopriate emoji to indicate success/failure: x, white_check_mark, vpause")
        if not channel:
            Log.critical("please provide the apprpopriate channel for slack communications")
        for key in SPOOL:
            PROFILE = CONFIG.get_profile(key)
            if PROFILE is None or PROFILE['config'] == {}:
                Log.critical(f"Unable to proceed because the profile {key} does not exist")
            timestamp = PROFILE['config']['start']
            mycomment = (f"INFO: change completed and marking ticket closed")
            RESULT = comment(key, mycomment, SPOOL[key])
            if RESULT:
                Log.info(f'ticket commented successfully, and change notification in progress to close ticket {key}.')
            TIMESTAMP = react.post_slack_reaction(channel, timestamp, emoji)
            for result in TIMESTAMP:
                myresult = result["ok"]
                CONFIG.update_config(myresult, "stop", key)
                CONFIG.update_config(emoji, "reaction", key)
            Log.info(f'Operation succesfull; slack reaction: {result["ok"]}')
            ANS = input("INFO: was the change successful? (y/n): ")
            if 'y' in ANS or 'Y' in ANS:
                key = convertTuple(key)
                TARGET_STATUS_NAME = 'Verify'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, SPOOL[key])
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                TARGET_STATUS_NAME = 'Success'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, SPOOL[key])
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                    if RESULT:
                        Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                        Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')
                TARGET_STATUS_NAME = 'Closed Successful'
                END = datetime.datetime.now()
                START = END - datetime.timedelta(hours=2)
                END = END.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                START = START.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                TRANSITION_PAYLOAD = localCscmUpdateTicket(START, END, TARGET_STATUS_NAME)
                TARGET_STATUS_ID = '201'
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                    if RESULT:
                        Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                        Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')
                FLY = Client()
                mykey = convertTuple(key) # tuple again
                job = get_runway_job(mykey) # get the runway job url
                if job:
                    team = job.split("/")[4]
                    RESULT = FLY.trigger_post_deploy_job(team, user_profile=ctx.obj['profile'])
                    if RESULT:
                        RESULT = FLY.get_post_deploy_results(team, user_profile=ctx.obj['profile'])
                else:
                    Log.warn(f"was not able to find the post-deploy job using ticket key: {key} - skipping post-deploy build.")
                    team = 'N/A'
                    RESULT = None
                if RESULT:
                    for I in RESULT:
                        Log.json(json.dumps(I, indent=2, sort_keys=True))
                        break
                    CONFIG.update_config(job, "post-deploy", key)
                    CONFIG.update_config(I, "post-deploy-status", key)
                else:
                    CONFIG.update_config('n/a', "post-deploy", key)
                    CONFIG.update_config('n/a', "post-deploy-status", key)
            else:
                key = convertTuple(key)
                TARGET_STATUS_NAME = 'Failed'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, SPOOL[key])
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                TARGET_STATUS_NAME = 'Closed Unsuccessful'
                END = datetime.datetime.now()
                START = END - datetime.timedelta(hours=2)
                END = END.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                START = START.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                TRANSITION_PAYLOAD = localCscmUpdateTicket(START, END, TARGET_STATUS_NAME)
                TARGET_STATUS_ID = '201'
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                    if RESULT:
                        Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                        Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')
    else:
        for key in SPOOL:
            profile = SPOOL[key]
            ANS = input("INFO: was the change successful? (y/n): ")
            if 'y' in ANS or 'Y' in ANS:
                mycomment = (f"INFO: change completed successfully and marking ticket closed")
                RESULT = comment(key, mycomment, profile)
                if RESULT:
                    Log.info(f'ticket commented successfully, and change notification in progress to close ticket {key}.')
                key = convertTuple(key)
                TARGET_STATUS_NAME = 'Verify'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, profile)
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, profile)
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                TARGET_STATUS_NAME = 'Success'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, profile)
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, profile)
                    if RESULT:
                        Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                        Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')
                TARGET_STATUS_NAME = 'Closed Successfully'
                TARGET_STATUS_ID = '221'
                END = datetime.datetime.now()
                START = END - datetime.timedelta(hours=2)
                END = END.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                START = START.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                TRANSITION_PAYLOAD = prodCscmUpdateTicket(START, END, TARGET_STATUS_NAME)
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                    if RESULT:
                       Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                       Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')
            else:
                mycomment = (f"INFO: change completed unsuccessfully and marking ticket closed.")
                RESULT = comment(key, mycomment, profile)
                if RESULT:
                    Log.info(f'ticket commented successfully, and change notification in progress to close ticket {key}.')
                key = convertTuple(key)
                TARGET_STATUS_NAME = 'Verify'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, profile)
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, profile)
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                TARGET_STATUS_NAME = 'Failed'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, profile)
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, profile)
                    if RESULT:
                        Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                        Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')
                TARGET_STATUS_NAME = 'Closed Unsuccessfully'
                TARGET_STATUS_ID = '221'
                END = datetime.datetime.now()
                START = END - datetime.timedelta(hours=2)
                END = END.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                START = START.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
                TRANSITION_PAYLOAD = prodCscmUpdateTicket(START, END, TARGET_STATUS_NAME)
                try:
                    RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                    if RESULT:
                       Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                    else:
                       Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')
                except:
                    Log.warn(f'Operation unsuccesfull. Issue key or transition field not found.')

def build_slack_message(title, issue, reporter):
    start = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000-0700')
    duration = "1 hour"
    assignee = os.environ["LOGNAME"]
    info = " Maintenance Title: %s \n Ticket: %s \n Start Time: %s \n Duration: %s \n Impact: (low) \n Regions: us-gov-west-1 \n Change Executor: %s \n Change Reporter: %s" %(title, issue, start, duration, assignee, reporter)
    text="INFO: VMC PubSecSRE team will be starting the following change now: " + "```\n" + info + "\n```" + "\nINFO: this thread will be updated with any issues & completion status."
    return text

def convertTuple(tup):
    # initialize an empty string
    str = ''
    for item in tup:
        str = str + item
    return str

def _dictionarify(issues, csv, json, wizard, user_profile=None):
    TOTAL = 0
    if user_profile is None:
        try:
            JIRA_SESSION, user_profile = get_jira_session_based_on_key(str(issues[0].key))
        except Exception as e:
            Log.critical('invalid JQL query or the search failed')
    ISSUES = []
    for ISSUE in issues:
        TOTAL = TOTAL + 1
        ISSUE_DICT = {}
        ISSUE_DICT['key'] = str(ISSUE.key)
        ISSUE_DICT['status'] = str(ISSUE.fields.status)
        ISSUE_DICT['assignee'] = str(ISSUE.fields.assignee)
        ISSUE_DICT['reporter'] = str(ISSUE.fields.reporter)
        ISSUE_DICT['summary'] = str(ISSUE.fields.summary)
        if not csv and not json and not wizard:
            ISSUE_DICT['launcher'] = create_link(build_url(str(ISSUE.key), user_profile), str(ISSUE.key))
        elif wizard:
            ISSUE_DICT.pop('assignee')
            ISSUE_DICT.pop('reporter')
        else:
            ISSUE_DICT['launcher'] = build_url(str(ISSUE.key), user_profile)
        ISSUES.append(ISSUE_DICT)
    return TOTAL, ISSUES

def setup_project(project, profile):
    # default to project tuple
    project = (project,)
    # default to the user's logname
    assignee = (os.environ["LOGNAME"].split("@")[0],)
    # default to descending order
    ascending = False
    descending = True
    # turn on the wizard
    wizard = True
    # set all of these to None
    orderby = jql = key = limit = csv = json =  None
    # these need to be tuples
    group = reporter = status = summary = description = ()
    ISSUES, JQL = search_issues(jql, project, key, assignee, group, reporter, status, summary, description, limit, orderby, ascending, descending, profile)
    TOTAL, ISSUES = _dictionarify(ISSUES, csv, json, wizard, profile)
    CHOICE = runMenu(ISSUES, JQL)
    if CHOICE is not None:
        if CHOICE[0]:
            key = CHOICE[0].strip()
    return key

def buildMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'Build Menu: {INPUT}'
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

def localCscmUpdateTicket(startdate, stopdate, name):
    data = {
               "customfield_17357": "%s" %(startdate),
               "customfield_11306": "%s" %(stopdate),
               "resolution": {
                   "name": "%s" %(name)
               }
           }
    return data

def prodCscmUpdateTicket(startdate, stopdate, name):
    data = {
               "customfield_10806": "%s" %(startdate),
               "customfield_10410": "%s" %(stopdate),
               "resolution": {
                   "name": "%s" %(name)
               }
           }
    return data
