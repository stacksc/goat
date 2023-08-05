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
    print('...unable to run goat as root! Exiting')
    exit(1)

@click.group(help="goat => GCP, OCI, & AWS tools : GOAT Team", context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-v', '--version', help="print version of goat and all its submodules", default=False, is_flag=True)
@click.option('-a', '--aliases', help="print all defined aliases and shortcuts", default=False, is_flag=True)
@click.option('-m', '--manuals', help="print all defined manuals matching pattern(s)", type=str, multiple=True, required=False)
@click.option('-s', '--setup', help="setup client(s) for goat interaction", default=False, is_flag=True)
@click.option('-r', '--reset', help="reset client credentials; i.e. post AD password rotation", default=False, is_flag=True)
@click.pass_context
def cli(ctx, debug, version, aliases, manuals, setup, reset):
    ctx.ensure_object(dict)
    if version:
        goat_version()
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
    if setup or reset:
        from .cmd_preset import init
        RESULT = init()
        easy_setup(reset=reset)
        sys.exit(0)
    Log.setup('goat', int(debug))
    pass

def goat_version():
    from importlib_metadata import version
    print('GOAT:\t\t\t' + version('goat'))
    print('- awstools:\t\t' + version('awstools'))
    print('- configstore:\t\t' + version('configstore'))
    print('- jiratools:\t\t' + version('jiratools'))
    print('- slacktools:\t\t' + version('slacktools'))
    print('- toolbox:\t\t' + version('toolbox'))
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
    from contools.tools import cli as confluence
    from .cmd_slack import slack
    from gitools.tools import cli as git
    cli.add_command(slack)
    cli.add_command(report)
    cli.add_command(git, name='git')
    cli.add_command(confluence, name='confluence')

if __name__ == "__main__":
    cli()
