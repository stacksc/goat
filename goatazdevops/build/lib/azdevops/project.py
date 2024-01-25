import click
from .search import run_jql_query
from .auth import get_user_profile_based_on_key
from toolbox.click_complete import complete_azdev_projects
from configstore.configstore import Config

@click.group(help='manage AZ DevOps projects', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def project(ctx):
    pass

@project.command('search', help="show a summary of projects matching the specified filter", context_settings={'help_option_names':['-h','--help']})
@click.argument('projects', nargs=-1, type=str, required=False, shell_complete=complete_azdev_projects)
@click.option('-a', '--assignee', help="i.e. jdoe", type=str, required=False, multiple=True)
@click.option('-r', '--reporter', help="i.e. smithj", type=str, required=False, multiple=True)
@click.option('-s', '--state', help="i.e. closed", type=str, required=False, multiple=True)
@click.option('--title', help="text to search for in the summary field", type=str, required=False, multiple=True)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.option('-J', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def search_projects(ctx, projects, assignee, reporter, state, title, orderby, ascending, descending, csv, json):
    if ctx.obj['PROFILE'] is None:
        RUN = {}
        for project in projects:
            PROFILE = get_user_profile_based_on_key(project)
            if PROFILE not in RUN:
                RUN[PROFILE] = {
                    "%s" %(project)
                }
            else:
                RUN[PROFILE].update({ "%s" %(project) })
        for profile in RUN:
            projects = RUN[profile]
            projects = tuple([(v) for v in projects])
            run_jql_query(projects, None, assignee, reporter, state, title, csv, json, orderby, ascending, descending, ctx.obj['PROFILE'])
    else:
        if not projects:
            PROFILE = ctx.obj['PROFILE']
            from azdevops.auth import get_default_profile
            CONFIG = Config('azdev')
            CACHED_PROJECTS = {}
            CACHED_PROJECTS.update(CONFIG.get_metadata('projects', get_default_profile()))
            projects = tuple([(v) for v in CACHED_PROJECTS])
        run_jql_query(projects, None, assignee, reporter, state, title, csv, json, orderby, ascending, descending, ctx.obj['PROFILE'])
