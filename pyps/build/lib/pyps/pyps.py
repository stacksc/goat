#!/usr/bin/env python3

import click, os, sys, gnureadline
from toolbox.logger import Log
from jiratools.jiraclient import cli as jira
from configstore.configstore_ctrl import cli as configs
from awstools.awstools import CLI as aws
from jenkinstools.jenkinstools import cli as jenkins
from jctools.tools import cli as jc
from toolbox.misc import set_terminal_width, get_aliases, detect_environment, easy_setup, search_man_pages

if os.getenv('USER') == 'root':
    print('...unable to run pyps as root! Exiting')
    exit(1)

@click.group(help="pyps - PYthon tools by PSsre team - pronounced as 'pipes'", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-v', '--version', help="print version of pyps and all its submodules", default=False, is_flag=True)
@click.option('-a', '--aliases', help="print all defined aliases and shortcuts", default=False, is_flag=True)
@click.option('-m', '--manuals', help="print all defined manuals matching pattern(s)", type=str, multiple=True, required=False)
@click.option('-s', '--setup', help="setup client(s) for pyps interaction", default=False, is_flag=True)
@click.pass_context
def cli(ctx, debug, version, aliases, manuals, setup):
    ctx.ensure_object(dict)
    if version:
        from importlib_metadata import version
        pyps_version()
        sys.exit(0)
    if aliases:
        from tabulate import tabulate
        ALIASES = get_aliases()
        Log.info(f"\n{tabulate(ALIASES, headers='keys', tablefmt='fancy_grid')}")
        sys.exit(0)
    if manuals:
        name = search_man_pages(manuals)
        os.system(f"man {name}")
        sys.exit(0)
    if setup:
        from .cmd_preset import init
        RESULT = init()
        easy_setup()
        sys.exit(0)
    Log.setup('pyps', int(debug))
    pass

def pyps_version():
    print('PYPS:\t\t\t' + version('pyps'))
    print('- awstools:\t\t' + version('awstools'))
    print('- configstore:\t\t' + version('configstore'))
    print('- csptools:\t\t' + version('csptools'))
    print('- jiratools:\t\t' + version('jiratools'))
    print('- slacktools:\t\t' + version('slacktools'))
    print('- toolbox:\t\t' + version('toolbox'))
    print('- vmctools:\t\t' + version('vmctools'))
    print('- idptools:\t\t' + version('idptools'))
    print('- nexustools:\t\t' + version('nexustools'))
    print('- jfrogtools:\t\t' + version('jfrogtools'))
    print('- flytools:\t\t' + version('flytools'))
    print('- jenkinstools:\t\t' + version('jenkinstools'))
    print('- confluence:\t\t' + version('contools'))
    sys.exit(0)

cli.add_command(configs, name='configs')
cli.add_command(jira, name='jira')
cli.add_command(aws, name='aws')
cli.add_command(jc, name='jc')
cli.add_command(jenkins, name='jenkins')

if detect_environment() == 'non-gc':
    # non-prod specific mods
    from .cmd_report import report
    from contools.tools import cli as confluence
    from jfrogtools.tools import cli as jfrog
    from .cmd_slack import slack
    from flytools.tools import cli as fly
    from gitools.tools import cli as git
    from .cmd_security import security
    cli.add_command(slack)
    cli.add_command(report)
    cli.add_command(jfrog, name='jfrog')
    cli.add_command(fly, name='fly')
    cli.add_command(git, name='git')
    cli.add_command(confluence, name='confluence')
    cli.add_command(security, name='security')
else:
    # production specific mods
    from csptools.csptools import cli as csp
    from idptools.idptools import cli as idp
    from vmctools.vmctools import cli as vmc
    from nexustools.nexustools import cli as nexus
    from .cmd_secrets import secrets
    cli.add_command(vmc, name='vmc')
    cli.add_command(csp, name='csp')
    cli.add_command(idp, name='idp')
    cli.add_command(nexus, name='nexus')
    cli.add_command(secrets, name='secrets')

if __name__ == "__main__":
    cli()
