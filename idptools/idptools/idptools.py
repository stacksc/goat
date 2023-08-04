#!/usr/bin/env python3

import os, click
from toolbox.logger import Log
from .idp_auth import auth, get_latest_profile
from .idp_show import show
from .idp_users import users
from .idp_tenant import tenants
from toolbox import misc
from configstore.configstore import Config
from toolbox.click_complete import complete_idp_profiles

os.environ['NCURSES_NO_UTF8_ACS'] = "1"
CONFIG = Config('idptools')
MESSAGE="VMware IDP CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'user_profile', help='user profile for IDP/vIDP operations', required=False, default=get_latest_profile(), shell_complete=complete_idp_profiles)
@click.pass_context
def cli(ctx, debug, user_profile):
    ctx.ensure_object(dict)
    if user_profile is not None or user_profile == 'default':
        ctx.obj['profile'] = user_profile
        PROFILE = CONFIG.get_profile(user_profile)
        try:
            ALL_ORGS = PROFILE['config']
            for ORG_ID in ALL_ORGS:
                AUTH = ORG_ID
                if AUTH:
                   ctx.obj['auth'] = AUTH
                   break
            ctx.obj['url'] = PROFILE['config'][AUTH]['url']
            Log.setup('idptools', int(debug))
            ctx.obj['setup'] = False
        except:
            ctx.obj['setup'] = True
    pass
    
cli.add_command(auth)
cli.add_command(show)
cli.add_command(tenants)
cli.add_command(users)

if __name__ == "__main__":
    cli(ctx)
