import click, os
from os.path import exists
from .kubeclients import vdpclient, k8sclient, run_command
#from awstools.iam_ingc import _assume_role
from toolbox.logger import Log
from toolbox.jsontools import reduce_json
from toolbox import misc

@click.group('nodes', help='manage and list nodes', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def nodes(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@nodes.group('show', help='show nodes info', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
def nodes_show():
    pass

@nodes_show.command('all', help='show details about all nodes', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=False, default=None)
@click.option('-r', '--role', 'role_name', help='filter nodes by roles name', required=False, default=None)
@click.pass_obj
def nodes_show_all(ctx, cluster_short_name, role_name):
    if cluster_short_name is not None:
        OUTPUT = _nodes_show_all(cluster_short_name, role_name)
        Log.info(OUTPUT)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            OUTPUT = _nodes_show_all(CLUSTER['short_name'], role_name)
            Log.info(OUTPUT)

def _nodes_show_all(cluster_short_name, role_name=None):
    VDP = vdpclient()
    K8S = k8sclient()
    VDP.set_cluster(cluster_short_name)
    Log.info(K8S.run('config current-context').msg)
    CMD = 'get node'
    if role_name is not None:
        CMD = f'{CMD} --selector="node-role.kubernetes.io/{role_name}"'
    CMD = f"{CMD} --output json"
    RESULT = K8S.run(CMD).msg
    #REDUCE = {  } #  TBD
    #.metadata.labels."kubernetes.io/hostname" + " " + (.status.addresses[] | select(.type == "InternalIP") | .address) + " " + .metadata.creationTimestamp + " " +  .metadata.labels."kubernetes.io/role" + " " + (.status.conditions[] | select(.type=="Ready") | .status) + " " + .status.nodeInfo.kubeletVersion + " " + .metadata.labels."failure-domain.beta.kubernetes.io/zone"'
    return RESULT

@nodes_show.command('top', help='show all the top nodes', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=False, default=None)
@click.option('-s', '--sort', help='sort by cpu ot by memory', type=click.Choice(['mem', 'cpu']), required=False, default=None)
def nodes_show_top(cluster_short_name, sort):
    if cluster_short_name is not None:
        OUTPUT = _nodes_show_top(cluster_short_name, sort)
        Log.info(OUTPUT)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            OUTPUT = _nodes_show_top(CLUSTER['short_name'], sort)
            Log.info(OUTPUT)

def _nodes_show_top(cluster_short_name, sort):
    VDP = vdpclient()
    K8S = k8sclient()
    VDP.set_cluster(cluster_short_name)
    Log.info(K8S.run('config current-context').msg)
    Log.info('kubectl top nodes')
    CMD = 'top nodes'
    if sort == 'mem':
        CMD = f"{CMD} | sort --reverse --key=4 --numeric"
    if sort == 'cpu':
        CMD = f"{CMD} | sort --reverse --key=2 --numeric"
    return K8S.run(CMD).msg

@nodes_show.command('ossec', help='show the json files for ossec across all nodes', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=False, default=None)
@click.option('-m', '--masters', help='run only against master nodes', required=False, default=False, is_flag=True)
@click.option('-v', '--var_only', help='display only vars', required=False, default=False, is_flag=True)
def nodes_show_ossed(cluster_short_name, masters, var_only):
    cmd = "sudo find /var/ossec/logs/archives/2020 -type f -ls | egrep '.sum|.gz'"
    if cluster_short_name is not None:
        OUTPUT = _nodes_run(cmd, cluster_short_name, masters, var_only)
        if OUTPUT.ok:
            Log.info(OUTPUT.msg)
        else:
            Log.critical(OUTPUT.msg)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            OUTPUT = _nodes_run(cmd, CLUSTER['short_name'], masters, var_only)
            if OUTPUT.ok:
                Log.info(OUTPUT.msg)
            else:
                Log.warn(OUTPUT.msg)

@nodes_show.command('disks', help='show disks for all nodes in the cluster', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=False, default=None)
@click.option('-m', '--masters', help='run only against master nodes', required=False, default=False, is_flag=True)
@click.option('-v', '--var_only', help='display only vars', required=False, default=False, is_flag=True)
def nodes_show_top(cluster_short_name, masters, var_only):
    cmd = 'df -k'
    if cluster_short_name is not None:
        OUTPUT = _nodes_run(cmd, cluster_short_name, masters, var_only)
        if OUTPUT.ok:
            Log.info(OUTPUT.msg)
        else:
            Log.critical(OUTPUT.msg)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            OUTPUT = _nodes_run(cmd, CLUSTER['short_name'], masters, var_only)
            if OUTPUT.ok:
                Log.info(OUTPUT.msg)
            else:
                Log.warn(OUTPUT.msg)

@nodes.group('delete', help='delete a node in a specific cluster', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cluster_short_name', required=False, default=None)
@click.argument('node_name', required=False, default=None)
@click.option('-f', '--force', help='force the deletion', required=False, default=False, is_flag=True)
def node_delete(cluster_short_name, node_name, force):
    _node_delete(cluster_short_name, node_name, force)

def _node_delete(cluster_short_name, node_name, force):
    K8S = k8sclient()
    VDP = vdpclient()
    if force:
        while True:
            CHOICE = input(f'are you sure you want to delete {node_name} in {cluster_short_name} (y/n): ')
            if CHOICE == 'y' or CHOICE == 'n':
                break
        if CHOICE == 'n':
            Log.critical('aborting operation')
        else:
            Log.info('proceeding with force deletion')
    IP = K8S.run(f"get nodes -l kubernetes.io/hostname={node_name} -o jsonpath={{.items[*].status.addresses[?\(@.type==\"InternalIP\"\)].address}}").msg
    if IP == "":
        Log.critical(f"NODE {node_name} or IP address not showing up - please validate the node to be deleted")
    else:   
        VDP.set_cluster(cluster_short_name)
        Log.info(f'issuing: kubectl drain --ignore-daemonsets --force --delete-local-data {node_name}')
        K8S.run(f'drain --ignore-daemonsets --force --delete-local-data {node_name}')
        Log.info(f"issuing: kubectl delete node {node_name}")
        K8S.run(f"delete node {node_name}")
        PEM_FILE = _check_pem_file()
        INSTANCE_ID = run_command(f'ssh -o StrictHostKeyChecking=no -q -i {PEM_FILE} -l ec2-user {IP} curl -s http://169.254.169.254/latest/meta-data/instance-id')
        ACCOUNT = run_command(f"ssh -o StrictHostKeyChecking=no -q -i {PEM_FILE} -l ec2-user {IP}  curl -s http://169.254.169.254/latest/meta-data/identity-credentials/ec2/info | jq -r .AccountId")
        Log.info(f"assuming role to {ACCOUNT} and terminating f{INSTANCE_ID}")
        Log.info(f"please login with your VMwareFed account when prompted below:")
        NODE_ROLE = VDP.CONFIG.get_var('node_arn', 'config', 'NODE_ARN', 'default')
        REGION = VDP.CONFIG.get_var('node_region', 'config', 'REGION', 'default')
        #_assume_role(role_arn=f"arn:aws-us-gov:iam::${ACCOUNT}:role/PowerUser", account_arn=NODE_ROLE, aws_profile_name='nodeterminate')
        run_command(f'aws --profile=nodeterminate ec2 terminate-instance --instance-ids {INSTANCE_ID} --region {REGION}')
        Log.info('node deleted')

@nodes.command('run', help='run a command on all nodes in a specific cluster', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('cmd', required=True)
@click.argument('cluster_short_name', required=False, default=None)
@click.option('-m', '--masters', help='run only against master nodes', required=False, default=False, is_flag=True)
@click.option('-v', '--var_only', help='display only vars', required=False, default=False, is_flag=True)
def nodes_run(cmd, cluster_short_name, masters, var_only):
    if cluster_short_name is not None:
        OUTPUT = _nodes_run(cmd, cluster_short_name, masters, var_only)
        if OUTPUT.ok:
            Log.info(OUTPUT.msg)
        else:
            Log.critical(OUTPUT.msg)
    else:
        VDP = vdpclient()
        for CLUSTER in VDP.CLUSTERS:
            OUTPUT = _nodes_run(cmd, CLUSTER['short_name'], masters, var_only)
            if OUTPUT.ok:
                Log.info(OUTPUT.msg)
            else:
                Log.warn(OUTPUT.msg)

def _nodes_run(cmd, cluster_short_name, masters=False, var_only=False):
    PEM_FILE = _check_pem_file()
    VDP = vdpclient()
    K8S = k8sclient()
    VDP.set_cluster(cluster_short_name)
    Log.info(K8S.run('config current-context').msg)
    CMD = 'get nodes -A -o wide'
    if masters:
        CMD = f"{CMD} -l kubernetes.io/role=master"
    if var_only:
        CMD = f"{CMD} 2>&1 | grep var"
    NODES = K8S.run(f'get nodes -A -o wide ${CMD} | tr -s " " " "| cut -f6 -d" " | grep -v INTERNAL-IP')
    for NODE in NODES:
        Log.info(f"Cluster: {cluster_short_name} | node: {NODE} | cmd: {cmd}")
        if cmd == "sudo find /var/ossec/logs/archives/2020 -type f -ls | egrep '.sum|.gz'": # ossec command
            Log.info('Disk usage summary ossec:')
            DIRS = run_command(f'ssh -o StrictHostKeyChecking=no -q -i {PEM_FILE} -l ec2-user {NODE} sudo ls /var/ossec/logs/archives/2020/')
            for DIR in DIRS:
                RESULT = f"{RESULT}\n{run_command(f'ssh -o StrictHostKeyChecking=no -q -i {PEM_FILE} -l ec2-user {NODE} sudo du -sk /var/ossec/logs/archives/2020/{DIR}')}"
        else:
            RESULT = run_command(f"ssh -o StrictHostKeyChecking=no -q -i {PEM_FILE} -l ec2-user {NODE} {cmd}")
    return RESULT

def _check_pem_file():
    HOME = os.enciron['HOME']
    if exists(f"{HOME}/.ssh/csp.pem"):
        return f"{HOME}/.ssh/csp.pem"
    elif exists(f"{HOME}/csp.pem"):
        return f"{HOME}/csp.pem"
    else:
        Log.error('failed to find CSP PEM file ~/.ssh/csp.pem or ./csp.pem')
