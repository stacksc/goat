import os, click, re, json
from .auth import get_jira_session
from .auth import get_jira_session_based_on_key
from .auth import get_user_profile_based_on_key
from .transitions import get_transitions, format_transitions_json, get_status_id, build_payload_from_input, transition_issue, transition_wizard
from .search import run_jql_query, runMenu
from toolbox.logger import Log
from toolbox.click_complete import complete_jira_profiles
from toolbox.misc import detect_environment, remove_html_tags

@click.group(help="manage JIRA issues", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def issue(ctx):
    pass

@issue.command('search', help="show a summary of specified issue or issues", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-J', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-w', '--wizard',help="output results in wizard format for transitioning", is_flag=True, show_default=True, default=False, required=False)
@click.option('-t', '--tui',help="use the native TUI to launch tickets in the browser", is_flag=True, show_default=True, default=False, required=False)
@click.option('-l', '--limit', help="max amount of issues to show", type=int, required=False)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.pass_context
def search_issues(ctx, issue_keys, limit, csv, json, tui, wizard, orderby, ascending, descending, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    run_jql_query(None, issue_keys, None, None, None, None, None, None, None, limit, csv, json, wizard, tui, orderby, ascending, descending, profile)

@issue.command('attach', help="attach a file to a given JIRA issue(s)", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-a', '--attach', help="name of file to attach", type=click.Path(exists=True))
@click.pass_context
def attach_file(ctx, issue_keys, attach, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = add_attachment(issue_keys, attach, profile)
    if RESULT:
        Log.info("File attached")

@issue.command('review', help='change the VMC Ops Review to Yes or No for a JIRA issue', context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_key', nargs=-1, type=str, required=True)
@click.option('-v', '--value', help="value to be used", required=True, default=None, type=click.Choice(['Yes', 'No']))
@click.pass_context
def review(ctx, issue_key, value, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    review_issue(issue_key, value, profile)
    Log.info(f"VMC Ops Review is complete and set to {value}")

@issue.command('assign', help="change assignee of a given JIRA issue(s)", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-a', '--assignee', help="assignee name, i.e. " + os.environ["LOGNAME"], type=str, required=False, default=None)
@click.pass_context
def assign(ctx, issue_keys, assignee=None, profile=None):
    if profile is None:
        profile = ctx.obj['profile']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = change_assignee(issue_keys, assignee, profile)
    if RESULT:
        Log.info("assignee modified")

def global_assign(issue_keys, assignee=None, profile=None):
    if profile is None:
        profile = ctx.obj['profile']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = change_assignee(issue_keys, assignee, profile)
    if RESULT:
        Log.info("assignee modified")

@issue.command('comment', help="post a comment to a given JIRA issue(s)", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-c', '--comment', help="body of the comment to post", type=str, required=True)
@click.pass_context
def comment(ctx, issue_keys, comment, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = add_comment(issue_keys, comment, profile)
    Log.info("Comment posted")
    return RESULT

@issue.command('update', help="update a field in a given JIRA issue", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_key', type=str, required=True)
@click.option('-f', '--field', 'issue_field', help="name of the field to update i.e. reporter", type=str, required=True)
@click.option('-v', '--value', 'issue_field_value', help="new value for the field i.e. jsmith", type=str, required=True)
@click.pass_context
def update(ctx, issue_key, field, value, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    update_field(issue_key, field, value, profile)
    Log.info("Field updated")

@issue.command('create', help="creates a new JIRA issue in a given project", context_settings={'help_option_names':['-h','--help']})
@click.argument('project', type=str, required=True)
@click.option('-s', '--summary', help="title of the ticket", type=str, required=True)
@click.option('-d', '--description', help="body of the ticket", type=str, required=False)
@click.pass_context
def create(ctx, project, summary, description, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(project)
    RESULT = create_issue(project, summary, description, profile)
    Log.info("Issue created")
    return RESULT

@issue.command('comments', help="look for specific data in the comments of a given issue", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-r', '--regex', 'regex', help="pattern to lookup", type=str, required=False, default=None)
@click.pass_context
def comments(ctx, issue_keys, regex, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = get_comments_from_issue(issue_keys, regex, profile)
    if regex:
        Log.info(RESULT)
    else:
        for LINE in RESULT:
            Log.info(LINE['body'])
    return RESULT


@issue.command('extract', help="look for specific data in the description of a given issue", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-k', '--key', 'data_key', help="data key to lookup", type=str, required=True)
@click.option('-e', '--exact', help="only grab exact matches", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def extract(ctx, issue_keys, data_key, exact, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = extract_data_from_issue(issue_keys, data_key, exact, profile)
    for issue_key in issue_keys:
        try:
            Log.info(f"issue {issue_key} matching {data_key}: {RESULT[issue_key]}")
        except:
            Log.warn(f"issue {issue_key} matching {data_key}: NULL") 
    return RESULT

@issue.command('change-plan', help="dump entire change implementation plan of a given issue", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_keys', nargs=-1, type=str, required=True)
@click.option('-r', '--regex', 'regex', help="pattern to lookup", type=str, required=False)
@click.option('-u', '--url', 'url', help="extract jenkins build URL", is_flag=True, required=False)
@click.option('-c', '--cred', 'cred', help="extract helm credentials for the build", is_flag=True, required=False)
@click.option('-v', '--verify', 'verify', help="verify the extracted helm credentials for the build by searching jenkins", is_flag=True, required=False)
@click.option('-p', '--post', 'post', help="extract the runway post-deploy URL from the change-plan", is_flag=True, required=False)
@click.pass_context
def change_plan(ctx, issue_keys, regex, url, cred, verify, post, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    RESULT = get_change_plan_from_issue(issue_keys, profile)
    for issue_key in issue_keys:
        try:
            for DATA in RESULT[issue_key]:
                if regex: 
                    if regex in DATA:
                        STRING = DATA.strip()
                        Log.info(STRING)
                elif url:
                    if 'jenkins' in DATA:
                        STRING = DATA.strip()
                        Log.info(STRING)
                elif post:
                    if 'runway' in DATA:
                        STRING = DATA.strip()
                        Log.info(STRING)
                elif verify is True or cred is True:
                    if 'jenkins' in DATA:
                        URL = DATA.strip()
                    if 'HELM_CREDENTIAL' in DATA:
                        STRING = DATA.strip()
                        STRING = re.findall(r"'(.*?)'", STRING)
                        if not verify:
                            Log.info(STRING)
                            return STRING
                        if 'atlas' in URL:
                            ctx.obj['profile'] = "atlas"
                        elif 'delta' in URL:
                            ctx.obj['profile'] = "delta"
                        else:
                            ctx.obj['profile'] = "default"

                        for CREDENTIAL in STRING:
                            try:
                                CHK = get_credentials(ctx, CREDENTIAL)
                                if CHK is not None:
                                    Log.info(f'creds: ->\n\t{CREDENTIAL} FOUND')
                                else:
                                    Log.info(f'creds: ->\n\t{CREDENTIAL} NOT FOUND')
                            except:
                                Log.info(f'creds: ->\n\t{CREDENTIAL} NOT FOUND')
                else:
                    print(DATA)
        except:
            Log.warn(f"issue {issue_key} description: NULL") 
    return RESULT

def get_runway_job(issue_keys):
    profile = get_user_profile_based_on_key(issue_keys)
    RESULT = get_change_plan_from_issue(issue_keys, profile)
    for DATA in RESULT[issue_keys]:
        if 'runway' in DATA:
            return DATA.strip()

def get_inb_data(issue_keys):
    profile = get_user_profile_based_on_key(issue_keys)
    RESULT = get_change_plan_from_issue(issue_keys, profile)
    CREDENTIALS = []
    BUILD_URL = []
    try:
        for DATA in RESULT[issue_keys]:
            if 'jenkins' in DATA:
                BUILD_URL = DATA.strip()
            if 'HELM_CREDENTIAL' in DATA:
                STRING = DATA.strip()
                CREDENTIALS = re.findall(r"'(.*?)'", STRING)
        return BUILD_URL, CREDENTIALS
    except:
        return None
    return None

@issue.command('transition', help="transition a given issue", context_settings={'help_option_names':['-h','--help']})
@click.argument('issue_key', type=str, required=True)
@click.option('-w', '--wizard', help="launch a wizard to guide you through transitioning an issue", is_flag=True, show_default=True, default=False, required=False)
@click.option('-s', '--showavailable', help="display the available transitions for a given issue", is_flag=True, show_default=True, default=False, required=False)
@click.option('-i', '--id', 'target_status_id', help="the ID of the state to transition to", type=str, required=False, default=None)
@click.option('-n', '--name', 'target_status_name', help="name of the state to transition to", type=str, required=False, default=None)
@click.option('-f', '--field_name', 'payload_field_name', help="name(s) of the field(s) to update during transition", type=str, required=False, multiple=True)
@click.option('-t', '--field_type', 'payload_field_type', help="value of the field(s) to update during transition", type=str, required=False, multiple=True)
@click.option('-v', '--field_value', 'payload_field_value', help="type of field(s) to update during transition", type=str, required=False, multiple=True)
@click.option('-P', '--payload', 'transition_payload', help="dict/json to be used as transition payload (field update)", type=str, required=False, default=None)
@click.pass_context
def transition(ctx, issue_key, wizard, showavailable, target_status_id, target_status_name, transition_payload, payload_field_name, payload_field_type, payload_field_value, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    if wizard:
        if not transition_wizard(issue_key, profile):
            Log.critical("Transition with a wizard failed. Please transition the issue with --payload or --field_* arguments")
        else:
            Log.info(f"Transitioning is complete for: {issue_key}")
    elif showavailable:
        RESULT = get_transitions(issue_key, profile, True)
        Log.info("Available transitions:\n"+format_transitions_json(RESULT))
        return RESULT
    else:
        if target_status_id is None:
            if target_status_name is None:
                Log.critical("Please supply a name or an id for the target status")
            else:
                target_status_id = get_status_id(issue_key, target_status_name, profile)
                if target_status_id is None:
                    Log.critical("Invalid status name supplied")
        if transition_payload is None:
            transition_payload = build_payload_from_input(payload_field_name, payload_field_type, payload_field_value)
        transition_issue(issue_key, target_status_id, transition_payload, profile)

def add_comment(issue_keys, comment, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    ISSUE_KEYS, JIRA_SESSION = prepare_issues_and_session(issue_keys, profile)
    try:
        RESULT = []
        for ISSUE_KEY in ISSUE_KEYS:
            RESULT.append(JIRA_SESSION.add_comment(ISSUE_KEY, comment))
        return RESULT
    except:
        Log.critical("Failed to post a comment")

def review_issue(issue_key, value, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_key)
            JIRA_SESSION = get_jira_session(profile_name=profile)
        else:
            JIRA_SESSION = get_jira_session(profile_name=profile)
    else:
        JIRA_SESSION = get_jira_session(profile_name=profile)
    # this is a custom field to modify VMC Ops Review
    issue_field = 'customfield_21117'
    issue_field_value = value
    ISSUE = JIRA_SESSION.issue(issue_key)
    UPDATE_DICT = {
            issue_field: { "value": issue_field_value }
    }
    try:
        return ISSUE.update(fields=UPDATE_DICT)
    except:
        Log.critical(f"Failed to transition VMC Ops Review to {value}")

def change_assignee(issue_keys, assignee=None, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_keys)
    ISSUE_KEYS, JIRA_SESSION = prepare_issues_and_session(issue_keys, profile)
    if assignee is None:
        ASSIGNEE = os.environ["LOGNAME"]
    else:
        ASSIGNEE = assignee
    try:
        RESULT = []
        for ISSUE_KEY in ISSUE_KEYS:
            RESULT.append(JIRA_SESSION.assign_issue(ISSUE_KEY, ASSIGNEE))
        return RESULT
    except:
        Log.critical("Failed to change assignee")

def update_field(issue_key, issue_field, issue_field_value, profile=None):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_key)
            JIRA_SESSION = get_jira_session(profile_name=profile)
        else:
            JIRA_SESSION = get_jira_session(profile_name=profile)
    else:
        JIRA_SESSION = get_jira_session(profile_name=profile)
    ISSUE = JIRA_SESSION.issue(issue_key)
    UPDATE_DICT = {
        issue_field: issue_field_value
    }
    return ISSUE.update(fields=UPDATE_DICT)

def create_issue(target_project, issue_summary, issue_description, profile=None):
    if profile is None:
        JIRA_SESSION = get_jira_session_based_on_key(target_project)[0]
    else:
        JIRA_SESSION = get_jira_session(profile_name=profile)
    try:
        return JIRA_SESSION.create_issue(
            project=target_project, 
            summary=issue_summary, 
            description=issue_description,
            issuetype={'name': 'Task'}
        )
    except:
        Log.critical("Failed to create an issue")

def get_review_status(issue_key, profile):
    if profile is None:
        profile = ctx.obj['PROFILE']
        if profile is None:
            profile = get_user_profile_based_on_key(issue_key)
            JIRA_SESSION = get_jira_session(profile_name=profile)
        else:
            JIRA_SESSION = get_jira_session(profile_name=profile)
    else:
        JIRA_SESSION = get_jira_session(profile_name=profile)
    STATUS = JIRA_SESSION.issue(issue_key).fields.customfield_21117.value
    return STATUS

def get_comments_from_issue(issue_keys, regex, profile):
    DATA = []
    ISSUE_KEYS, JIRA_SESSION = prepare_issues_and_session(issue_keys, profile)
    for ISSUE_KEY in ISSUE_KEYS:
        COMMENTS = JIRA_SESSION.issue(ISSUE_KEY).fields.comment.comments
        for COMMENT in COMMENTS:
            FOUND_COMMENTS = {}
            BODY = remove_html_tags(COMMENT.body)
            if regex is not None and regex in BODY:
                return BODY
            elif regex is None:
                FOUND_COMMENTS['body'] = BODY
                DATA.append(FOUND_COMMENTS)
    return DATA

def get_change_plan_from_issue(issue_keys, profile):
    FOUND_DESC = {}
    ISSUE_KEYS, JIRA_SESSION = prepare_issues_and_session(issue_keys, profile)
    for ISSUE_KEY in ISSUE_KEYS:
        DATA = []
        if 'prod' in detect_environment():
            ISSUE_DESC = JIRA_SESSION.issue(ISSUE_KEY).fields.customfield_11100
        else:
            ISSUE_DESC = JIRA_SESSION.issue(ISSUE_KEY).fields.customfield_13809
        for LINE in ISSUE_DESC.split('\n'): 
            LINE = LINE.strip('\r')
            DATA.append(LINE)
        FOUND_DESC[ISSUE_KEY] = DATA
    return FOUND_DESC

def extract_data_from_issue(issue_keys, data_key, exact, profile):
    ISSUE_KEYS, JIRA_SESSION = prepare_issues_and_session(issue_keys, profile)
    FOUND_VALUES = {}
    for ISSUE_KEY in ISSUE_KEYS:
        if 'prod' in detect_environment():
            TXTID = JIRA_SESSION.issue(ISSUE_KEY).fields.customfield_12600
        else:
            TXTID = JIRA_SESSION.issue(ISSUE_KEY).fields.customfield_22339
        if TXTID is None:
            ISSUE_DESC = JIRA_SESSION.issue(ISSUE_KEY).fields.description
            for LINE in ISSUE_DESC.split('\n'): 
                if data_key in LINE:
                    LINE = LINE.strip('\r') # anti-windows measure
                    if ':' in LINE:
                        KEY, VALUE = LINE.split(':') # detects key:value pair
                        if VALUE[0] == ' ':
                            VALUE = VALUE.replace(' ', '')
                        if KEY[0] == ' ':
                            KEY = KEY.replace(' ', '')
                        KEY = KEY.replace('*', '')   # removed *bold* markdown markers
                        if exact:
                            if data_key == KEY:
                                FOUND_VALUES[ISSUE_KEY] = VALUE
                        else:
                            if data_key in KEY:
                                if VALUE[0] == ' ':
                                    VALUE = VALUE.replace(' ', '')
                                FOUND_VALUES[ISSUE_KEY] = VALUE
        else:
            FOUND_VALUES[ISSUE_KEY] = TXTID
        if len(FOUND_VALUES) == 0:
            VALUE = 'UNKNOWN'
            FOUND_VALUES[ISSUE_KEY] = VALUE
    return FOUND_VALUES

def index_in_range(index, array):
    if index < len(array):
        return True
    else:
        return False

def add_attachment(issue_keys, attach_file, profile=None):
    ISSUE_KEYS, JIRA_SESSION = prepare_issues_and_session(issue_keys, profile)
    if file_is_empty(attach_file):
        Log.critical("Failed to add an attachment because file is empty")
    with open(attach_file, 'rb') as ATTACH:
        try:
            RESULT = []
            for ISSUE_KEY in ISSUE_KEYS:
                RESULT.append(JIRA_SESSION.add_attachment(issue=ISSUE_KEY, attachment=ATTACH))
            return RESULT
        except:
            Log.critical("Failed to add an attachment")

def prepare_issues_and_session(issue_keys, profile):
    try:
        ISSUE_KEYS = issue_keys.split(',')
    except:
        try:
            ISSUE_KEYS = issue_keys.split(' ')
        except:
            try:
                ISSUE_KEYS = issue_keys
            except:
                Log.critical("Issue Keys are not formatted correctly")

    if profile is None:
        JIRA_SESSION = get_jira_session_based_on_key(ISSUE_KEYS[0])[0]
    else:
        JIRA_SESSION = get_jira_session(profile_name=profile)
    return ISSUE_KEYS, JIRA_SESSION

def file_is_empty(path):
    return os.stat(path).st_size==0
