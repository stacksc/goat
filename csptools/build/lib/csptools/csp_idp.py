import sys, os, click, json
from .idpclient import idpc
from idptools.idpclient import IDPclient
from toolbox.logger import Log
from toolbox.jsontools import filter
import toolbox.misc as misc
from configstore.configstore import Config
from toolbox.menumaker import Menu

CONFIG = Config('csptools')

@click.group('idp', help="VMware IDP/vIDP Client", context_settings={'help_option_names':['-h','--help'], 'max_content_width': misc.set_terminal_width()}, invoke_without_command=True)
@click.option('-d', '--debug', help="0 = no output, 1 = default, 2 = debug on", default='1', type=click.Choice(['0', '1', '2']))
@click.option('-m', '--menu', help="launch a menu driven interface for common CSP user actions", is_flag=True)
@click.pass_context
def idp(ctx, debug, menu):
    profile = ctx.obj['profile']
    if menu is True:
        ctx.obj['menu'] = True
    else:
        ctx.obj['menu'] = False

    PROFILE = CONFIG.get_profile('operator')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj['operator'] = AUTH
        if AUTH:
            break

    PROFLE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj['platform'] = AUTH
        if AUTH:
            break
    log = Log('csptools.log', debug)

@idp.command('add', help='regiter vIDM tenant', context_settings={'help_option_names':['-h','--help']})
@click.argument('tenant', required=True)
@click.argument('domains', required=True)
@click.argument('ticket', required=True)
@click.argument('public_key', required=True)
@click.pass_context
def idp_add(ctx, tenant, domain, ticket, public_key):
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    RESULT = IDP.add(tenant, domain, ticket, public_key, AUTH)
    Log.info(RESULT)

@idp.command('delete', help='delete vIDM tenant', context_settings={'help_option_names':['-h','--help']})
@click.argument('idp_id', required=True)
@click.option('-f', '--force', help='force the deletion', is_flag=True, required=True, default=False)
@click.pass_context
def idp_delete(ctx, idp_id, force):
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    RESULT = IDP.delete(idp_id, force, AUTH)
    Log.info(RESULT)

@idp.command('show', help='list all vIDM tenants with optional filter', context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--tenants', help='show only tenant display names', is_flag=True, required=False, default=False)
@click.option('-f', '--filter', 'filter_definition', help='filter the result by key:value, key: or :value', required=False, default=None)
@click.pass_context
def idp_show(ctx, tenants, filter_definition):
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    if tenants:
        RESULT = IDP.get_tenant_names(filter_definition, AUTH)
        for TENANT in RESULT:
            Log.info(TENANT)
        sys.exit(0)
    RESULT = IDP.show(filter_definition, AUTH)
    if filter_definition:
        for ITEM in RESULT:
            for I in ITEM:
                FILTER = I[f'{filter_definition}']
                if FILTER:
                    Log.info(f'{FILTER}')
    else:
        Log.json(json.dumps(RESULT, indent=2))

def _get_tenant_ids(filter_definition=None):
    CONFIG = Config('csptools')
    PROFILE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        if AUTH:
            break
    IDP = idpc('platform')
    DATA = IDP.get_tenant_ids(filter_definition, AUTH)
    return DATA

def _get_tenants(filter_definition=None):
    PROFILE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        if AUTH:
            break
    IDP = idpc('platform')
    DATA = IDP.get_tenant_names(filter_definition, AUTH)
    return DATA

@idp.command('users', help='list all vIDM users belonging to a tenant', context_settings={'help_option_names':['-h','--help']})
@click.option('-t', '--tenant', help='display users belonging to a specific tenant', required=False, default=None)
@click.pass_context
def idp_users(ctx, tenant):
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    if not tenant:
        TENANTS = _get_tenants()
        TENANTS.sort()
        INPUT = 'Tenant Manager'
        CHOICE = runMenu(TENANTS, INPUT)
        if CHOICE:
            CHOICE = ''.join(CHOICE)
            tenant = CHOICE.split('\t')[1].strip()
            url = CHOICE.split('\t')[0].strip()
            Log.info(f'gathering users belonging to tenant {tenant} => {url}')
        else:
            Log.critical("please select a tenancy to gather users")

    ctx.obj['profile'] = tenant
    IDP = IDPclient(ctx)
    RESULT = IDP.list_users(ctx)
    Log.json(json.dumps(RESULT, indent=2))

@idp.group('domains', help='manage tenant vIDM domains', context_settings={'help_option_names':['-h','--help']})
def idp_domains():
    pass

@idp_domains.command('add', help='add domains to vIDM tenant', context_settings={'help_option_names':['-h','--help']})
@click.argument('idp_id', required=True)
@click.argument('domains', required=True)
@click.pass_context
def idp_domains_add(ctx, idp_id, domains):
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    RESULT = IDP.domains_add(idp_id, domains, AUTH)
    Log.info(RESULT)

@idp_domains.command('delete', help='remove vIDM tenant domains', context_settings={'help_option_names':['-h','--help']})
@click.argument('idp_id', required=True)
@click.argument('domains', required=True)
@click.pass_context
def idp_domains_delete(ctx, idp_id, domains):
    AUTH, PROFILE = get_platform_context(ctx)
    IDP = idpc(PROFILE)
    RESULT = IDP.domains_delete(idp_id, domains, AUTH)
    Log.info(RESULT)

def get_operator_context(ctx):
    PROFILE_NAME = 'operator'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME

def get_platform_context(ctx):
    PROFILE_NAME = 'platform'
    PROFILE = CONFIG.get_profile(PROFILE_NAME)
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        ctx.obj[PROFILE_NAME] = AUTH
        if AUTH:
            break
    return AUTH, PROFILE_NAME


def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'TENANT Menu: {INPUT}'
    for data in DATA:
        COUNT = COUNT + 1
        RESULTS = []
        RESULTS.append(data)
        FINAL.append(RESULTS)
    SUBTITLE = f'showing {COUNT} available object(s)'
    JOINER = '\t\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, SUBTITLE)
    CHOICE = FINAL_MENU.display()
    return CHOICE

