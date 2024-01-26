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

@click.group(help="manage boards and sprints", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def boards(ctx):
    pass

@boards.command(help="search boards and sprints", context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--team', help="provide team name for board search", type=str, required=False, default="Infrastructure Engineering and Operations", multiple=False, show_default=True)
@click.option('-b', '--board', help="provide sprint board to search - default is current sprint", type=str, required=False, default=None)
@click.option('-j', '--json', help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.option('-a', '--assignee', help="retrieve work items from board and filter by assignee", type=str, required=False)
@click.option('-r', '--reporter', help="retrieve work items from board and filter by reporter", type=str, required=False)
@click.option('-s', '--state', help="retrieve work items from board and filter by state", type=str, required=False)
@click.pass_context
def find(ctx, team, board, json, orderby, ascending, descending, csv, assignee, reporter, state):
    profile = ctx.obj['PROFILE']
    from azdevops.auth import get_default_profile
    CACHED_PROJECTS = {}
    CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
    projects = tuple([(v) for v in CACHED_PROJECTS])
    project = projects[0] if projects else None
    START = time.time()
    ISSUES, TOTAL = search_boards(team, board, project, profile, orderby, ascending, assignee, reporter, state)
    END = time.time()
    RUNTIME = END - START

    if json:
        print(jjson.dumps(ISSUES, indent=2, sort_keys=True))
    elif csv:
        save_query_results(ISSUES, csv)
    else:
        Log.info(f"\n{tabulate(ISSUES, headers='keys', tablefmt='rst')}")

def get_credentials(profile):
    """
    Retrieves credentials for a given profile.
    """
    creds = get_user_creds(profile)
    token = creds[1]
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    credentials = ('', token)
    return headers, credentials

def search_boards(team_name=None, board_name=None, project_name=None, profile=None, orderby=None, ascending=True, assignee=None, reporter=None, state=None):
    DATA = []
    TOTAL = 0

    url = get_url(profile)
    headers, credentials = get_credentials(profile)

    try:
        iterations = get_team_iterations(url, project_name, team_name, headers, credentials)
        
        # Find specific board/sprint by name or default to current sprint
        target_sprint = None
        if board_name:
            target_sprint = next((iteration for iteration in iterations if iteration['name'] == board_name), None)
        if not target_sprint:
            target_sprint = next((iteration for iteration in iterations if is_current_sprint(iteration)), None)
        
        # Print active filters
        active_filters = format_active_filters(assignee, reporter, state)
        print(f"Active Filters: {active_filters}")

        if target_sprint:
            print(f"Target Sprint: {target_sprint['name']}")
            work_item_links = get_work_items_for_iteration(url, headers, credentials, project_name, team_name, target_sprint['id'])
            for link in work_item_links:
                TOTAL += 1
                if 'target' in link and 'url' in link['target']:
                    work_item_url = link['target']['url']
                    work_item_details = get_work_item_details(work_item_url, headers, credentials)
                    if work_item_details:
                        work_data = extract_work_item_data(work_item_details)
                        if is_matching_work_item(work_data, assignee, reporter, state):
                            DATA.append(work_data)
                            TOTAL += 1
        else:
            print("No target sprint found.")
    except Exception as e:
        print(f"Error: {e}")
    return DATA, TOTAL

def list_iterations(team_name, project_name, profile):
    green_start = "\033[42m"  # Green background for highlighting
    red_start = "\033[31m"  # Red text color
    yellow_start = "\033[33m"  # Yellow text color
    color_end = "\033[0m"  # Reset color to default

    url = get_url(profile)
    headers, credentials = get_credentials(profile)

    iterations_data = []
    current_date = datetime.now()
    iterations = get_team_iterations(url, project_name, team_name, headers, credentials)
    if iterations:
        for iteration in iterations:
            start_date = datetime.fromisoformat(iteration['attributes']['startDate'].rstrip('Z'))
            end_date = datetime.fromisoformat(iteration['attributes']['finishDate'].rstrip('Z'))

            if start_date <= current_date <= end_date:
                sprint_status = f"{green_start}Current Sprint{color_end}"
            elif end_date < current_date:
                sprint_status = f"{red_start}Old Sprint{color_end}"
            else:
                sprint_status = f"{yellow_start}Future Sprint{color_end}"

            iteration_info = {
                "Name": iteration['name'],
                "Path": iteration['path'],
                "Status": sprint_status
            }
            iterations_data.append(iteration_info)

        # Tabulate and print the iterations data
        Log.info(f"\n{tabulate(iterations_data, headers='keys', tablefmt='rst')}")
    else:
        print(f"No iterations / sprints found for Team '{team_name}'.")

@boards.command(help="List boards and sprints", context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--team', help="provide team name for board search", type=str, required=False, default="Infrastructure Engineering and Operations", multiple=False, show_default=True)
@click.pass_context
def list(ctx, team):
    profile = ctx.obj['PROFILE']
    from azdevops.auth import get_default_profile
    CACHED_PROJECTS = {}
    CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
    projects = tuple([(v) for v in CACHED_PROJECTS])
    project = projects[0] if projects else None

    if project:
        list_iterations(team, project, profile)
    else:
        print("No project found or specified.")

def format_active_filters(assignee, reporter, state):
    filters = []
    if assignee:
        filters.append(f"Assignee: {assignee}")
    if reporter:
        filters.append(f"Reporter: {reporter}")
    if state:
        filters.append(f"State: {state}")
    return ", ".join(filters) if filters else "No filters applied"

def extract_work_item_data(work_item_details):
    assigned_to = work_item_details['fields'].get('System.AssignedTo', {})
    created_by = work_item_details['fields'].get('System.CreatedBy', {})
    return {
        "Id": work_item_details['id'],
        "Title": trim_string(work_item_details['fields']['System.Title']),
        "State": work_item_details['fields']['System.State'],
        "Assignee": assigned_to.get("displayName", "Unassigned"),
        "Reporter": created_by.get("displayName", "Unknown")
    }

def is_matching_work_item(work_data, assignee, reporter, state):
    if assignee and work_data["Assignee"] != assignee:
        return False
    if reporter and work_data["Reporter"] != reporter:
        return False
    if state and work_data["State"] != state:
        return False
    return True

def get_work_items_for_iteration(url, headers, credentials, project_name, team_name, iteration_id):
    work_items_url = f"{url}/{project_name}/{team_name}/_apis/work/teamsettings/iterations/{iteration_id}/workitems?api-version=6.0"
    response = requests.get(work_items_url, headers=headers, auth=credentials)
    if response.status_code == 200:
        work_item_links = response.json()['workItemRelations']
        return work_item_links
    else:
        print(f"Warning: Failed to retrieve work items for iteration {iteration_id}: {response.status_code}")
        return []

def get_work_item_details(work_item_url, headers, credentials):
    response = requests.get(work_item_url, headers=headers, auth=credentials)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Warning: Failed to retrieve work item details: {response.status_code}")
        return None
 
def get_team_iterations(url, project_name, team_name, headers, credentials):
    iterations_url = f"{url}/{project_name}/{team_name}/_apis/work/teamsettings/iterations?api-version=6.0"
    response = requests.get(iterations_url, headers=headers, auth=credentials)
    if response.status_code == 200:
        return response.json()['value']
    else:
        print(f"Warning: Failed to retrieve iterations for team {team_name}: {response.status_code}")
        return []

def is_current_sprint(iteration):
    current_date = datetime.now()
    start_date = datetime.fromisoformat(iteration['attributes']['startDate'].rstrip('Z'))
    end_date = datetime.fromisoformat(iteration['attributes']['finishDate'].rstrip('Z'))
    return start_date <= current_date <= end_date

def save_query_results(issues, csvfile):
    ROWS = ['ID', 'State', 'Title', 'CreatedDate', 'Assignee', 'CreatedBy']
    with open(csvfile, 'w') as CSV:
        writer = csv.DictWriter(CSV, fieldnames=ROWS)
        writer.writeheader()
        writer.writerows(issues)

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

