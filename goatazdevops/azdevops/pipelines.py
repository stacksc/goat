import os, csv, time, click, re, threading
from typing import List, Tuple, Optional
from datetime import datetime
from toolbox.click_complete import complete_azdev_projects
import json as jjson
import requests
from configstore.configstore import Config
from prompt_toolkit.styles import Style
from toolbox.logger import Log
from prompt_toolkit.shortcuts import radiolist_dialog
from .auth import get_session, get_url, get_session_based_on_key, get_user_profile_based_on_key, get_user_creds

CONFIG = Config('azdev')

@click.group(help="manage pipelines", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def pipeline(ctx):
    pass

@pipeline.command(help="List pipelines", context_settings={'help_option_names':['-h','--help']})
@click.argument('project', nargs=-1, type=str, required=False, shell_complete=complete_azdev_projects)
@click.pass_context
def list_pipelines(ctx, project):
    profile = ctx.obj['PROFILE']
    if not project:
        from azdevops.auth import get_default_profile
        CACHED_PROJECTS = {}
        CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
        projects = tuple([(v) for v in CACHED_PROJECTS])
        project = projects[0] if projects else None
    OUTPUT = get_pipelines(profile, project)

    selected_id = display_menu(OUTPUT)
    clear_terminal()
    Log.info(f'selected ID: {selected_id} found')
    if selected_id:
        OUTPUT = get_pipeline_details(profile, selected_id, project)
        Log.info(jjson.dumps(OUTPUT, sort_keys=True, indent=2))
    else:
        return None

# Function to clear the terminal screen
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the visible content
    print("\033c", end='')  # Clear the terminal history (scroll-back buffer)

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

def get_pipelines(profile, project):
    url = get_url(profile)
    url = f"{url}/{project}/_apis/pipelines"
    headers, credentials = get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        pipelines_data = response.json()
        pipelines_list = []
        # Process pipelines_data to extract and store the pipelines
        pipelines = pipelines_data.get('value', [])
        for pipeline in pipelines:
            pipeline_id = pipeline.get('id')
            pipeline_name = pipeline.get('name')
            # Create a dictionary for the pipeline and add it to the list
            pipeline_info = {'id': pipeline_id, 'name': pipeline_name}
            pipelines_list.append(pipeline_info)
        # Now you have a list of dictionaries with pipeline information
        pipelines_list = sorted(pipelines_list, key=lambda x: x['name'])
        return pipelines_list
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def display_menu(data):
    selected_id = None
    def run_dialog():
        nonlocal selected_id
        style = Style.from_dict({
            'dialog': 'bg:#4B4B4B',
            'dialog.body': 'bg:#242424',
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C',
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        selected_id = radiolist_dialog(
            title="Select Pipeline",
            text="Choose a Pipeline:",
            values=[(sub['id'], f"{sub['name']} (ID: {sub['id']})") for sub in data],
            style=style
        ).run()

    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()

    return selected_id

def get_pipeline_details(profile, pipeline_id, project):
    my_url = get_url(profile)
    url = f"{my_url}/{project}/_apis/pipelines/{pipeline_id}"

    headers, credentials = get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        pipeline_details = response.json()
        return pipeline_details
    else:
        print(f"Failed to retrieve pipeline details. Status code: {response.status_code}")
        return None

@pipeline.command(help="list builds", context_settings={'help_option_names':['-h','--help']})
@click.argument('project', nargs=-1, type=str, required=False, shell_complete=complete_azdev_projects)
@click.pass_context
def list_builds(ctx, project):
    profile = ctx.obj['PROFILE']
    if not project:
        from azdevops.auth import get_default_profile
        CACHED_PROJECTS = {}
        CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
        projects = tuple([(v) for v in CACHED_PROJECTS])
        project = projects[0] if projects else None
    OUTPUT = get_builds_list(profile, project)

    selected_build_id = display_builds_menu(OUTPUT)

    if selected_build_id:
        build_details = get_build_details(profile, selected_build_id, project)
        clear_terminal()
        Log.info(jjson.dumps(build_details, sort_keys=True, indent=2))

def get_build_details(profile, build_id, project):
    url = get_url(profile)
    url = f"{url}/{project}/_apis/build/builds/{build_id}"
    headers, credentials = get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        build_details = response.json()
        return build_details
    else:
        print(f"Failed to retrieve build details. Status code: {response.status_code}")
        return None

def get_builds(profile, project):
    url = get_url(profile)
    url = f"{url}/{project}/_apis/build/builds"
    headers, credentials = get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)
    if response.status_code == 200:
        builds_data = response.json().get('value', [])
        if builds_data:
            sorted_builds = sorted(builds_data, key=lambda x: x['lastChangedDate'], reverse=True)
            most_recent_build = sorted_builds[0]
        return most_recent_build
    else:
        print(f"Failed to retrieve builds. Status code: {response.status_code}")
        return []

def get_builds_list_active(profile, project):
    url = get_url(profile)
    url = f"{url}/{project}/_apis/build/builds"
    headers, credentials = get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        builds_data = response.json().get('value', [])
        builds_list = [build for build in builds_data if build['status'] in ['inProgress', 'active']]
        builds_list = sorted(builds_list, key=lambda x: x[1])  # Sort by build name
        return builds_list
    else:
        print(f"Failed to retrieve builds. Status code: {response.status_code}")
        return []

def get_builds_list(profile, project):
    url = get_url(profile)
    url = f"{url}/{project}/_apis/build/builds"
    headers, credentials = get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        builds_data = response.json().get('value', [])
        builds_list = [build for build in builds_data]
        return builds_list
    else:
        print(f"Failed to retrieve builds. Status code: {response.status_code}")
        return []

def display_builds_menu(builds_list):
    selected_build_id = None

    def run_dialog():
        nonlocal selected_build_id
        style = Style.from_dict({
            'dialog': 'bg:#4B4B4B',
            'dialog.body': 'bg:#242424',
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C',
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        selected_build_id = radiolist_dialog(
            title="Select Build",
            text="Choose a build:",
            values=[(str(build['id']), build['definition']['name']) for build in builds_list],
            style=style
        ).run()

    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()

    return selected_build_id

@pipeline.command(help="Stop a running build", context_settings={'help_option_names':['-h','--help']})
@click.argument('project', nargs=-1, type=str, required=False, shell_complete=complete_azdev_projects)
@click.pass_context
def stop_build(ctx, project):
    profile = ctx.obj['PROFILE']
    if not project:
        from azdevops.auth import get_default_profile
        CACHED_PROJECTS = {}
        CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
        projects = tuple([(v) for v in CACHED_PROJECTS])
        project = projects[0] if projects else None
    builds_list = get_builds_list_active(profile, project)
    if not builds_list:
        print("No builds found.")
        return

    selected_build_id = display_builds_menu(builds_list)
    print(selected_build_id)

if __name__ == '__main__':
    pipeline()
