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

@click.group(help="pipeline tasks initiated in/out-boundary per CSCM ticket to stop changes", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()}, invoke_without_command=True)
@click.pass_context
def stop(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = 'default'
    pass

@stop.command(help='transition tickets to close, with necessary pipeline tasks included', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
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
                
                TARGET_STATUS_NAME = 'Rollback'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, SPOOL[key])
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')

                TARGET_STATUS_NAME = 'Incomplete'
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

                TARGET_STATUS_NAME = 'Rollback'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, SPOOL[key])
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')

                TARGET_STATUS_NAME = 'Incomplete'
                TRANSITION_PAYLOAD = None
                TARGET_STATUS_ID = get_status_id(key, TARGET_STATUS_NAME, SPOOL[key])
                RESULT = transition_issue(key, TARGET_STATUS_ID, TRANSITION_PAYLOAD, SPOOL[key])
                if RESULT:
                    Log.info(f'ticket transitioned successfully to {TARGET_STATUS_NAME} and ID {TARGET_STATUS_ID}')
                else:
                    Log.critical(f'Operation unsuccesfull. Issue key not found in jira.')

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
