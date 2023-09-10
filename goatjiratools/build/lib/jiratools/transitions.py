import os, click, json, jira, datetime
from .auth import get_jira_session
from .auth import get_jira_url
from .auth import get_jira_user_creds
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox import curl
from toolbox.misc import detect_environment

def get_transitions(issue_key, user_profile, available=False):
    CONFIG = Config('jiratools')
    PROFILE = CONFIG.get_profile(user_profile)
    PROJECT_KEY = issue_key.split('-')[0]
    if 'transitions' not in PROFILE['metadata']['projects'][PROJECT_KEY]:
        Log.warn("New transition/status type detected - initiating caching process.  This might take a while")
        PROFILE['metadata']['projects'][PROJECT_KEY]['transitions'] = {}
    TRANSTIONS_FIELDS = pull_transition_fields(issue_key, user_profile)
    PROFILE['metadata']['projects'][PROJECT_KEY]['transitions'].update(TRANSTIONS_FIELDS)
    CONFIG.update_profile(PROFILE)
    if not available:
        # return transitons available to the ticket regardless of its current state
        return PROFILE['metadata']['projects'][PROJECT_KEY]['transitions']
    else:
        # return only transitions available to the issue in its current state
        return TRANSTIONS_FIELDS

def pull_transitions(issue_key, user_profile):
    try:
        if type(issue_key) is str:
            PROJECT_KEY = issue_key.split('-')[0]
        else:
            PROJECT_KEY = issue_key[0].split('-')[0]
    except IndexError:
        Log.critical("You must provide a issue key, project key, or a user profile to use jiratools")
    JIRA_URL = get_jira_url(user_profile)
    JIRA_CREDS = get_jira_user_creds(user_profile)
    RESULT = curl.get(
            url=f"{JIRA_URL}/rest/api/latest/issue/{issue_key}/transitions",
            auth={ 'user': JIRA_CREDS[0], 'pass': JIRA_CREDS[1] },
            headers={ 'Content-Type': 'application/json' }
        )['transitions']
    TRANSITIONS = {}
    for TRANSITION in RESULT:
        TRANSITIONS[TRANSITION['name']] = { 'id': TRANSITION['id'], 'required_fields': {} }
    return TRANSITIONS

def pull_transition_fields(issue_key, user_profile):
    JIRA_CREDS = get_jira_user_creds(user_profile)
    JIRA_URL = get_jira_url(user_profile)
    RESPONSE = curl.get(
        url=f"{JIRA_URL}/rest/api/latest/issue/{issue_key}/transitions?expand=transitions.fields",
        auth={ 'user': JIRA_CREDS[0], 'pass': JIRA_CREDS[1] },
        headers={ 'Content-Type': 'application/json' }
    )
    TRANSITIONS = {}
    for TRANSITION in RESPONSE['transitions']:
        TRANSITIONS[TRANSITION['name']] = { 'id': TRANSITION['id'], 'required_fields': {} }
        REQ_FIELDS = {}
        for FIELD_NAME in TRANSITION['fields']:
            FIELD = TRANSITION['fields'][FIELD_NAME]
            if FIELD['required'] == True:
                if 'allowedValues' in FIELD:
                    REQ_FIELDS[FIELD_NAME] = { 'id': FIELD['fieldId'], 'operation': FIELD['operations'][0], 'allowedValues': {} }
                    ALLOWED_VALUES = {}
                    for INDEX in range(len(FIELD['allowedValues'])):
                        ALLOWED_VALUE = FIELD['allowedValues'][INDEX]
                        ALLOWED_VALUES[ALLOWED_VALUE['name']] = { 'id': ALLOWED_VALUE['id'] }
                    REQ_FIELDS[FIELD_NAME]['allowedValues'].update(ALLOWED_VALUES)
                else:
                    REQ_FIELDS[FIELD_NAME] = { 'id': FIELD['fieldId'], 'operation': FIELD['operations'][0] }
        TRANSITIONS[TRANSITION['name']]['required_fields'].update(REQ_FIELDS)
    return TRANSITIONS

def get_status_id(issue_key, transition_name, user_profile):
    TRANSITIONS = get_transitions(issue_key, user_profile)
    for TRANSITION in TRANSITIONS:
        if TRANSITION == transition_name:
            return TRANSITIONS[TRANSITION]['id']
    return None

def transition_issue(issue_key, transition_id, transition_payload, user_profile, wizard=False):
    JIRA_SESSION = get_jira_session(profile_name=user_profile)
    ISSUE = JIRA_SESSION.issue(issue_key)
    REQ_FIELDS = get_req_fields(issue_key, transition_id, user_profile)
    if transition_payload is None:
        if REQ_FIELDS == {}:
            RESULT = transition_issue_without_payload(JIRA_SESSION, ISSUE, transition_id)
            if len(RESULT) == 0:
                Log.debug("Transition succesfull without a payload")
                return True
            else:
                REQ_FIELDS = RESULT
                TRANSITION_NAME = get_transition_name(issue_key, transition_id, user_profile)
                update_cached_transitions(issue_key, TRANSITION_NAME, REQ_FIELDS, user_profile)
        ERROR = 'Selected transition requires a payload for the following fields:\n'
        for REQ_FIELD in REQ_FIELDS:
            ERROR = ERROR + f"{json.dumps(REQ_FIELD, indent=2)}\n"
        if not wizard:
            open_url(build_url(str(issue_key), user_profile))
            Log.critical(ERROR)
        else:
            return REQ_FIELDS
    else:
        if REQ_FIELDS != {}:
            if not check_payload(REQ_FIELDS, transition_payload):
                ERROR = 'Selected transition requires a payload for the following fields:\n'
                ERROR = ERROR + format_req_fields_json(REQ_FIELDS)
                if not wizard:
                    open_url(build_url(str(issue_key), user_profile))
                    Log.critical(ERROR)
                else:
                    return REQ_FIELDS
        if type(transition_payload) is str:
            transition_payload = json.loads(transition_payload)
        REQ_FIELDS_NEW = transition_issue_with_payload(JIRA_SESSION, ISSUE, transition_id, transition_payload)
        if REQ_FIELDS_NEW == {}:
            return True
        else:
            TRANSITION_NAME = get_transition_name(issue_key, transition_id, user_profile)
            REQ_FIELDS = update_cached_transitions(issue_key, TRANSITION_NAME, REQ_FIELDS_NEW, user_profile)
            ERROR = 'Selected transition requires a payload for the following fields:\n'
            ERROR = ERROR + format_req_fields_json(REQ_FIELDS)
            if not wizard:
                open_url(build_url(str(issue_key), user_profile))
                Log.critical(ERROR)
            else:
                return REQ_FIELDS

def check_payload(REQ_FIELDS, PAYLOAD):
    for REQ_FIELD_NAME in REQ_FIELDS:
        if not REQ_FIELD_NAME in PAYLOAD:
            return False
    return True

def get_req_fields(issue_key, transition_id, user_profile):
    TRANSITIONS = get_transitions(issue_key, user_profile, False)
    for TRANSITION in TRANSITIONS:
        if TRANSITIONS[TRANSITION]['id'] == transition_id:
            return TRANSITIONS[TRANSITION]['required_fields']
    Log.critical("Supplied status name/ID is wrong or transitioning to it is not available in current state of the ticket")

def transition_issue_without_payload(jira_session, jira_issue, transition_id):
    try:
        REQ_FIELDS = []
        jira_session.transition_issue(jira_issue, transition_id)
    except jira.exceptions.JIRAError as EXCEPTION:
        EXCEPTION_DICT = json.loads(EXCEPTION.response.text)['errors']
        for KEY in EXCEPTION_DICT:
            REQ_FIELD = {
                'id': KEY,
                'description': EXCEPTION_DICT[KEY]
            }
            REQ_FIELDS[KEY] = REQ_FIELD
    return REQ_FIELDS

def transition_issue_with_payload(jira_session, jira_issue, transition_id, transition_payload):
    try:
        REQ_FIELDS = {}
        jira_session.transition_issue(jira_issue, transition_id, fields=transition_payload)
    except jira.exceptions.JIRAError as EXCEPTION:
        print(EXCEPTION)
        EXCEPTION_DICT = json.loads(EXCEPTION.response.text)['errors']
        for KEY in EXCEPTION_DICT:
            REQ_FIELD = {
                'id': KEY,
                'description': EXCEPTION_DICT[KEY]
            }
            REQ_FIELDS[KEY] = REQ_FIELD
    return REQ_FIELDS

def get_transition_name(issue_key, transition_id, user_profile):
    TRANSITIONS = get_transitions(issue_key, user_profile)
    for TRANSITION in TRANSITIONS:
        if TRANSITIONS[TRANSITION]['id'] == transition_id:
            return TRANSITION
    return None

