#!/usr/bin/env python3
import click
from toolbox.logger import Log
from .project import project
from .issue import issue
from .auth import auth, config, get_default_url, get_default_profile
from .search import search
from toolbox.click_complete import complete_jira_profiles
from toolbox import misc

MESSAGE="VMware JIRA CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_default_url().lower() + misc.RESET

@click.group('jira', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'profile_name', help='profile name to use when working with the jiraclient', required=False, default=get_default_profile(), shell_complete=complete_jira_profiles, show_default=True)
@click.pass_context
def cli(ctx, debug, profile_name):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile_name
    Log.setup('jiraclient', int(debug))
    pass
    
cli.add_command(issue)
cli.add_command(auth)
cli.add_command(config)
cli.add_command(project)
cli.add_command(search)

if __name__ == "__main__":
    cli(ctx)
