import os, csv, time, click, re, threading
from typing import List, Tuple, Optional
from datetime import datetime
import json as jjson
from tabulate import tabulate
from toolbox.logger import Log
import requests
from configstore.configstore import Config
from azdevops.azdevclient import AzDevClient
from azdevops.auth import get_user_profile_based_on_key
from azdevops.misc import remove_equals, clear_terminal, join_lists_to_strings, display_menu, generic_menu, setup_runner, setup_az_ctx
from azdevops.search import run_jql_query
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import radiolist_dialog

CONFIG = Config('azdev')
AZDEV = AzDevClient()

@click.group(help="manage boards and sprints", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common actions", is_flag=True)
@click.pass_context
def sprints(ctx, debug, menu):
    setup_az_ctx(ctx, debug, menu)
    log = Log('azdev.log', debug)
    pass

@sprints.command(help="search boards and sprints", context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--team', help="provide team name for board search", type=str, required=False, default=["Infrastructure Engineering and Operations"], show_default=True, multiple=True, callback=remove_equals)
@click.option('-s', '--sprint', help="provide sprint path to search", type=str, required=False, default=None, callback=remove_equals)
@click.option('-j', '--json', help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-o', '--orderby', help="choose which field to use for sorting", required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False, multiple=True, callback=remove_equals)
@click.option('-t', '--title', help="text to search for in the title field", multiple=True, callback=remove_equals)
@click.option('-a', '--assignee', help="retrieve work items from board and filter by assignee", type=str, multiple=True, required=False, callback=remove_equals)
@click.option('-r', '--reporter', help="retrieve work items from board and filter by reporter", type=str, multiple=True, required=False, callback=remove_equals)
@click.option('-s', '--state', help="retrieve work items from board and filter by state", type=str, multiple=True, required=False, callback=remove_equals)
@click.option('-d', '--details', help="display more details per ticket", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def search(ctx, team, sprint, json, orderby, ascending, descending, csv, title, assignee, reporter, state, details):
    projects = None
    RUN = setup_runner(ctx, projects)

    if not RUN:
        Log.warn('No runnable projects found.')
        exit()

    project, user_profile = get_first_project(RUN)
    
    if not project:
        Log.warn('No projects available.')
        exit()

    if not sprint:
        sprint = select_sprint(ctx, project, user_profile)
        if not sprint:
            Log.warn('Please provide a sprint name to search against')
            exit()

    run_jql_query(ctx, projects, None, assignee, details, reporter, state, title, csv, json, orderby, ascending, descending, user_profile, sprint)

def get_first_project(RUN):
    for profile, projects in RUN.items():
        if projects:
            # Since projects is a set, use next(iter(projects)) to get an element
            project = next(iter(projects), None)
            return project, profile
    return None, None

def select_sprint(ctx, project, profile):
    teams = find_team_per_project(ctx, project, profile)
    if not teams:
        return None

    team = choose_option(teams, 'team name')
    try:
        sprints = list_iterations(team, project, profile, display=False)
        sprints = sorted(sprints, key=get_sort_key, reverse=True)
    except:
        Log.warn('unable to run query to list sprints')
        exit()

    if sprints:
        return choose_option(sprints, 'sprint name')
    return None

def get_sprint_number(iteration_path):
    try:
        # Split the string and convert the last part to an integer
        return int(iteration_path.split('Sprint ')[-1])
    except ValueError:
        # In case the sprint number isn't an integer or not present
        return float('inf')  # Sorts non-numeric sprints last

def get_sort_key(iteration_path):
    # Convert the string to lowercase to handle inconsistent capitalization
    parts = iteration_path.lower().split('\\')[-1].split(' - ')  # Split the last part of the path
   
    try:
        year = int(parts[0])  # Extract the year
        # Extract the sprint number, convert to integer for numerical sorting
        sprint_number = int(parts[-1].split('sprint')[-1].strip())
        return (year, sprint_number)
    except ValueError:
        # In case of non-integer values
        return (float('inf'), float('inf'))  # Sorts these items last


def choose_option(options, option_type):
    sorted_options = sorted(options)
    try:
        return generic_menu(sorted_options)[0]
    except IndexError:
        Log.warn(f'Please provide a {option_type} to search against')
        return None

def get_credentials(profile):
    """
    Retrieves credentials for a given profile.
    """
    creds = AZDEV.get_user_creds(profile)
    token = creds[1]
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    credentials = ('', token)
    return headers, credentials

def list_iterations(team_name, project_name, profile, display=False):
    green_start = "\033[42m"  # Green background for highlighting
    red_start = "\033[31m"  # Red text color
    yellow_start = "\033[33m"  # Yellow text color
    color_end = "\033[0m"  # Reset color to default

    url = AZDEV.get_url(profile)
    headers, credentials = get_credentials(profile)

    menu_data = []
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
            menu_data.append(iteration['path'])
            iterations_data.append(iteration_info)

        # Tabulate and print the iterations data
        if display is True:
            Log.info(f"\n{tabulate(iterations_data, headers='keys', tablefmt='rst')}")
        return menu_data
    else:
        print(f"No iterations / sprints found for Team '{team_name}'.")

@sprints.command(help="List boards and sprints", context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--team', help="provide team name for board search", type=str, required=False, default=["Infrastructure Engineering and Operations"], multiple=True, show_default=True, callback=remove_equals)
@click.pass_context
def list(ctx, team):
    CONFIG = Config('azdev')
    profile = ctx.obj['PROFILE']
    CACHED_PROJECTS = {}
    cached_projects_data = CONFIG.get_metadata('projects', profile)
    # Check if cached_projects_data is not None before updating CACHED_PROJECTS
    if cached_projects_data:
        CACHED_PROJECTS.update(cached_projects_data)
    projects = tuple([(v) for v in CACHED_PROJECTS])
    project = projects[0] if projects else None
    if team:
        team = ','.join(team)

    if project:
        list_iterations(team, project, profile, display=True)
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

def get_team_iterations(url, project_name, team_name, headers, credentials):
    iterations_url = f"{url}/{project_name}/{team_name}/_apis/work/teamsettings/iterations?api-version=6.0"
    response = requests.get(iterations_url, headers=headers, auth=credentials)
    if response.status_code == 200:
        return response.json()['value']
    else:
        print(f"Warning: Failed to retrieve iterations for team {team_name}: {response.status_code}")
        return []

def find_team_per_project(ctx, project, profile):
    # Construct the work item URL based on work_item_id
    all_teams = []
    url = AZDEV.get_url(profile)
    creds = AZDEV.get_user_creds(profile)
    token = creds[1]
    url = f"{url}/_apis/projects/{project}/teams?api-version=7.2-preview.3"

    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    auth = ('', token)
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        teams = response.json()["value"]
        for team in teams:
            all_teams.append(team['name'])
    else:
        print(f"Warning: Failed to retrieve work item details: {response.status_code}")
        return None
    return all_teams
