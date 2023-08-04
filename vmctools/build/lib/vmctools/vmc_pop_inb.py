# inb - in-boundary - POP is accessible only via VDP user pod

import click
from .popclient import popclient
from toolbox.logger import Log

@click.group(help="connect to, manage and view info about SDDC's POP instance", context_settings={'help_option_names':['-h','--help']})
@click.option('-a', '--auth', 'auth_org', help="org id/name to use for authentication", type=str, required=False, default='operator')
@click.pass_context
def pop(ctx):
    pass

@click.command('start', help='request access to POP in a given SDDC and connect to it via ssh')
@click.argument('sddc_id', required=True)
@click.argument('ticket', required=True)
@click.option('-c', '--command', help="run a specific command over ssh instead of opening an interactive session", required=False, default=None)
@click.pass_context
def pop_start(ctx, sddc_id, ticket, command):
    POP = popclient(ctx)
    RESULT = POP.start_vdp_pod()
    RESULT.print()
    POD_NAME = RESULT.pod
    RESULT = POP.start_pop(POD_NAME)

    
