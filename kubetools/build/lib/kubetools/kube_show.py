import click
from .kube_vdp import vdp_clusters
from .kube_deployments import deployments_show
from .kube_namespaces import namespaces_show
from toolbox import misc

@click.group('show', help='show information pulled from VDP/kubernetes', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def show():
    pass

show.add_command(vdp_clusters, name='vdp_clusters')
show.add_command(deployments_show, name='deployments')
show.add_command(namespaces_show, name='namespaces')
