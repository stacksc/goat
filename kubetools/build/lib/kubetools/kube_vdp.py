import click, os
from configstore.configstore import Config
from csptools.cspclient import CSPclient
from toolbox.logger import Log
from .kubeclients import vdpclient
from toolbox import misc

@click.group('vdp', help='a collection of utilities to help with VDP', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.pass_context
def vdp(ctx):
    ctx.ensure_object(dict)
    ctx.obj['profile'] = ctx.parent.params['user_profile']
    pass

@vdp.command('setup', help='setup a VDP profile for an organization', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('target_org', required=True, default=None)
@click.option('-d', '--default', 'is_default', help='set the new profile as a default profile for VDP client', required=False, is_flag=True, default=False)
@click.pass_context
def vdp_setup(ctx, target_org, is_default):
    VDP = vdpclient()
    VDP_PROFILE_NAME = f"org_{target_org}"
    AUTH, PROFILE = get_operator_context(ctx)
    REFRESH = get_org_refresh_token(ctx)
    if vdp_installed(VDP):
        RESULT = VDP.run(f'profile set {VDP_PROFILE_NAME} --endpoint {VDP.ENDPOINT} --token {REFRESH}')
    if not RESULT.ok:
        Log.critical(f'failed to set profile for org {target_org}\nmsg: {RESULT.msg}')
    if is_default:
        RESULT = VDP.run(f'profile activate {VDP_PROFILE_NAME}')
    if not RESULT.ok:
        Log.critical(f'failed to set {VDP_PROFILE_NAME} as default\nmsg: {RESULT.msg}')
    Log.info('vdp profile configuration complete')

@vdp.command('kubeconfig', help='create vdp kubeconfig for an organization')
@click.argument('target_org', required=True)
@click.option('-P', '--project', help='set project name', required=False, default=None)
@click.option('-n', '--namespace', help='set default namespace', required=False, default=None)
@click.option('-m', '--merge', help='merge the result with existing config', required=False, is_flag=True, default=False)
@click.pass_context
def vdp_kubeconfig(ctx, target_org, project, namespace, merge):
    VDP = vdpclient()
    VDP_PROFILE_NAME = f"org_{target_org}"
    TARGET = CSPclient.get_org_ids(target_org, ctx.obj['profile'])
    CLUSTER = None
    for KNOWN_CLUSTER in VDP.CLUSTERS:
        if KNOWN_CLUSTER['org'] == TARGET['id']:
            CLUSTER = KNOWN_CLUSTER['name']
    if CLUSTER is None:
        Log.critical('failed to find cluster name for specified organization')
    USER_HOME = os.environ['HOME']
    KUBECONFIG_FILE = f"{USER_HOME}/{VDP_PROFILE_NAME}.kubeconfig"
    if vdp_installed(VDP):
        if os.path.exists(KUBECONFIG_FILE):
            os.remove(KUBECONFIG_FILE)
        RESULT = VDP.run(f"profile set {VDP_PROFILE_NAME} --endpoint {VDP.ENDPOINT} --token {TARGET['token']}")
        if not RESULT.ok:
            Log.critical(f'failed to set profile for org {target_org}\nmsg: {RESULT.msg}')
        if project is not None:
            VDP.run(f"profile set  {VDP_PROFILE_NAME} --project {project}")
        Log.info(VDP.run(f'profile list {VDP_PROFILE_NAME}').msg)
        CMD = f"cluster kubeconfig --profile {VDP_PROFILE_NAME} --context-name ${CLUSTER}"
        if namespace is not None:
            CMD=f"{CMD} --default-namespace {namespace}"
        CMD = f"{CMD} {CLUSTER}"
        if merge:
            os.environ['KUBECONFIG'] = KUBECONFIG_FILE
            CMD = f"{CMD} --merge"
        if not VDP(CMD).ok:
            Log.critical(f"failed to create file {KUBECONFIG_FILE}")
        else:
            Log.info(f'kubeconfig created: {KUBECONFIG_FILE}')

@vdp.command('clusters', help='show a list of VDP clusters', context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()})
@click.argument('target_org', required=True)
@click.pass_context
def vdp_clusters(ctx, target_org):
    VDP = vdpclient()
    VDP_PROFILE_NAME = f"org_{target_org}"
    RESULT = VDP.run(f"profile get {VDP_PROFILE_NAME}")
    if not RESULT.ok is False:
        Log.critical(f'failed to find profile for organization {target_org}, try to set it up first')
    else:
        Log.info(VDP.run(f"cluster list --profile {VDP_PROFILE_NAME} | grep http | awk '{{print $1}}'").msg)

def vdp_installed(vdp):
  if vdp.run('--version').ok is False:
    Log.critical('failed to find vdp command')
  else:
    return True

def get_operator_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'operator'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def get_org_refresh_token(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'operator'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        REFRESH = PROFILE['config'][AUTH]['refresh_token']
        ctx.obj[PROFILE_NAME] = AUTH
        if REFRESH:
            break
    return REFRESH

def get_platform_context(ctx):
    CONFIG = Config('csptools')
    PROFILE_NAME = 'platform'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME
