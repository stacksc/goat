import csv, time, click, re
from datetime import datetime
import json as jjson
from tabulate import tabulate
from .auth import get_session, get_url, get_session_based_on_key, get_user_profile_based_on_key, get_user_creds
from toolbox.logger import Log
from toolbox.menumaker import Menu
from toolbox.menuboard import MenuBoard
import requests
from configstore.configstore import Config

CONFIG = Config('azdev')

@click.command(help="search for issues in AZ DevOps", context_settings={'help_option_names':['-h','--help']})
@click.option('-k', '--key', help="i.e. 12345", type=str, required=False, multiple=True, default=None)
@click.option('-p', '--project', help="i.e. BCUProd", type=str, required=False, multiple=True, default=None)
@click.option('-a', '--assignee', help="i.e. jdoe", type=str, required=False, multiple=True)
@click.option('-d', '--details', help="display more details per ticket", is_flag=True, show_default=True, default=False, required=False)
@click.option('-r', '--reporter', help="i.e. smithj", type=str, required=False, multiple=True)
@click.option('-s', '--state', help="i.e. [Closed, Active, New, Resolved, Removed]", type=str, required=False, multiple=True)
@click.option('-t', '--title', help="text to search for in the title field", type=str, required=False, multiple=True)
@click.option('-j', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
def search(ctx, project, key, assignee, details, reporter, state, title, json, orderby, ascending, descending, csv):
    if ctx.obj['PROFILE'] is None:
        if key != () or project != ():
            if key != ():
                profile = get_user_profile_based_on_key(key)
            if project != ():
                profile = get_user_profile_based_on_key(project)
        else:
            Log.critical("One of the following fields is required: key, project")

def run_jql_query(projects, keys, assignee, details, reporter, state, title, csv, json, orderby, ascending, descending, profile):
    START = time.time()
    ISSUES = search_issues(assignee, details, reporter, state, title, projects, keys, profile, orderby, ascending)
    END = time.time()
    RUNTIME = END - START

    if json or details:
        print(jjson.dumps(ISSUES, indent=2, sort_keys=True))
    elif csv:
        save_query_results(ISSUES, csv)
    else:
        Log.info(f"\n{tabulate(ISSUES, headers='keys', tablefmt='rst')}")

def search_issues(assignee=None, details=None, reporter=None, state=None, title=None, project=None, keys=None, profile=None, orderby=None, ascending=True):
    ISSUES = []
    url = get_url(profile)
    creds = get_user_creds(profile)
    token = creds[1]
    title = title[0] if title else None
    project = project[0] if project else None
    if project is None:
        CACHED_PROJECTS = CONFIG.get_metadata('projects', profile)
        if CACHED_PROJECTS is not None:
            for CACHED_PROJECT in CACHED_PROJECTS:
                project = CACHED_PROJECT
                break

    if details is True:
        wiql = build_detailed_wiql(assignee, reporter, state, title, project, keys, orderby, ascending)
    else:
        wiql = build_wiql(assignee, reporter, state, title, project, keys, orderby, ascending)

    formatted_query = ' '.join(wiql['query'].split())
    Log.info(jjson.dumps(formatted_query, indent=2, sort_keys=True))

    # Setup headers and authentication
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    auth = ('', token)

    # Construct the API URL
    api_url = f"{url}/{project}/_apis/wit/wiql?api-version=6.0"

    # Execute the API call
    response = requests.post(api_url, headers=headers, auth=auth, json=wiql)

    if response.status_code == 200:
        ISSUES = []
        TOTAL = 0
        work_item_references = response.json()['workItems']
        for work_item_ref in work_item_references:
            # Fetch each work item by ID
            work_item_url = f"{url}/_apis/wit/workitems/{work_item_ref['id']}?api-version=6.0"
            work_item_response = requests.get(work_item_url, headers=headers, auth=auth)
    
            if work_item_response.status_code == 200:
                TOTAL = TOTAL + 1
                work_item = work_item_response.json()
                # Extract specific fields
                parsed_time = parse_datetime(work_item['fields'].get("System.CreatedDate"))
                standard_format_time = parsed_time.strftime("%B %d, %Y")
                if details is True:
                    work_item_data = {
                        "ID": work_item_ref['id'],
                        "Title": trim_string(work_item['fields'].get("System.Title")),
                        "CreatedBy": work_item['fields'].get("System.CreatedBy", {}).get("displayName", "Unknown"),
                        "CreatedDate": standard_format_time,
                        "Assignee": work_item['fields'].get("System.AssignedTo", {}).get("displayName", "Unassigned"),
                        "State": work_item['fields'].get("System.State"),
                        "AreaPath": work_item['fields'].get("System.AreaPath"),
                        "IterationPath": work_item['fields'].get("System.IterationPath"),
                        "Type": work_item['fields'].get("System.WorkItemType"),
                        "Reason": work_item['fields'].get("System.Reason"),
                        "Description": remove_html_tags(work_item['fields'].get("System.Description")),
                        "URL": work_item['url']
                    }
                else:
                    work_item_data = {
                        "ID": work_item_ref['id'],
                        "Title": trim_string(work_item['fields'].get("System.Title")),
                        "CreatedBy": work_item['fields'].get("System.CreatedBy", {}).get("displayName", "Unknown"),
                        "CreatedDate": standard_format_time,
                        "Assignee": work_item['fields'].get("System.AssignedTo", {}).get("displayName", "Unassigned"),
                        "State": work_item['fields'].get("System.State")
                    }
                ISSUES.append(work_item_data)
            else:
                print(f"Failed to retrieve work item {work_item_ref['id']}: {work_item_response.status_code}")
    else:
        print(f"Failed to retrieve work items: {response.status_code}, {response.text}")
    return ISSUES

def parse_datetime(datetime_str):
    # Split the string into the main part and the milliseconds + timezone
    try:
        main_part, ms_and_timezone = datetime_str.split('.')
        milliseconds = ms_and_timezone.rstrip('Z').ljust(3, '0')
    except:
        main_part = datetime_str.rstrip('Z')
        milliseconds = '000'

    # Reconstruct the timestamp with padded milliseconds
    formatted_datetime_str = f"{main_part}.{milliseconds}"

    # Parse the string into a datetime object
    return datetime.fromisoformat(formatted_datetime_str)

def save_query_results(issues, csvfile):
    ROWS = ['ID', 'State', 'Title', 'CreatedDate', 'Assignee', 'CreatedBy']
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

def build_detailed_wiql(assignee=None, reporter=None, states=None, title=None, project=None, keys=None, orderby=None, ascending=True):
    clauses = []
    if project:
        clauses.append(f"[System.TeamProject] = '{project}'")

    def handle_single_or_multiple(field, values):
        if len(values) > 1:
            # Handling multiple values with proper grouping
            or_clauses = [f"{field} = '{value}'" for value in values]
            return f"({ ' OR '.join(or_clauses) })"
        else:
            # Single value
            return f"{field} = '{values[0]}'"

    if keys:
        clauses.append(handle_single_or_multiple("System.Id", keys))

    if assignee:
        clauses.append(handle_single_or_multiple("System.AssignedTo", assignee))

    if reporter:
        clauses.append(handle_single_or_multiple("System.CreatedBy", reporter))

    if states:
        clauses.append(f"[System.State] = '{states}'")

    if title:
        clauses.append(f"System.Title CONTAINS '{title}'")

    query = " AND ".join(clauses)

    # Add ORDER BY clause
    if orderby:
        order_direction = "ASC" if ascending else "DESC"
        query += f" ORDER BY [{orderby}] {order_direction}"

    # Select additional fields for detailed information
    return {"query": f"""
        SELECT
            [System.Id], [System.Title], [System.State], [System.AssignedTo],
            [System.CreatedBy], [System.AreaPath], [System.TeamProject],
            [System.IterationPath], [System.WorkItemType], [System.Reason],
            [System.CreatedDate], [System.ChangedDate], [System.ChangedBy],
            [System.Description]
        FROM WorkItems
        WHERE {query}
    """}

def build_wiql(assignee=None, reporter=None, states=None, title=None, project=None, keys=None, orderby=None, ascending=True):
    clauses = []

    if project:
        clauses.append(f"[System.TeamProject] = '{project}'")

    def handle_single_or_multiple(field, values):
        if len(values) > 1:
            # Handling multiple values with proper grouping
            or_clauses = [f"{field} = '{value}'" for value in values]
            return f"({ ' OR '.join(or_clauses) })"
        else:
            # Single value
            return f"{field} = '{values[0]}'"

    if keys:
        clauses.append(handle_single_or_multiple("System.Id", keys))

    if assignee:
        clauses.append(handle_single_or_multiple("System.AssignedTo", assignee))

    if reporter:
        clauses.append(handle_single_or_multiple("System.CreatedBy", reporter))

    if states:
        clauses.append(f"[System.State] = '{states}'")

    if title:
        clauses.append(f"System.Title CONTAINS '{title}'")

    query = " AND ".join(clauses)
    if orderby:
        order_direction = "ASC" if ascending else "DESC"
        query += f" ORDER BY [{orderby}] {order_direction}"

    return {"query": f"SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.CreatedBy] FROM WorkItems WHERE {query}"}

def trim_string(s, max_length=50):
    if len(s) > max_length:
        return s[:max_length - 3] + "..."
    else:
        return s

def remove_html_tags(text):
    """Remove html tags from a string"""
    try:
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    except:
        return None

