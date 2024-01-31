#!/usr/bin/env python3
import click
from toolbox.logger import Log
from .project import project
from azdevops.auth import auth
from azdevops.azdev_show import show
from azdevops.misc import get_default_url, get_default_profile
from azdevops.search import search
from azdevops.issue import issue
from azdevops.sprints import sprints
from azdevops.pipelines import pipeline
from toolbox import misc
from toolbox.misc import debug
from toolbox.click_complete import complete_azdev_profiles
from configstore.configstore import Config

CONFIG = Config('azdev')

MESSAGE="AZDEV Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_default_url() + misc.RESET

@click.group('azdev', help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-p', '--profile', 'user_profile', help='profile name to use when working with the azdev client', required=False, default=None, shell_complete=complete_azdev_profiles, show_default=True)
@click.pass_context
def cli(ctx, user_profile):
    ctx.ensure_object(dict)
    ctx.obj['PROFILE'] = user_profile
    if user_profile is not None:
        try:
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
        try:
            user_profile = ctx.obj['PROFILE'] = get_default_profile()
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
    Log.setup('azdev', int(debug))
    pass

cli.add_command(auth)
cli.add_command(issue)
cli.add_command(pipeline)
cli.add_command(project)
cli.add_command(show)
cli.add_command(sprints)

if __name__ == "__main__":
    cli(ctx)
