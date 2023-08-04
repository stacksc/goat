import click, json, pprint, re, sys, os, time, csv, datetime, readline
from jiratools.issue import add_comment as comment, get_inb_data, global_assign, extract_data_from_issue
from jiratools.auth import get_user_profile_based_on_key, get_jira_session_based_on_key
from jiratools.search import get_comms_data, build_url, search_issues, runMenu as jiraRunMenu, create_link
from nexustools.nexusclient import NexusClient
from .cspclient import CSPclient
from .idpclient import idpc
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import MenuResults as MenuResults
from tabulate import tabulate
from toolbox import misc
from jenkinstools.jenkinsclient import JenkinsClient

JENKINS = JenkinsClient()
CSP = CSPclient()
NEXUS = NexusClient()
CONFIG = Config('csptools')
CSP_LIST = ['csp-account-management-mvc','csp-api-gateway','csp-authn','csp-commerce','csp-console-frontend','csp-email','csp-ff-service','csp-iam-roles-mgmt','csp-onboarding','csp-post-office','csp-resource-manager','csp-rtc','csp-servicve-lifecycle','ns-event-service','ns-inapp']

@click.group('upgrade', help='CSP end-to-end upgrade tasks', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def upgrade(ctx):
    pass

@upgrade.command(help='perform CSP upgrade preparation tasks', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.option('-t', '--ticket', 'ticket', help="provide CSSD ticket", type=str, required=False, default=None)
@click.option('-s', '--skip', 'skip', help="CSP micro-services to skip if required", required=False, default=None, type=click.Choice(CSP_LIST), multiple=True)
@click.pass_context
def prep(ctx, ticket, skip):
    OPTION = ''
    while OPTION != 'Quit':
        OPTIONS = ['DP Process Transaction', 'CSP System Jenkins YAML Deploy', 'CSP Upgrade Pipeline', 'Console Output Review', 'Quit']
        DATA = []
        for OPTION in OPTIONS:
            STR = OPTION.ljust(60)
            DATA.append(STR)
        INPUT = 'CSP Upgrade Tasks'
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

        if 'DP Process Transaction' in OPTION:
            CONFIG = Config('csptools')
            SUMMARY = 'CSP Gov Production Upgrade'
            if not ticket:
                ticket = setup_project('CSCM', SUMMARY.strip(), profile='default')
                if not ticket:
                    ticket = input('Enter ticket key: ')
            if not ticket:
                Log.critical('unable to find a CSP upgrade ticket, exiting')
            else:
                TICKET = ticket
            PROFILE = get_user_profile_based_on_key(TICKET)
            if PROFILE:
                RESPONSE = get_comms_data(TICKET, PROFILE)
                ISSUES = []
                KEY = (TICKET,)
                for ISSUE in RESPONSE:
                    ISSUE_DICT = {}
                    ISSUE_DICT['key'] = str(ISSUE.key)
                    ISSUE_DICT['summary'] = str(ISSUE.fields.summary)
                    ISSUE_DICT['status'] = str(ISSUE.fields.status)
                    ISSUE_DICT['assignee'] = str(ISSUE.fields.assignee)
                    ISSUE_DICT['reporter'] = str(ISSUE.fields.reporter)
                    DESC = str(ISSUE.fields.description)
                    ISSUES.append(ISSUE_DICT)

                    # save the rollback transaction ID
                    DATA_KEY = "Rollback Transaction-ID"
                    ROLLBACK_ID = extract_data_from_issue(KEY, DATA_KEY, False, PROFILE)
                    if ROLLBACK_ID:
                        Log.info(f'rollback transition-ID found in ticket: {ROLLBACK_ID}')
                    Log.info(f"\n{tabulate(ISSUES, headers='keys', tablefmt='rst')}\n")
                    SERVICES = []
                    IDS = []
                    for LINE in DESC.split('\n'):
                        SERVICE_DICT = {}
                        if LINE.startswith('s_'):
                            TXID = LINE.split(':')[0].replace('s_','').strip()
                            IDS.append(TXID)
                            SERVICE = LINE.split(':')[1].strip()
                            TAG = LINE.split(':')[2].replace('\r','').strip().replace('{code}','')
                            if SERVICE in skip:
                                print(f'searching nexus for {SERVICE} {TAG}', end='', flush=True)
                                print(misc.MOVE2 + misc.YELLOW + misc.UNDERLINE + 'SKIP' + misc.RESET)
                                continue
                            SERVICE_DICT = { 'service': SERVICE, 'transaction-id': TXID, 'tag': TAG }
                            print(f'searching nexus for {SERVICE} {TAG}', end='', flush=True)
                            OUTPUT = NEXUS.list_tag_details(SERVICE, TAG, raw=False)
                            if OUTPUT:
                                SERVICE_DICT.update({'nexus': True })
                                print(misc.MOVE2 + misc.GREEN + misc.UNDERLINE + 'PASS' + misc.RESET)
                            else:
                                SERVICE_DICT.update({'nexus': False })
                                print(misc.MOVE2 + misc.RED + misc.UNDERLINE + 'FAIL' + misc.RESET)
                            SERVICES.append(SERVICE_DICT)
                    print()
                    Log.info(f"\n{tabulate(SERVICES, headers='keys', tablefmt='rst')}\n")
            ANS = input(f"\nINFO: would you like to start change {TICKET} now? (y/n): ")
            CONF_PROFILE = CONFIG.get_profile(TICKET)
            USERNAME = os.environ["LOGNAME"].split("@")[0]
            CT = datetime.datetime.now()
            TS = CT.timestamp()
            if CONF_PROFILE is None or CONF_PROFILE['config'] == {}:
                Log.info(f"profile not found -> creating a new profile for ticket {TICKET}")
                CONFIG.create_profile(TICKET)
                CONFIG.update_config(TS, "start", TICKET)
                CONFIG.update_config(SERVICES, "services", TICKET)
            else:
                Log.info(f"profile found -> updating profile for ticket {TICKET}")
                CONFIG.update_config(TS, "start", TICKET)
                CONFIG.update_config(SERVICES, "services", TICKET)
            if ANS == 'y' or ANS == 'Y':
                TICKET = (TICKET,)
                RESULT = global_assign(TICKET, USERNAME, PROFILE)

            IDS = listToStringWithoutBrackets(IDS).replace(' ','')
            SERVER='https://delta-prd-jenkins.vmwarefed.com'
            JOB = 'dp-process-transaction-us-gov-west-1-prd'
            JSONDICT = {}
            JSONDICT['SERVICE_DESK_TICKET_ID'] = TICKET
            JSONDICT['DATA_TX_ID'] = IDS
            ctx.obj['profile'] = 'delta'
            sleeper=10
            Log.info(f"please see the following build information:")
            print()
            Log.info(f'url: ->\n\t{SERVER}')
            Log.info(f'job: ->\n\t{JOB}')
            Log.info(f'params: ->\n\t{JSONDICT}')
            print()

            ANS = input(f"would you like to trigger the build now (y/n): ")
            if ANS == 'y' or ANS == 'Y':
                CONFIG.update_config(JOB, "job", TICKET)
                CONFIG.update_config(JSONDICT, "params", TICKET)
                MYURL = JENKINS.build_url(JOB, JSONDICT, user_profile=ctx.obj['profile'])
                RESULT = JENKINS.launch_job(JOB, JSONDICT, files={}, wait=True, interval=30, time_out=7200, sleep=sleeper, user_profile=ctx.obj['profile'])
                print()
                if RESULT:
                    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
                    Log.info(f"full URL: {MYURL}")
                    mykey = (TICKET,)
                    TEMPLATE = "\n" + str(RESULT) + "\n"
                    profile = get_user_profile_based_on_key(TICKET)
                    RCODE = comment(mykey, TEMPLATE, profile)
                    if RCODE:
                        Log.info(f'ticket commented with job output.')
                    print()
                    CONFIG.update_config(RESULT, "result", TICKET)
                else:
                    Log.warn("the launch job returned an empty string. Please look into this job in Jenkins console.")
            else:
                CONFIG.update_config(JOB, "job", TICKET)
                CONFIG.update_config(JSONDICT, "params", TICKET)
                MYURL = JENKINS.build_url(JOB, JSONDICT, user_profile=ctx.obj['profile'])
                MYURL = MYURL.replace('/buildWithParameters?','/parambuild/?')
                CONFIG.update_config("skipping", "result", TICKET)
                Log.info("skipping build now...")
                Log.info(f"full URL: {MYURL}")
        elif 'CSP System Jenkins YAML Deploy' in OPTION:
            CONFIG = Config('csptools')
            SUMMARY = 'CSP Gov Production Upgrade'
            if not ticket:
                ticket = setup_project('CSCM', SUMMARY.strip(), profile='default')
                if not ticket:
                    ticket = input('Enter ticket key: ')
            if not ticket:
                Log.critical('unable to find a CSP upgrade ticket, exiting')
            else:
                TICKET = ticket
            SERVER='https://delta-prd-jenkins.vmwarefed.com'
            JOB = 'csp_system_jenkins_yaml_deploy_dockerized'
            JSONDICT = {}
            ctx.obj['profile'] = 'delta'
            sleeper=10
            Log.info(f"please see the following build information:")
            print()
            Log.info(f'url: ->\n\t{SERVER}')
            Log.info(f'job: ->\n\t{JOB}')
            print()

            ANS = input(f"would you like to trigger the build now (y/n): ")
            if ANS == 'y' or ANS == 'Y':
                CONFIG.update_config(JOB, "job", TICKET)
                CONFIG.update_config(JSONDICT, "params", TICKET)
                MYURL = JENKINS.build_url(JOB, JSONDICT, user_profile=ctx.obj['profile'])
                RESULT = JENKINS.launch_job(JOB, JSONDICT, files={}, wait=True, interval=30, time_out=7200, sleep=sleeper, user_profile=ctx.obj['profile'])
                print()
                if RESULT:
                    Log.json(json.dumps(RESULT, indent=2, sort_keys=True))
                    Log.info(f"full URL: {MYURL}")
                    mykey = (TICKET,)
                    TEMPLATE = "\n" + str(RESULT) + "\n"
                    profile = get_user_profile_based_on_key(TICKET)
                    RCODE = comment(mykey, TEMPLATE, profile)
                    if RCODE:
                        Log.info(f'ticket commented with job output.')
                    print()
                    CONFIG.update_config(RESULT, "result", TICKET)
                else:
                    Log.warn("the launch job returned an empty string. Please look into this job in Jenkins console.")
            else:
                CONFIG.update_config(JOB, "job", TICKET)
                CONFIG.update_config(JSONDICT, "params", TICKET)
                MYURL = JENKINS.build_url(JOB, JSONDICT, user_profile=ctx.obj['profile'])
                MYURL = MYURL.replace('/build','/parambuild/?')
                CONFIG.update_config("skipping", "result", TICKET)
                Log.info("skipping build now...")
                Log.info(f"full URL: {MYURL}")

        elif 'Console' in OPTION:
            DATA = []
            ctx.obj['pattern'] = 'csp'
            ctx.obj['profile'] = 'delta'
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
                                                       
            RESULT = JENKINS.get_console_output(url, raw=False, user_profile=ctx.obj['profile'])
            for RESULT in RESULT.split("\n"):
                print(RESULT)
        elif 'Quit' in OPTION:
            sys.exit()
        wait_for_enter()

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace("{","").replace("}","")

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'CSP Menu: {INPUT}'
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

def wait_with_message(seconds):
    while True:
        Log.info(f"sleeping for {seconds} seconds, please wait...")
        time.sleep(30)
        seconds = seconds - 30
        if seconds <= 0:
            Log.info("FINISHED")
            break
    return True

def wait_for_enter():
    time.sleep(2)
    print()
    return input('press ENTER to continue: ')

def get_operator_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'operator'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def get_platform_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'platform'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def convertTuple(tup):
    # initialize an empty string
    str = ''
    for item in tup:
        str = str + item
    return str

def setup_project(project, summary, profile='default'):
    # default to project tuple
    project = (project,)
    # default to descending order
    ascending = False
    descending = True
    # turn on the wizard
    wizard = True
    # set all of these to None
    orderby = jql = key = limit = csv = json =  None
    # these need to be tuples
    assignee = group = reporter = status = description = ()
    summary = (summary,)
    ISSUES, JQL = search_issues(jql, project, key, assignee, group, reporter, status, summary, description, limit, orderby, ascending, descending, profile)
    TOTAL, ISSUES = _dictionarify(ISSUES, csv, json, wizard, profile)
    CHOICE = jiraRunMenu(ISSUES, JQL)
    if CHOICE is not None:
        if CHOICE[0]:
            key = CHOICE[0].strip()
    return key

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
