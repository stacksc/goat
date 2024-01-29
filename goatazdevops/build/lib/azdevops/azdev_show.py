import sys, os, re, requests
import click, json
import xml.etree.ElementTree as ET
from .azdevclient import AzDevClient
from toolbox.logger import Log
from toolbox.jsontools import filter
from toolbox import misc
from configstore.configstore import Config
from tabulate import tabulate
from toolbox.misc import detect_environment
from azdevops.misc import remove_equals, join_lists_to_strings

AZDEV = AzDevClient()
CONFIG = Config('azdev')

@click.group(help="retrieve information from Azure DevOps",context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def show(ctx, debug):
    user_profile = ctx.obj['PROFILE']
    url = None  # Initialize url as None
    if ctx.obj['setup'] == True:
        if user_profile is None:
            user_profile = 'default'
        # Fetch the URL based on the profile
        url = AZDEV.get_url(user_profile)
        AZDEV.get_session(url, user_profile, force=True)
    log = Log('azdev.log', debug)
    pass

@show.command('access-token', help='API token for accessing the Jenins functionality', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token(ctx):
    RESULT = AZDEV.get_access_token(user_profile=ctx.obj['PROFILE'])
    Log.info(f"Access token:\n{RESULT}")
    return RESULT

@show.command('access-token-age', help='how long the current access token will remain active', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_access_token_age(ctx):
    RESULT = AZDEV.get_access_token_age(user_profile=ctx.obj['PROFILE'])
    RESULT = round(RESULT / 60.0, 2) # convert to minutes 
    Log.info(f"Access token has been created {RESULT} minutes ago")
    return RESULT

@show.command('health', help='retrieve health status for services and regions', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def show_health(ctx):
    service_data_list = []
    health_api_url = "https://status.dev.azure.com/_apis/status/health?api-version=7.2-preview.1"
    response = requests.get(health_api_url)
    green_start = "\033[32m"  # green
    red_start = "\033[31m"  # Red text color
    yellow_start = "\033[33m"  # Yellow text color
    color_end = "\033[0m"  # Reset color to default

    if response.status_code == 200:
        health_data = response.json()
        # You can access the status information from the 'health_data' JSON response
        print("Status:", health_data["status"]["health"])
        print("Message:", health_data["status"]["message"])
        # Extract geographies and their statuses from the JSON
        services = health_data.get("services", [])
        for service in services:
            service_id = service.get("id")
            geographies = service.get("geographies", [])
            for geography in geographies:
                geography_name = geography.get("name")
                geography_status = geography.get("health")
                if 'healthy' not in geography_status:
                    geography_status = f"{red_start}{geography_status}{color_end}"
                else:
                    geography_status = f"{green_start}{geography_status}{color_end}"

                # Create a dictionary for the current service and geography
                service_dict = {
                    "Service": service_id,
                    "Geography": geography_name,
                    "Health": geography_status
                }

                # Append the dictionary to the list
                service_data_list.append(service_dict)
    else:
        print(f"Failed to retrieve status information. Status code: {response.status_code}")
    Log.info(f"\n{tabulate(service_data_list, headers='keys', tablefmt='fancy_grid')}")

@show.command('config', help="retrieve the entire content of azdev's configstore instance", context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def display_config(ctx):
    AZDEV.display_azdev_config(ctx.obj['PROFILE'])
