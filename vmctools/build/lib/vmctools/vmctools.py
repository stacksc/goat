import click, sys, os
from toolbox.logger import Log
from .vmc_sddc import sddc
from .vmc_show import show
from .vmc_account import account
from .vmc_rts import _rts as rts
from csptools.csp_auth import auth, get_latest_profile
from csptools.csp_org import org
from csptools.csp_user import user
from csptools.csp_idp import idp
from toolbox import misc
from configstore.configstore import Config
from toolbox.click_complete import complete_csp_profiles

os.environ['NCURSES_NO_UTF8_ACS'] = "1"
CONFIG = Config('csptools')
MESSAGE="VMware VMC CLI Client" + misc.MOVE + "Current Profile: " + misc.GREEN + misc.UNDERLINE + get_latest_profile().upper() + misc.RESET

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'user_profile', help='user profile for CSP operations', required=False, default=get_latest_profile(), shell_complete=complete_csp_profiles)
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def cli(ctx, debug, user_profile, menu):
    ctx.ensure_object(dict)
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False

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
    Log.setup('vmctools', int(debug))
    ctx = setup_context(ctx)
    pass

def setup_context(ctx):
    CONFIG = Config('csptools')
    PROFILE = CONFIG.get_profile('operator')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj['operator'] = AUTH
        if AUTH:
            break

    PROFLE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj['platform'] = AUTH
        if AUTH:
            break
    return ctx

cli.add_command(sddc)
cli.add_command(show)
cli.add_command(account)
cli.add_command(auth)
cli.add_command(org)
cli.add_command(user)
cli.add_command(idp)
cli.add_command(rts)

if __name__ == "__main__":
    cli(ctx)
