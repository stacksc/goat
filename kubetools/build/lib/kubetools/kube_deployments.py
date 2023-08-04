import click
from toolbox.logger import Log
from .kubeclients import vdpclient, k8sclient
from toolbox import misc

@click.group('deployments', help='manage and list deployments', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def deployments(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@deployments.command('show', help='show info about a specific deployment or all deployments', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('deployment', required=False, default=None)
@click.option('-c', '--cluster', help='limit the search to a specific cluster (short name, ie. res002)', required=False, default=None)
@click.option('-n', '--namespace', help='limit the search to a specific namespace', required=False, default=None)
@click.option('-a', '--app', help='limit the search to a specific app', required=False, default=None)
@click.pass_obj
def deployments_show(ctx, deployment, cluster, namespace, app):
    CMD = 'get deployment'
    if cluster is not None:
        deployments_show_cluster(cluster, deployment, namespace, app)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            deployments_show_cluster(CLUSTER['short_name'], deployment, namespace, app)

def deployments_show_cluster(cluster_short_name, deployment, namespace, app):
    K8S = k8sclient()
    VDP = vdpclient()
    VDP.set_cluster(cluster_short_name)
    if deployment is not None:
        if namespace is None:
            Log.critical('namespace is required for showing a specific deployment')
    if app is not None:
        CMD = f"{CMD} -l app={app}"
    if namespace is None:
        CMD = f"{CMD} --all-namespaces"
    else:
        CMD = f"{CMD} --namespace {namespace}" 
    Log.info(K8S.run(CMD).msg)
