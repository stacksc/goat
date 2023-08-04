import click
from toolbox.logger import Log
from .kubeclients import vdpclient, k8sclient
from toolbox import misc

@click.group('pods', help='manage and list pods', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def pods(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@pods.group('show', help='show pods info', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def pods_show():
    Log.critical('not yet implemented')

@pods_show.command('all', help='show details about all pods', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('-c', '--cluster', 'cluster_short_name', help='limit the output to a specific cluster', required=False, default=None)
@click.argument('-n', '--namespace', help='limit the output to a specific namespace', required=False, default=None)
@click.argument('-a', '--app', help='limit the output to a specific app', required=False, default=None)
@click.argument('-s', '--state', help='limit the output to a specific state', required=False, default=None)
@click.argument('-p', '--pod', help='limit the output to a specific pod', required=False, default=None)
@click.argument('-g', '--good', 'good_only', help='limit the output to the good pods only', is_flag=True, required=False, default=None)
def pods_show_all(cluster_short_name, namespace, app, state, pod, good_only):
    if cluster_short_name is not None:
        OUTPUT = _pods_show_all(cluster_short_name, namespace, app, state, pod, good_only)
        if OUTPUT.ok:
            Log.info(OUTPUT.msg)
        else:
            Log.critical(OUTPUT.msg)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            OUTPUT = _pods_show_all(CLUSTER['short_name'], namespace, app, state, pod, good_only)
            if OUTPUT.ok:
                Log.info(OUTPUT.msg)
            else:
                Log.warn(OUTPUT.msg)

def _pods_show_all(cluster_short_name, namespace, app, state, pod, good_only):
    VDP = vdpclient()
    K8S = k8sclient()
    VDP.set_cluster(cluster_short_name)
    Log.info(K8S.run('config current-context').msg)
    CMD = "get pod -A -o wide"
    if pod is not None:
        if namespace is None:
            Log.critical('cant list a specific pod without providing a namespace')
        else:
            CMD = f"{CMD} {pod}"    
    if namespace is not None:
        CMD = f"{CMD} --namespace {namespace}"
    else:
        CMD = f"{CMD} --all-namespaces"
    if state is not None:
        CMD = f"{CMD} --field-selector=status.phase={state}"
    if app is not None:
        CMD = f"{CMD} -l app={app}"
    if good_only:
        CMD = f"{CMD} | egrep -v 'Running|Completed'"
    return K8S.run(CMD)

@pods_show.command('top', help='show all the top pods', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def pods_show_top():
    Log.critical('not yet implemented')

@pods_show.command('log', help='display pod log', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def pods_show_log():
    Log.critical('not yet implemented')

@pods.command('delete', help='delete pods of specific type', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('state', required=True)
@click.argument('cluster_short_name', required=True)
def pods_delete(cluster_short_name, state):
    if state != 'Evicted' or state != 'Error' or state != 'Completed':
        Log.critical('incorrect state specified; valid options: Evicted, Error, Completed')
    if cluster_short_name is not None:
        _pods_delete(cluster_short_name, state)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            _pods_delete(CLUSTER['short_name'], state)

def _pods_delete(cluster_short_name, state):
    VDP = vdpclient()
    K8S = k8sclient()
    VDP.set_cluster(cluster_short_name)
    Log.info(K8S.run('config current-context').msg)
    NAMESPACES = K8S.run('get namespace | grep -v NAME | cut -f1 -d" "').msg
    for NAMESPACE in NAMESPACES:
        PODS = K8S.run(f'get pods -n {NAMESPACE} | grep ${state} |cut -f1 -d " "')
        for POD in PODS:
            RESULT = K8S.run(f'delete pod -n {NAMESPACE} {POD}')
            if not RESULT.ok:
                Log.warn(f'failed to delete {NAMESPACE}/{POD}')
    Log.info('operation complete')
