import click
from .kubeclients import vdpclient, k8sclient
from toolbox.logger import Log
from toolbox import misc

@click.group('cluster', help='switch cluster contexts and show k8s cluster info', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def cluster(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@cluster.command('set', help="set current context to a specific cluster; (e.g res02)", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=True)
@click.pass_obj
def cluster_set(cluster_short_name):
    VDP = vdpclient()
    RESULT = VDP.set_cluster(cluster_short_name)
    if RESULT.ok:
        Log.info(RESULT.msg)
    else:
        Log.critical(RESULT.msg)

@cluster.command('events', help='show cluster events for a specific cluster or all clusters')
@click.argument('cluster_short_name', required=False, default=None)
def clusters_events(cluster_short_name):
    VDP = vdpclient()
    K8S = k8sclient()
    if cluster_short_name is None:
        CLUSTERS = VDP.CLUSTERS
        for CLUSTER in CLUSTERS:
            cluster_events_get(CLUSTER['short_name'])
    else:
        cluster_events_get(cluster_short_name)
    Log.info('current context: ' + K8S.run('config current-context').msg)

def cluster_events_get(cluster_short_name):
    VDP = vdpclient()
    K8S = k8sclient()
    RESULT = VDP.set_cluster(cluster_short_name)
    if RESULT.ok:
        Log.info(RESULT.msg)
    else:
        Log.critical(RESULT.msg)
    Log.info(K8S.run('get events -A').msg + '\n')           

@cluster.command('pressures', help='show pressure across all clusters or on a specific cluster', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=False, default=None)
def cluster_pressures(cluster_short_name):
    VDP = vdpclient()
    K8S = k8sclient()
    if cluster_short_name is None:
        CLUSTERS = VDP.CLUSTERS
        for CLUSTER in CLUSTERS:
            cluster_pressures_get(CLUSTER['short_name'])
    else:
        cluster_pressures_get(cluster_short_name)
    Log.info('current context: ' + K8S.run('config current-context').msg)

def cluster_pressures_get(cluster_short_name):
    VDP = vdpclient()
    K8S = k8sclient()
    RESULT = VDP.set_cluster(cluster_short_name)
    if RESULT.ok:
        Log.info(RESULT.msg)
    else:
        Log.critical(RESULT.msg)
    Log.info(K8S.run('describe nodes | grep Pressure | grep -v False').msg)
    Log.info(K8S.run('describe nodes | grep DiskPressure | grep -v KubeletHasNoDiskPressure').msg + '\n')
