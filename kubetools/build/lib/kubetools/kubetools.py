import click
from toolbox.logger import Log
from .kube_vdp import vdp
from .kube_cluster import cluster
from .kube_deployments import deployments
from .kube_namespaces import namespaces
from .kube_nodes import nodes
from .kube_show import show
from toolbox import misc

@click.group(help="IN-DEV | a module to improve kubernetes & vdp", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-p', '--profile', 'user_profile', help="user profile for the operation", type=str, required=False, default='default')
@click.pass_context
def cli(ctx, debug, user_profile):
    Log.setup('kubetools', int(debug))
    pass

cli.add_command(vdp)
cli.add_command(cluster)
cli.add_command(deployments)
cli.add_command(namespaces)
cli.add_command(nodes)
cli.add_command(show)

if __name__ == "__main__":
    cli()
