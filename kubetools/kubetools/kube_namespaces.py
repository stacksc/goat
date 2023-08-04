import click
from toolbox.logger import Log
from toolbox import misc
from .kubeclients import k8sclient, vdpclient

@click.group('namespaces', help='manage and list namespaces', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def namespaces(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@namespaces.command('show', help='list namespaces', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.option('-c', '--cluster', help='limit the search to a specific cluster (short name, ie. res002)', required=False, default=None)
@click.pass_obj
def namespaces_show(ctx, cluster):
    if cluster is not None:
        CONTEXT, OUTPUT = namespaces_show_cluster(cluster)
        Log.info(f'Context: {CONTEXT}')
        Log.info(OUTPUT)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            CONTEXT, OUTPUT = namespaces_show_cluster(CLUSTER['short_name'])
            Log.info(f'Context: {CONTEXT}')
            Log.info(OUTPUT)
    
def namespaces_show_cluster(cluster_short_name):
    K8S = k8sclient()
    VDP = vdpclient()
    if not VDP.set_cluster(cluster_short_name).ok:
        Log.critical(f'unable to switch context to {cluster_short_name}')
    return K8S.run('config current-context').msg, K8S.run('get namespace').msg
