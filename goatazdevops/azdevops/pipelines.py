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
from azdevops.azdevclient import AzDevClient
from azdevops.misc import clear_terminal, generic_menu, setup_runner, setup_az_ctx
from azdevops.auth import get_user_profile_based_on_key

AZDEV = AzDevClient()
CONFIG = Config('azdev')

@click.group(help="manage pipelines", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common actions", is_flag=True)
@click.pass_context
def pipeline(ctx, debug, menu):
    setup_az_ctx(ctx, debug, menu)
    log = Log('azdev.log', debug)
    pass

@pipeline.command(help="List pipelines", context_settings={'help_option_names':['-h','--help']})
@click.argument('projects', nargs=-1, type=str, required=False, shell_complete=lambda ctx, param, incomplete: complete_azdev_projects(ctx, param, incomplete))
@click.option('-r', '--runs',help="output the run information for selected pipeline", is_flag=True, show_default=True, default=False, required=False)
@click.option('-d', '--details',help="output the details for pipeline ID found", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def list_pipelines(ctx, projects, runs, details):
    RUN = setup_runner(ctx, projects)
    if RUN and RUN != {}:
        for profile in RUN:
            project = RUN[profile]
            # we can only select one
            project = ','.join(tuple([(v) for v in project]))
            if project is not None:
                if runs:
                    OUTPUT = get_pipelines(profile, project)
                    selected_pipeline_id = display_menu(OUTPUT)
                    clear_terminal()
                    Log.info(f'Selected Pipeline ID: {selected_pipeline_id} found')
                    if selected_pipeline_id:
                        OUTPUT = get_pipeline_details(profile, selected_pipeline_id, project, runs)
                        if 'value' in OUTPUT and isinstance(OUTPUT['value'], list):
                            extracted_output = []
                            extracted_runs = []
                            for item in OUTPUT['value']:
                                extracted_item = {
                                    "createdDate": item.get("createdDate", ""),
                                    "finishedDate": item.get("finishedDate", ""),
                                    "id": item.get("id", ""),
                                    "name": item.get("name", ""),
                                    "pipeline": {
                                        "folder": item["pipeline"].get("folder", ""),
                                         "id": item["pipeline"].get("id", ""),
                                         "name": item["pipeline"].get("name", ""),
                                         "revision": item["pipeline"].get("revision", ""),
                                         "url": item["pipeline"]["url"] if "pipeline" in item else ""
                                    },
                                    "result": item.get("result", ""),
                                    "state": item.get("state", ""),
                                    "templateParameters": item.get("templateParameters", {}),
                                    "url": item.get("url", "")
                                }
                                extracted_output.append(extracted_item)
        
                            # Sort the extracted output by the "id" field
                            Log.info("Log JSON:")
                            Log.info(jjson.dumps(extracted_output, sort_keys=True, indent=2))
                elif details:
                    OUTPUT = get_pipelines(profile, project)
                    selected_pipeline_id = display_menu(OUTPUT)
                    clear_terminal()
                    Log.info(f'Selected Pipeline ID: {selected_pipeline_id} found')
                    # Output details for the selected pipeline
                    if selected_pipeline_id:
                        OUTPUT = get_pipeline_details(profile, selected_pipeline_id, project, runs)
                        Log.info(jjson.dumps(OUTPUT, sort_keys=True, indent=2))

def get_pipelines(profile, project):
    url = AZDEV.get_url(profile)
    url = f"{url}/{project}/_apis/pipelines"
    headers, credentials = AZDEV.get_credentials(profile)
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
            'dialog.body': 'bg:#242424 fg:#FFFFFF',  # Change fg to a lighter color (white in this case)
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C fg:#FFFFFF',  # Change fg to a lighter color
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        try:
            values=[(sub['id'], f"{sub['name']} (ID: {sub['id']})") for sub in data]
        except:
            values=[(url, url) for url in data]

        selected_id = radiolist_dialog(
            title="Select Pipeline",
            text="Choose a Pipeline:",
            values=values,
            style=style
        ).run()

    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()

    return selected_id

def get_pipeline_details(profile, pipeline_id, project, runs):
    my_url = AZDEV.get_url(profile)
    if runs:
        url = f"{my_url}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=7.2-preview.1"
    else:
        url = f"{my_url}/{project}/_apis/pipelines/{pipeline_id}"

    headers, credentials = AZDEV.get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        pipeline_details = response.json()
        return pipeline_details
    else:
        print(f"Failed to retrieve pipeline details. Status code: {response.status_code}")
        return None

@pipeline.command(help="list builds", context_settings={'help_option_names':['-h','--help']})
@click.argument('project', nargs=-1, type=str, required=False, shell_complete=complete_azdev_projects)
@click.option('-a', '--artifacts',help="output the artifacts for build ID found", is_flag=True, show_default=True, default=False, required=False)
@click.option('-d', '--details',help="output the details for build ID found", is_flag=True, show_default=True, default=True, required=False)
@click.pass_context
def list_builds(ctx, project, artifacts, details):
    RUN = setup_runner(ctx, project)
    if RUN and RUN != {}:
        for profile in RUN:
            project = RUN[profile]
            # we can only select one
            project = ','.join(tuple([(v) for v in project]))
            if project is not None:
                OUTPUT = get_builds_list(profile, project)
                selected_build_id = display_builds_menu(OUTPUT)

                if selected_build_id:
                    build_details = get_build_details(profile, selected_build_id, project, artifacts)
                    clear_terminal()
                    Log.info(jjson.dumps(build_details, sort_keys=True, indent=2))

def get_build_details(profile, build_id, project, artifacts=False):
    url = AZDEV.get_url(profile)
    if artifacts:
        url = f"{url}/{project}/_apis/build/builds//{build_id}/artifacts?api-version=7.2-preview.5"
    else:
        url = f"{url}/{project}/_apis/build/builds/{build_id}"
    headers, credentials = AZDEV.get_credentials(profile)
    response = requests.get(url, headers=headers, auth=credentials)

    if response.status_code == 200:
        build_details = response.json()
        return build_details
    else:
        print(f"Failed to retrieve build details. Status code: {response.status_code}")
        return None

def get_builds(profile, project):
    url = AZDEV.get_url(profile)
    url = f"{url}/{project}/_apis/build/builds"
    headers, credentials = AZDEV.get_credentials(profile)
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
    url = AZDEV.get_url(profile)
    url = f"{url}/{project}/_apis/build/builds"
    headers, credentials = AZDEV.get_credentials(profile)
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
    url = AZDEV.get_url(profile)
    url = f"{url}/{project}/_apis/build/builds"
    headers, credentials = AZDEV.get_credentials(profile)
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
            'dialog.body': 'bg:#242424 fg:#FFFFFF',  # Change fg to a lighter color (white in this case)
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C fg:#FFFFFF',  # Change fg to a lighter color
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
    CONFIG = Config('azdev')
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

if __name__ == '__main__':
    pipeline()
