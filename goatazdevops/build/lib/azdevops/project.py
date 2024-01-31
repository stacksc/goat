import click, threading
from typing import List, Tuple, Optional
from .search import run_jql_query
from toolbox.click_complete import complete_azdev_projects
from configstore.configstore import Config, ExitSignal
from azdevops.azdevclient import AzDevClient
from azdevops.misc import remove_equals, generic_menu
from azdevops.auth import get_user_profile_based_on_key
from toolbox.logger import Log
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import radiolist_dialog
from azdevops.misc import clear_terminal, setup_runner, setup_az_ctx

CONFIG = Config('azdev')
AZDEV = AzDevClient()

@click.group(help='manage AZ DevOps projects', context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common actions", is_flag=True)
@click.pass_context
def project(ctx, debug, menu):
    setup_az_ctx(ctx, debug, menu)
    log = Log('azdev.log', debug)
    pass

@project.command('search', help="show a summary of projects matching the specified filter", context_settings={'help_option_names':['-h','--help']})
@click.argument('projects', nargs=-1, type=str, required=False, shell_complete=lambda ctx, param, incomplete: complete_azdev_projects(ctx, param, incomplete))
@click.option('-a', '--assignee', help="i.e. jdoe", type=str, required=False, multiple=True, callback=remove_equals)
@click.option('-d', '--details', help="display more details per ticket", is_flag=True, show_default=True, default=False, required=False)
@click.option('-r', '--reporter', help="i.e. smithj", type=str, required=False, multiple=True, callback=remove_equals)
@click.option('--title', help="text to search for in the summary field", type=str, required=False, multiple=True, callback=remove_equals)
@click.option('-s', '--state', help="i.e. active", required=False, type=str, multiple=True, callback=remove_equals)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False, callback=remove_equals)
@click.option('-J', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def search_projects(ctx, projects, assignee, details, reporter, state, title, orderby, ascending, descending, csv, json):
    RUN = setup_runner(ctx, projects)
    if RUN and RUN != {}:
        for profile in RUN:
            projects = RUN[profile]
            projects = tuple([(v) for v in projects])
            if projects is not None and profile is not None:
                run_jql_query(ctx, projects, None, assignee, details, reporter, state, title, csv, json, orderby, ascending, descending, profile)

def display_menu(data):
    selected_project = None
    def run_dialog():
        nonlocal selected_project
        style = Style.from_dict({
            'dialog': 'bg:#4B4B4B',
            'dialog.body': 'bg:#242424 fg:#FFFFFF',  # Change fg to a lighter color (white in this case)
            'dialog.title': 'bg:#00aa00',
            'radiolist': 'bg:#1C1C1C fg:#FFFFFF',  # Change fg to a lighter color
            'button': 'bg:#528B8B',
            'button.focused': 'bg:#00aa00',
        })

        values=[(project, project) for project in data]

        selected_project = radiolist_dialog(
            title="Select Project",
            text="Choose a Project:",
            values=values,
            style=style
        ).run()

    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()

    return selected_project