def update_cached_transitions(issue_key, transition_name, req_fields, user_profile):
    CONFIG = Config('jiratools')
    PROFILE = CONFIG.get_profile(user_profile)
    PROJECT_KEY = issue_key.split('-')[0]
    for REQ_FIELD in req_fields:
        PROFILE['metadata']['projects'][PROJECT_KEY]['transitions'][transition_name]['required_fields'][REQ_FIELD] = req_fields[REQ_FIELD]
    CONFIG.update_profile(PROFILE)
    return PROFILE['metadata']['projects'][PROJECT_KEY]['transitions'][transition_name]['required_fields']

def update_cache_with_correct_payload(issue_key, payload, transition_id, user_profile):
    UPDATE_DICT = {}
    TRANSITION_NAME = get_transition_name(issue_key, transition_id, user_profile)
    for FIELD_NAME in payload:
        UPDATE_DICT[FIELD_NAME] = {}
        FIELD_DICT = {}
        for FIELD_TYPE in payload[FIELD_NAME]:
            FIELD_VALUE = payload[FIELD_NAME][FIELD_TYPE]
            FIELD_DICT[FIELD_TYPE] = FIELD_VALUE
        UPDATE_DICT[FIELD_NAME] = FIELD_DICT
    update_cached_transitions(issue_key, TRANSITION_NAME, UPDATE_DICT, user_profile)

def build_payload_from_input(field_name_tuple, field_type_tuple, field_value_tuple):
    if len(field_name_tuple) != len(field_type_tuple) and len(field_name_tuple) != len(field_value_tuple):
        Log.critical("failed building transition payload. the number of supplied field names, field types and fields values must be the same")
    PAYLOAD = {}
    for INDEX in range(len(field_name_tuple)):
        PAYLOAD[field_name_tuple[INDEX]] = { field_type_tuple[INDEX]: field_value_tuple[INDEX]}
        Log.debug(PAYLOAD)
    return PAYLOAD

def transition_wizard(issue_key, user_profile):
    TOTAL = 0
    AVAILABLE_TRANSITIONS = get_transitions(issue_key, user_profile, True)
    TRANSITION_CHOICES = []
    for TRANSITION in AVAILABLE_TRANSITIONS:
        TOTAL = TOTAL + 1
        NAME = TRANSITION
        ID = AVAILABLE_TRANSITIONS[TRANSITION]['id']
        TRANSITION_CHOICES.append([ID.ljust(10), NAME])

    # this will setup the menu to join fields by 2 tabs with a new title and subtitle
    JOINER = '\t\t'
    TITLE = 'JIRA Transitioning Menu'
    SUBTITLE = f'showing {TOTAL} available transition(s)'
    TRANSITION_MENU = Menu(TRANSITION_CHOICES, TITLE, JOINER, SUBTITLE)

    TARGET_TRANSITION_CHOICE = TRANSITION_MENU.display()
    if TARGET_TRANSITION_CHOICE:
        TARGET_TRANSITION_ID = TARGET_TRANSITION_CHOICE[0].strip()
    else:
        Log.critical("please select a target transition")

    TOTAL = 0 # reset
    TARGET_TRANSITION_REQ_FIELDS = get_req_fields(issue_key, TARGET_TRANSITION_ID, user_profile)
    if TARGET_TRANSITION_REQ_FIELDS is not []:
            REQ_FIELD_RESPONSES = []
            for REQ_FIELD_NAME in TARGET_TRANSITION_REQ_FIELDS:
                REQ_FIELD = TARGET_TRANSITION_REQ_FIELDS[REQ_FIELD_NAME]
                if 'allowedValues' in REQ_FIELD:
                    VALUE_DATA = []
                    VALUE_CHOICES = []
                    for VALUE in REQ_FIELD['allowedValues']:
                        for KEY in REQ_FIELD['allowedValues'][VALUE]:
                            VALUE_DATA.append([VALUE, KEY, REQ_FIELD['allowedValues'][VALUE][KEY]])
                    for DATA in VALUE_DATA:
                        TOTAL = TOTAL + 1
                        VALUE_CHOICES.append([DATA[2].ljust(10), DATA[0]])
                    JOINER = '\t\t' # join fields with 2 tabs
                    TITLE = 'Required Fields Menu'
                    SUBTITLE = f'showing {TOTAL} required fields'
                    REQ_FIELD_VALUE_MENU = Menu(VALUE_CHOICES, TITLE, JOINER, SUBTITLE)
                    if REQ_FIELD_VALUE_MENU is not None:
                        try:
                            REQ_FIELD_VALUE = REQ_FIELD_VALUE_MENU.display()[0].strip()
                        except:
                            Log.critical("unable to retrieve required field value")
                    else:
                        Log.critical("please select a target required field")
                    REQ_FIELD_RESPONSES.append([REQ_FIELD['id'], KEY, REQ_FIELD_VALUE])
                else:
                    Log.info(f"Update required for field {REQ_FIELD_NAME}")
                    REQ_FIELD_VALUE = input("Value to use for the update: ")
                    REQ_FIELD_VALUE_TYPE = input("Type of the value: ")
                    REQ_FIELD_RESPONSES.append([REQ_FIELD['name'], REQ_FIELD_VALUE_TYPE, REQ_FIELD_VALUE])

    TRANSITION_PAYLOAD = {}
    END = datetime.datetime.now()
    START = END - datetime.timedelta(hours=1)
    ENDTIME = END.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
    STARTTIME = START.strftime('%Y-%m-%dT%H:%M:%S.000-0700')
    JIRA_URL = get_jira_url(user_profile)

    for REQ_FIELD_RESPONSE in REQ_FIELD_RESPONSES:
        TRANSITION_PAYLOAD[REQ_FIELD_RESPONSE[0]] = { REQ_FIELD_RESPONSE[1]: REQ_FIELD_RESPONSE[2]}
        # OOB
        RESULT = detect_environment()
        if 'prod' in RESULT and 'CSCM' in issue_key:
            TRANSITION_PAYLOAD.update({"customfield_10806": STARTTIME, "customfield_10410": ENDTIME})
        else:
            if 'CSCM' in issue_key and 'customfield_17357' in REQ_FIELD_RESPONSES and 'customfield_11306' in REQ_FIELD_RESPONSES:
                TRANSITION_PAYLOAD.update({"customfield_17357": STARTTIME, "customfield_11306": ENDTIME})
    REQ_FIELDS = transition_issue(issue_key, TARGET_TRANSITION_ID, TRANSITION_PAYLOAD, user_profile)
    if type(REQ_FIELDS) is not dict:
        return True
    else:
        for REQ_FIELD_NAME in REQ_FIELDS:
            Log.info(f"Update required for field {REQ_FIELD_NAME}")
            REQ_FIELD_VALUE = input("Value to use for the update: ")
            REQ_FIELD_VALUE_TYPE = input("Type of the value: ")
            REQ_FIELD_RESPONSES.append([REQ_FIELD_NAME, REQ_FIELD_VALUE_TYPE, REQ_FIELD_VALUE])
        TRANSITION_PAYLOAD = {}
        for REQ_FIELD_RESPONSE in REQ_FIELD_RESPONSES:
            TRANSITION_PAYLOAD[REQ_FIELD_RESPONSE[0]] = { REQ_FIELD_RESPONSE[1]: REQ_FIELD_RESPONSE[2]}
        REQ_FIELDS = transition_issue(issue_key, TARGET_TRANSITION_ID, TRANSITION_PAYLOAD, user_profile)
        if type(REQ_FIELD) is not dict:
            return True
        else:
            return False

