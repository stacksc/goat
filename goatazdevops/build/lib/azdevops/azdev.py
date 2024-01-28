#!/usr/bin/env python3
import click
from toolbox.logger import Log
from .project import project
from .auth import auth, config, get_default_url, get_default_profile
from .search import search
from .issue import issue
from .boards import boards
from .pipelines import pipeline
from toolbox import misc
from toolbox.misc import debug

MESSAGE="AZDEV Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_default_url().upper() + misc.RESET

@click.group('azdev', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'profile_name', help='profile name to use when working with the azdev client', required=False, default=get_default_profile(), show_default=True)
@click.pass_context
def cli(ctx, profile_name):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = profile_name
    Log.setup('azdev', int(debug))
    pass
    
cli.add_command(auth)
cli.add_command(boards)
cli.add_command(config)
cli.add_command(issue)
cli.add_command(pipeline)
cli.add_command(project)

if __name__ == "__main__":
    cli(ctx)
