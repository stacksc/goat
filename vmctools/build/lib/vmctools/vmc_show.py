import click
from .vmc_sddc import sddc_show
from .vmc_account import account_show
from csptools.csp_show import user as csp_user_show
from csptools.csp_show import org as csp_org_show
from csptools.csp_show import csp_config
from csptools.csp_show import csp_features
from csptools.csp_show import csp_properties
from csptools.csp_show import vmc_roles
from csptools.csp_idp import idp_show as csp_idp_show

@click.group('show', help='show data about VMC')
def show():
    pass

show.add_command(sddc_show, name='sddc')
show.add_command(account_show, name='account')
show.add_command(csp_user_show, name='user')
show.add_command(csp_org_show, name='org')
show.add_command(csp_config, name='config')
show.add_command(csp_features, name='features')
show.add_command(vmc_roles, name='roles')
show.add_command(csp_properties, name='properties')
show.add_command(csp_idp_show, name='idp')
