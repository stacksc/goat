#!/usr/bin/env python3
import click
from toolbox.logger import Log
from .project import project
from .auth import auth, config
from azdevops.misc import get_default_url, get_default_profile
from .search import search
from .issue import issue
from .boards import boards
from .pipelines import pipeline
from toolbox import misc
from toolbox.misc import debug
from configstore.configstore import Config

CONFIG = Config('azdev')

MESSAGE="AZDEV Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_default_url() + misc.RESET

@click.group('azdev', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'user_profile', help='profile name to use when working with the azdev client', required=False, default=get_default_profile(), show_default=True)
@click.pass_context
def cli(ctx, user_profile):
    ctx.ensure_object(dict)
    if user_profile is not None:
        try:
            ctx.obj['PROFILE'] = user_profile
            PROFILE = CONFIG.get_profile(user_profile)
            ALL = PROFILE['config']
            for ID in ALL:
                AUTH = ID
                if AUTH:
                    ctx.obj['pass'] = AUTH
                    ctx.obj['setup'] = False
                    break
        except:
            ctx.obj['setup'] = True
            pass
    else:
        ctx.obj['setup'] = True
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
