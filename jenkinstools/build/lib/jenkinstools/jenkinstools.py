#!/usr/bin/env python3
import os, click
from toolbox.logger import Log
from .jenkins_auth import auth, get_latest_profile
from .jenkins_show import show
from toolbox import misc
from configstore.configstore import Config
from toolbox.click_complete import complete_jenkins_profiles
from toolbox import misc

os.environ['NCURSES_NO_UTF8_ACS'] = "1"
CONFIG = Config('jenkinstools')
MESSAGE="Jenkins Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'user_profile', help='user profile for Jenkins operations', required=False, default=get_latest_profile(), shell_complete=complete_jenkins_profiles)
@click.pass_context
def cli(ctx, debug, user_profile):
    ctx.ensure_object(dict)
    if user_profile is not None:
        try:
            ctx.obj['profile'] = user_profile
            PROFILE = CONFIG.get_profile(user_profile)
            ALL = PROFILE['config']
            for ID in ALL:
                AUTH = ID
                if AUTH:
                    ctx.obj['token'] = AUTH
                    ctx.obj['setup'] = False
                    break
        except:
            ctx.obj['setup'] = True
            pass
    else:
        ctx.obj['setup'] = True
    Log.setup('jenkinstools', int(debug))
    pass
    
cli.add_command(auth)
cli.add_command(show)

if __name__ == "__main__":
    cli(ctx)