def format_req_fields_json(rf_json):
    TEXT = ""
    for FIELD_NAME in rf_json:
        FIELD = rf_json[FIELD_NAME]
        TEXT = TEXT + "  - fieldId: " + FIELD['id'] + "\n"
        if 'description' in FIELD:
            TEXT = TEXT + "    - description: " + FIELD['description'] + "\n"
        if 'operation' in FIELD:
            TEXT = TEXT + "    - operation: " + FIELD['operation'] + "\n"
        if 'allowedValues' in FIELD:
            TEXT = TEXT + "    - allowed values:\n"
            for ALLOWED_VALUE_NAME in FIELD['allowedValues']:
                ALLOWED_VALUE = FIELD['allowedValues'][ALLOWED_VALUE_NAME]
                TEXT = TEXT + "      - " + ALLOWED_VALUE_NAME + f" (id {ALLOWED_VALUE['id']})\n"
    return TEXT

def format_transitions_json(t_json):
    TEXT = ""
    for TRANSITION_NAME in t_json:
        TRANSITION = t_json[TRANSITION_NAME]
        TEXT = TEXT + "- " + TRANSITION_NAME + f" (id {TRANSITION['id']})"
        if 'required_fields' in TRANSITION:
            REQ_FIELDS = TRANSITION['required_fields']
            TEXT = TEXT + '\n' + format_req_fields_json(REQ_FIELDS)
    return TEXT

def build_url(issue_key, user_profile):
    try:
        JIRA_URL = get_jira_url(user_profile)
    except:
        Log.critical("Failed to get JIRA URL. Please verify your configuration details, server URL, profile, etc.")
    url = JIRA_URL + '/browse/%s' %(issue_key)
    return url

def open_url(URL):
    try:
        click.launch(URL)
    except:
        pass
