#!/usr/bin/env python3

import os, click
from toolbox.logger import Log
from .csp_auth import auth, get_latest_profile
from .csp_org import org
from .csp_user import user
from .csp_show import show
from .csp_oauth import oauth
from toolbox import misc
from configstore.configstore import Config
from toolbox.click_complete import complete_csp_profiles

os.environ['NCURSES_NO_UTF8_ACS'] = "1"
CONFIG = Config('csptools')
MESSAGE="VMware CSP CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'user_profile', help='user profile for CSP operations', required=False, default=get_latest_profile(), shell_complete=complete_csp_profiles)
@click.pass_context
def cli(ctx, debug, user_profile):
    ctx.ensure_object(dict)
    if user_profile is not None:
        try:
            ctx.obj['profile'] = user_profile
            PROFILE = CONFIG.get_profile(user_profile)
            ALL_ORGS = PROFILE['config']
            for ORG_ID in ALL_ORGS:
                AUTH = ORG_ID
                if AUTH:
                    ctx.obj['auth'] = AUTH
                    break
        except:
            pass
        Log.setup('csptools', int(debug))
    pass
    
cli.add_command(auth)
cli.add_command(oauth)
cli.add_command(org)
cli.add_command(user)
cli.add_command(show)

if __name__ == "__main__":
    cli(ctx)
