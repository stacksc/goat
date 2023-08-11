#!/usr/bin/env python3

import click, os, sys, gnureadline, operator
from pathlib import Path
from toolbox.logger import Log
from jiratools.jiraclient import cli as jira
from configstore.configstore_ctrl import cli as configs
from awstools.awstools import CLI as aws
from ocitools.ocitools import CLI as oci
from jenkinstools.jenkinstools import cli as jenkins
from toolbox.misc import set_terminal_width, detect_environment, search_man_pages, debug, draw_title
from .cmd_slack import slack

if os.getenv('USER') == 'root':
    print('...unable to run goat as root! Exiting')
    exit(1)

MESSAGE = 'goat => GCP, OCI, & AWS TK'

@click.group(help=MESSAGE, context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()}, invoke_without_command=True)
@click.option('-v', '--version', help="print version of goat and all its submodules", default=False, is_flag=True)
@click.option('-m', '--manuals', help="print all defined manuals matching pattern(s)", type=str, multiple=True, required=False)
@click.pass_context
def cli(ctx, version, manuals):
    ctx.ensure_object(dict)
    if version:
        goat_version()
        sys.exit(0)
    if manuals:
        name = search_man_pages(manuals)
        os.system(f"man {name}")
        sys.exit(0)
    Log.setup('goat', int(debug))
    pass

def goat_version():
    from importlib_metadata import version
    RES = draw_title()
    print('GOAT:\t\t\t' + version('goat'))
    print('- awstools:\t\t' + version('awstools'))
    print('- configstore:\t\t' + version('configstore'))
    print('- jenkinstools:\t\t' + version('jenkinstools'))
    print('- jiratools:\t\t' + version('jiratools'))
    print('- ocitools:\t\t' + version('ocitools'))
    print('- slacktools:\t\t' + version('slacktools'))
    print('- toolbox:\t\t' + version('toolbox'))
    print(RES)
    sys.exit(0)

cli.add_command(configs, name='configs')
cli.add_command(jira, name='jira')
cli.add_command(aws, name='aws')
cli.add_command(oci, name='oci')
cli.add_command(jenkins, name='jenkins')
cli.add_command(slack)

if __name__ == "__main__":
    cli(ctx)
