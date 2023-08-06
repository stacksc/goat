import csv, time, click
import json as jjson
from tabulate import tabulate
from .auth import get_jira_session, get_jira_url, get_jira_session_based_on_key, get_user_profile_based_on_key
from . import transitions
from toolbox.logger import Log
from toolbox.menumaker import Menu
from toolbox.menuboard import MenuBoard
from toolbox.click_complete import complete_jira_profiles

@click.command(help="search for issues in Jira", context_settings={'help_option_names':['-h','--help']})
@click.option('-k', '--key', help="i.e. PUBSECSRE-123", type=str, required=False, multiple=True, default=None)
@click.option('-p', '--project', help="i.e. PUBSECSRE", type=str, required=False, multiple=True, default=None)
@click.option('-a', '--assignee', help="i.e. jdoe", type=str, required=False, multiple=True)
@click.option('-g', '--group', help="i.e. devops", type=str, required=False, multiple=True)
@click.option('-r', '--reporter', help="i.e. smithj", type=str, required=False, multiple=True)
@click.option('-s', '--status', help="i.e. closed", type=str, required=False, multiple=True)
@click.option('--summary', help="text to search for in the summary field", type=str, required=False, multiple=True)
@click.option('--description', help="text to search for in the description field", type=str, required=False, multiple=True)
@click.option('-j', '--jql', help="ignore other filters and use explicit jql query", type=str, required=False)
@click.option('-J', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-w', '--wizard',help="output results in wizard format for transitioning", is_flag=True, show_default=True, default=False, required=False)
@click.option('-t', '--tui',help="use the native TUI to launch tickets in the browser", is_flag=True, show_default=True, default=False, required=False)
@click.option('-l', '--limit', help="max amount of issues to show", type=int, required=False)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.pass_context
def search(ctx, project, key, assignee, group, reporter, status, summary, description, jql, limit, csv, json, wizard, tui, orderby, ascending, descending):
    if ctx.obj['PROFILE'] is None:
        if key != () or project != ():
            if key != ():
                profile = get_user_profile_based_on_key(key)
            if project != ():
                profile = get_user_profile_based_on_key(project)
        else:
            Log.critical("One of the following fields is required: key, project")
    run_jql_query(project, key, assignee, group, reporter, status, summary, description, jql, limit, csv, json, wizard, tui, orderby, ascending, descending, ctx.obj['PROFILE'])

def run_jql_query(project, key, assignee, group, reporter, status, summary, description, jql, limit, csv, json, wizard, tui, orderby, ascending, descending, user_profile=None, data=False):
    START = time.time()
    ISSUES, JQL = search_issues(jql, project, key, assignee, group, reporter, status, summary, description, limit, orderby, ascending, descending, user_profile)
    TOTAL, ISSUES = _dictionarify(ISSUES, csv, json, wizard, tui, user_profile)
    END = time.time()
    RUNTIME = END - START

    if TOTAL == 0:
        Log.info(f"scanned {TOTAL} tickets in {RUNTIME} seconds\n")
    elif data:
        return ISSUES
    elif json:
        print(jjson.dumps(ISSUES, indent=2, sort_keys=True))
    elif csv:
        save_query_results(ISSUES, csv)
    elif wizard or tui:
        if wizard:
            CHOICE = runMenu(ISSUES, JQL)
            if CHOICE is not None:
                if CHOICE[0]:
                    TRIM_CHOICE = CHOICE[0].strip()
                    if not transitions.transition_wizard(TRIM_CHOICE, user_profile):
                        Log.critical("Transition with a wizard failed. Please transition the issue with --payload or --field_* arguments")
                    else:
                        Log.info(f"Transitioning is complete for {CHOICE[0]}")
        else:
            runMenuBoard(ISSUES, JQL)
    else:
        JQL = JQL.lstrip()
        Log.info(f"{JQL}")
        Log.info(f"scanned {TOTAL} tickets in {RUNTIME} seconds\n")
        Log.info(f"\n{tabulate(ISSUES, headers='keys', tablefmt='rst')}")

def add(self, key, value):
    self[key] = value

def get_comms_data(key, user_profile):
    orderby = 'CREATED'
    ascending = None
    descending = True
    JIRA_SESSION = get_jira_session(profile_name=user_profile)
    key = (key,)
    JQL = add_search_statement("", 'key', key)
    if JQL.split()[-1] == 'AND':
        JQL = ' '.join(JQL.split(' ')[:-1])
    JQL = add_order_statement(JQL, orderby, ascending, descending)
    try:
        ISSUES = JIRA_SESSION.search_issues(JQL)
        return ISSUES
    except:
        Log.critical('invalid JQL query or the search failed')

def search_issues(jql, project, key, assignee, group, reporter, status, summary, description, limit, orderby, ascending, descending, user_profile):
    JIRA_SESSION = get_jira_session(profile_name=user_profile)
    if jql is None:
        if key is not None:
            if len(key) != 0:
                JQL = add_search_statement("", 'key', key)
            else:
                JQL = build_jql(project, assignee, group, reporter, status, summary, description)
        else:
            JQL = build_jql(project, assignee, group, reporter, status, summary, description)
        if JQL.split()[-1] == 'AND':
            JQL = ' '.join(JQL.split(' ')[:-1])
        JQL = add_order_statement(JQL, orderby, ascending, descending)
    else:
        JQL = jql
    try:
        ISSUES = JIRA_SESSION.search_issues(JQL, maxResults=limit)
        return ISSUES, JQL
    except FileExistsError:
        Log.critical('invalid JQL query or the search failed')
    
def build_jql(project, assignee, group, reporter, status, summary, description, JQL=""):
    JQL = add_search_statement(JQL, 'project', project)
    JQL = add_search_statement(JQL, 'assignee', assignee)
    JQL = add_search_statement(JQL, 'group', group)
    JQL = add_search_statement(JQL, 'reporter', reporter)
    JQL = add_search_statement(JQL, 'status', status)
    JQL = add_search_statement(JQL, 'summary', summary, '~')
    JQL = add_search_statement(JQL, 'description', description, '~')
    return JQL

def add_search_statement(JQL, name, items, operator='='):
    if items is not None and len(items) != 0:
        if len(items) > 1:
            JQL = f'{JQL} ('
            for item in items:
                JQL = f'{JQL} {name} {operator} "{item}" OR'
            JQL = ' '.join(JQL.split(' ')[:-1])
            JQL = f'{JQL} ) AND'
        else:
            JQL = f'{JQL} {name} {operator} "{items[0]}" AND'
    return JQL

def add_order_statement(jql, orderby, ascending, descending):
    if orderby is not None:
        jql = f"{jql} ORDER BY {orderby}"
        if ascending is True:
            jql = f"{jql} ASC"
        elif descending is True:
            jql = f"{jql} DESC"
    else:
        # default to this
        if ascending is True:
            jql = f"{jql} ORDER BY created ASC"
        elif descending is True:
            jql = f"{jql} ORDER BY created DESC"
    return jql

def save_query_results(issues, csvfile):
    ROWS = ['key', 'status', 'assignee', 'reporter', 'summary', 'launcher']
    with open(csvfile, 'w') as CSV:
        writer = csv.DictWriter(CSV, fieldnames=ROWS)
        writer.writeheader()
        writer.writerows(issues)

def create_link(url, label=None):
    if label is None:
        label = url
    parameters = ''
    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return escape_mask.format(parameters, url, label)

def build_url(issue_key, user_profile):
    try:
        JIRA_URL = get_jira_url(user_profile)
    except:
        Log.critical("Failed to get JIRA URL. Please verify your configuration details, server URL, profile, etc.")
    url = JIRA_URL + '/browse/%s' %(issue_key)
    return url

def _dictionarify(issues, csv, json, wizard, tui, user_profile=None):
    TOTAL = 0
    if user_profile is None:
        try:
            JIRA_SESSION, user_profile = get_jira_session_based_on_key(str(issues[0].key))
        except:
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
        if not csv and not json and not wizard and not tui:
            ISSUE_DICT['launcher'] = create_link(build_url(str(ISSUE.key), user_profile), str(ISSUE.key))
        elif wizard or tui:
            ISSUE_DICT.pop('assignee')
            ISSUE_DICT.pop('reporter')
        else:
            ISSUE_DICT['launcher'] = build_url(str(ISSUE.key), user_profile)
        ISSUES.append(ISSUE_DICT)
    return TOTAL, ISSUES

def runMenu(ISSUES, JQL):
    FINAL = []
    COUNT = 0
    for ISSUE in ISSUES:
        COUNT = COUNT + 1
        RESULTS = []
        for key, val in ISSUE.items():
            val = val.ljust(20)
            if 'launcher' in key:
                continue
            RESULTS.append(val)
        FINAL.append(RESULTS)
    TITLE = 'JIRA Issue Menu'
    JOINER = '\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, JQL)
    CHOICE = FINAL_MENU.display()
    return CHOICE

def runMenuBoard(ISSUES, JQL):
    FINAL = []
    COUNT = 0
    for ISSUE in ISSUES:
        COUNT = COUNT + 1
        RESULTS = []
        for key, val in ISSUE.items():
            val = val.ljust(20)
            if 'launcher' in key:
                continue
            RESULTS.append(val)
        FINAL.append(RESULTS)
    TITLE = 'JIRA Launch Board'
    JOINER = '\t'
    FINAL_MENU = MenuBoard(FINAL, TITLE, JOINER, JQL)
    CHOICE = FINAL_MENU.display()
    return CHOICE
