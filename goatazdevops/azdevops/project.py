import click
from .search import run_jql_query
from toolbox.click_complete import complete_azdev_projects
from configstore.configstore import Config
from azdevops.azdevclient import AzDevClient
from toolbox.logger import Log

CONFIG = Config('azdev')
AZDEV = AzDevClient()

@click.group(help='manage AZ DevOps projects', context_settings={'help_option_names':['-h','--help']})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.pass_context
def project(ctx, debug):
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

@project.command('search', help="show a summary of projects matching the specified filter", context_settings={'help_option_names':['-h','--help']})
@click.argument('projects', nargs=-1, type=str, required=False, shell_complete=complete_azdev_projects)
@click.option('-a', '--assignee', help="i.e. jdoe", type=str, required=False, multiple=True)
@click.option('-d', '--details', help="display more details per ticket", is_flag=True, show_default=True, default=False, required=False)
@click.option('-r', '--reporter', help="i.e. smithj", type=str, required=False, multiple=True)
@click.option('--title', help="text to search for in the summary field", type=str, required=False, multiple=True)
@click.option('-s', '--state', help="i.e. active", required=False, type=click.Choice(['active', 'closed', 'new', 'resolved', 'blocked']))
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.option('-J', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def search_projects(ctx, projects, assignee, details, reporter, state, title, orderby, ascending, descending, csv, json):
    if ctx.obj['PROFILE'] is None:
        RUN = {}
        for project in projects:
            PROFILE = AZDEV.get_user_profile_based_on_key(project)
            if PROFILE not in RUN:
                RUN[PROFILE] = {
                    "%s" %(project)
                }
            else:
                RUN[PROFILE].update({ "%s" %(project) })
        for profile in RUN:
            projects = RUN[profile]
            projects = tuple([(v) for v in projects])
            run_jql_query(projects, None, assignee, details, reporter, state, title, csv, json, orderby, ascending, descending, ctx.obj['PROFILE'])
    else:
        if not projects:
            PROFILE = ctx.obj['PROFILE']
            CONFIG = Config('azdev')
            CACHED_PROJECTS = {}
            CACHED_PROJECTS.update(CONFIG.get_metadata('projects', AZDEV.get_default_profile()))
            projects = tuple([(v) for v in CACHED_PROJECTS])
        run_jql_query(projects, None, assignee, details, reporter, state, title, csv, json, orderby, ascending, descending, ctx.obj['PROFILE'])
