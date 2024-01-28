import os, click, re, json
from .search import run_jql_query
from toolbox.logger import Log
from toolbox.misc import detect_environment, remove_html_tags
from azdevops.azdevclient import AzDevClient
from toolbox.logger import Log

AZDEV = AzDevClient()

user_env_var = "USERNAME" if os.name == 'nt' else "LOGNAME"
default_assignee = os.environ.get(user_env_var, None)

@click.group(help="manage Azure DevOps worklist items", context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def issue(ctx, debug):
    user_profile = ctx.obj['PROFILE']
    url = None  # Initialize url as None
    if ctx.obj['setup'] == True:
        if user_profile is None:
            user_profile = 'default'
        # Fetch the URL based on the profile
        url = AZDEV.get_url(user_profile)
        AZDEV.get_session(url, user_profile)
    log = Log('azdev.log', debug)
    pass

@issue.command('search', help="show a summary of specified issue or issues", context_settings={'help_option_names':['-h','--help']})
@click.argument('keys', nargs=-1, type=str, required=True)
@click.option('-j', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.option('-d', '--details', help="display more details per ticket", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def search_issues(ctx, keys, json, orderby, ascending, descending, csv, details):
    profile = ctx.obj['PROFILE']
    run_jql_query(None, keys, None, details, None, None, None, csv, json, orderby, ascending, descending, profile)

