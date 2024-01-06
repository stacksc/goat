import click
from .search import run_jql_query
from .auth import get_user_profile_based_on_key
from toolbox.click_complete import complete_projects, complete_jira_profiles

@click.group(help='manage JIRA projects', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def project(ctx):
    pass

@project.command('search', help="show a summary of projects matching the specified filter", context_settings={'help_option_names':['-h','--help']})
@click.argument('projects', nargs=-1, type=str, required=True, shell_complete=complete_projects)
@click.option('-a', '--assignee', help="i.e. jdoe", type=str, required=False, multiple=True)
@click.option('-g', '--group', help="i.e. devops", type=str, required=False, multiple=True)
@click.option('-r', '--reporter', help="i.e. smithj", type=str, required=False, multiple=True)
@click.option('-s', '--status', help="i.e. closed", type=str, required=False, multiple=True)
@click.option('--summary', help="text to search for in the summary field", type=str, required=False, multiple=True)
@click.option('--description', help="text to search for in the description field", type=str, required=False, multiple=True)
@click.option('-l', '--limit', help="max amount of issues to show", type=int, required=False, default=50)
@click.option('-o', '--orderby', help="choose which field to use for sorting", show_default=True, required=False)
@click.option('-A', '--ascending', help="show issues in ascending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-D', '--descending', help="show issues in descending order", is_flag=True, show_default=True, default=False, required=False)
@click.option('-c', '--csv', help="name of the csv file to save the results to", type=str, required=False)
@click.option('-J', '--json',help="output results in JSON format", is_flag=True, show_default=True, default=False, required=False)
@click.option('-w', '--wizard',help="output results in wizard format for transitioning", is_flag=True, show_default=True, default=False, required=False)
@click.option('-t', '--tui',help="use the native TUI to launch tickets in the browser", is_flag=True, show_default=True, default=False, required=False)
@click.pass_context
def search_projects(ctx, projects, assignee, group, reporter, status, summary, description, limit, csv, json, wizard, tui, orderby, ascending, descending):
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
            run_jql_query(projects, None, assignee, group, reporter, status, summary, description, None, limit, csv, json, wizard, tui, orderby, ascending, descending, ctx.obj['PROFILE'])
    else:
        run_jql_query(projects, None, assignee, group, reporter, status, summary, description, None, limit, csv, json, wizard, tui, orderby, ascending, descending, ctx.obj['PROFILE'])
