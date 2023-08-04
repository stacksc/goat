import click, json, pprint, re, sys, os, time, csv, datetime, readline
from .sddcclient import sddc
from .vmc_misc import get_operator_context
from .vmcclient import vmc
from idptools.idpclient import IDPclient
from jiratools.issue import add_comment as comment, get_inb_data, global_assign, extract_data_from_issue
from jiratools.auth import get_user_profile_based_on_key, get_jira_session_based_on_key
from jiratools.search import get_comms_data, build_url, search_issues, runMenu as jiraRunMenu, create_link
from csptools.idpclient import idpc
from toolbox.logger import Log
from configstore.configstore import Config
from toolbox.menumaker import Menu
from toolbox.misc import MenuResults, DeletedMenuResults
from csptools.cspclient import CSPclient
from tabulate import tabulate
from toolbox import misc
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CSP = CSPclient()
CONFIG = Config('csptools')

@click.group('onboard', help='VMC end-to-end customer onboarding tasks', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def onboard(ctx):
    pass

@onboard.command(help='launch a menu to perform customer onboarding tasks in order of operation', context_settings={'help_option_names':['-h','--help'], 'max_content_width': 110})
@click.option('-r', '--raw', 'raw', help="display raw json; don't reduce output", is_flag=True, required=False, default=False)
@click.option('-t', '--ticket', 'ticket', help="provide CSSD ticket", type=str, required=False, default='CSSD-1234')
@click.option('-s', '--set', 'set', help="flag to specify the type of organization", required=False, default=None, type=click.Choice(['CUSTOMER','CUSTOMER_POC','INTERNAL_AWS','INTERNAL_CORE','INTERNAL_CUSTOMER','INTERNAL_ECO','INTERNAL_NON_CORE']))
@click.pass_context
def menu(ctx, raw, ticket, set):
    OPTION = ''
    while OPTION != 'Quit':
        OPTIONS = ['Organization Creation Tasks', 'User Creation Tasks', 'Update Ticket', 'Update Organization with SID', 'vIDM Tenant Creation', 'Misc Sub-Menu', 'Quit']
        DATA = []
        for OPTION in OPTIONS:
            STR = OPTION.ljust(60)
            DATA.append(STR)
        INPUT = 'Customer Onboarding'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            OPTION = CHOICE.split('\t')[0].strip()
            if OPTION and OPTION != 'Quit':
                Log.info(f"launching {OPTION} tasks now, please wait...")
            else:
                if OPTION == 'Quit':
                    break
                else:
                    Log.critical("please select an option to continue...")
        except:
            Log.critical("please select an option to continue...")
        if 'Sub-Menu' in OPTION:
            OPTION = ''
            while OPTION != 'Main Menu':
                OPTIONS = ['Mark Organization as Deleted', 'Mark Organization as Active', 'Rename Organization', 'Organization Details', 'Delete Child Tenant', 'Child Tenant Details', 'Show User Details', 'Remove User from Org', 'Remove User from Tenant', 'Add User to Org', 'Add User to Tenant', 'List Orgs per User', 'Delete SDDC', 'Return']
                DATA = []
                for OPTION in OPTIONS:
                    STR = OPTION.ljust(60)
                    DATA.append(STR)
                INPUT = 'Misc Sub-Menu'
                CHOICE = runMenu(DATA, INPUT)
                try:
                    CHOICE = ''.join(CHOICE)
                    OPTION = CHOICE.split('\t')[0].strip()
                    if OPTION and OPTION != 'Return':
                        Log.info(f"launching {OPTION} tasks now, please wait...")
                    else:
                        if OPTION == 'Return':
                            break
                        else:
                            Log.critical("please select an option to continue...")
                except:
                    Log.critical("please select an option to continue...")
                if 'Mark Organization as Deleted' in OPTION:
                    AUTH, PROFILE = get_operator_context(ctx)
                    TARGET_ORG_ID, NAME = MenuResults(ctx)
                    OUTPUT = CSP.delete_org(TARGET_ORG_ID, AUTH, PROFILE)
                    try:
                        if OUTPUT.status_code == 200:
                            Log.info(f'organization {NAME} marked as deleted')
                        else:
                            Log.critical('failed to mark the org as deleted')
                    except:
                        Log.critical('failed to mark the org as deleted')
                elif 'Mark Organization as Active' in OPTION:
                    AUTH, PROFILE = get_operator_context(ctx)
                    TARGET_ORG_ID, NAME = DeletedMenuResults(ctx)
                    OUTPUT = CSP.activate_org(TARGET_ORG_ID, AUTH, PROFILE)
                    try:
                        if OUTPUT.status_code == 200:
                            Log.info(f'organization {NAME} marked as active')
                        else:
                            Log.critical('failed to mark the org as active')
                    except:
                        Log.critical('failed to mark the org as active')
                elif 'Rename' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    TARGET_ORG, NAME = MenuResults(ctx)
                    NEW_ORG_NAME = input('Enter the new organization name: ')
                    OUTPUT = CSP.rename_org(TARGET_ORG, NEW_ORG_NAME, AUTH, PROFILE)
                    if OUTPUT:
                        Log.json(json.dumps(OUTPUT, indent=2))
                    Log.info('please wait for CSP to sync, this can take a minute...')
                    OUTPUT = CSP.trigger_ss_backend(ctx.obj['operator'], 'operator')
                    if OUTPUT:
                        Log.info('renamed the organization successfully')
                elif 'Organization Details' in OPTION:
                    AUTH, PROFILE = get_operator_context(ctx)
                    TARGET_ORG, NAME = MenuResults(ctx)
                    if TARGET_ORG is None:
                        Log.critical("please select an organization to continue using the menu interface.")
                    OUTPUT = CSP.org_show_details(TARGET_ORG, AUTH, PROFILE)
                    if OUTPUT == []:
                        Log.critical('unable to find org details or org doesnt exist')
                    else:
                        Log.json(json.dumps(OUTPUT, indent=2))
                elif 'Delete Child Tenant' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    TENANTS = _get_tenants()
                    TENANTS.sort()
                    INPUT = 'Parent Tenant Selection'
                    CHOICE = runMenu(TENANTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        PARENT = CHOICE.split('\t')[1].strip()
                        if 'VMwareFed' in PARENT:
                            PARENT = 'vmc-prod'
                        elif 'customer.local' in PARENT:
                            PARENT = 'customer-local'
                    else:
                        Log.critical("please select a parent-tenancy to continue")
                    ctx.obj['profile'] = PARENT
                    IDP = IDPclient(ctx)
                    TENANTS = IDP.list_all_tenants()
                    DATA = []
                    for TENANT in TENANTS:
                        NAME = TENANT['name']
                        DATA.append(NAME)
                    INPUT = 'Child Tenant Selection'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        TENANT = CHOICE.split('\t')[0].strip()
                    else:
                        Log.critical("please select a child tenancy to continue")
                    RESULT = IDP.delete_tenant(TENANT)
                    if RESULT:
                        Log.json(json.dumps(RESULT.json(), indent=2))
                    else:
                        Log.critical(f'failure while deleting tenant {TENANT}')
                elif 'Show User Details' in OPTION:
                    raw = False
                    AUTH, PROFILE = get_platform_context(ctx)
                    target_org, name = MenuResults(ctx)
                    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
                    DATA = []
                    for I in OUTPUT:
                        DATA.append(I['username'])
                    INPUT = 'user manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        user_name = CHOICE.split('\t')[0]
                        if user_name:
                            Log.info(f"gathering username {user_name} details now, please wait...")
                        OUTPUT = CSP.user_list_details(user_name, AUTH, PROFILE)
                        Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
                    else:
                        Log.critical("please select a username to continue...")
                elif 'Remove User from Org' in OPTION:
                    raw = False
                    AUTH, PROFILE = get_platform_context(ctx)
                    target_org, name = MenuResults(ctx)
                    OUTPUT = CSP.show_all_users(target_org, raw, AUTH, PROFILE)
                    DATA = []
                    for I in OUTPUT:
                        DATA.append(I['username'])
                    INPUT = 'user manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        user_name = CHOICE.split('\t')[0]
                        if user_name:
                            Log.info(f"removing username {user_name} from {name} now, please wait...")
                        OUTPUT = CSP.org_remove_user(user_name, target_org, AUTH, PROFILE)
                        Log.json(json.dumps(OUTPUT, indent=2, sort_keys=True))
                    else:
                        Log.critical("please select a username to continue...")
                elif 'Remove User from Tenant' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    TENANTS = _get_tenants()
                    TENANTS.sort()
                    INPUT = 'Tenant Manager'
                    CHOICE = runMenu(TENANTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        TENANT = CHOICE.split('\t')[1].strip()
                        if 'VMwareFed' in TENANT:
                            TENANT = 'vmc-prod'
                        elif 'customer.local' in TENANT:
                            TENANT = 'customer-local'
                        URL = CHOICE.split('\t')[0].strip()
                        Log.info(f'gathering users belonging to tenant {TENANT} => {URL}')
                    else:
                        Log.critical("please select a tenancy to gather users")
                    ctx.obj['profile'] = TENANT
                    IDP = IDPclient(ctx)
                    OUTPUT = IDP.list_users(raw=False)
                    DATA = []
                    for I in OUTPUT:
                        USERNAME = I['username'].ljust(50)
                        ID = I['id']
                        DATA.append(USERNAME + '\t' + ID)
                    DATA.sort()
                    INPUT = 'User Manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        USERNAME = CHOICE.split('\t')[0].strip()
                        ID = CHOICE.split('\t')[1].strip()
                        Log.info(f'removing user {USERNAME} => {ID}')
                    else:
                        Log.critical("please select a username to remove")
                    RESULT = IDP.delete_user(USERNAME, ID)
                    if RESULT == 200 or RESULT == 204:
                        Log.info(f'removed username {USERNAME} successfully')
                    else:
                        Log.critical(f'remove username {USERNAME} failed')
                elif 'Add User to Tenant' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    TENANTS = _get_tenants()
                    TENANTS.sort()
                    INPUT = 'Tenant Manager'
                    CHOICE = runMenu(TENANTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        TENANT = CHOICE.split('\t')[1].strip()
                        URL = CHOICE.split('\t')[0].strip()
                        Log.info(f'gathering users belonging to tenant {TENANT} => {URL}')
                    else:
                        Log.critical("please select a tenancy to gather users")
                    try:
                        firstname = input("1. Enter new user firstname: ")
                        lastname = input("2. Enter new user lastname: ")
                        email = input("3. Enter new user email address: ")
                        initial = [*firstname][0]
                        tryusername = lastname.lower().strip() + initial.lower().strip()
                        username = input("4. Enter new username [" + tryusername + "]: ")
                    except:
                        Log.critical('encountered an error while capturing new user information; exiting')
                    if not username:
                        username = tryusername.strip()
                        tenant_email = username + '@' + TENANT
                    else:
                        tenant_email = username + '@' + TENANT
                    if '.' not in username:
                        print()
                        Log.info(f'running add user on username: {username}')
                    else:
                        Log.critical('please provide a username without a "." in it')

                    CONFIG = Config('idptools')
                    if 'customer.local' in TENANT:
                        ctx.obj['profile'] = 'customer-local'
                        PROFILE = CONFIG.get_profile('customer-local')
                        DOMAIN = 'customer-local'
                    elif 'VMwareFed' in TENANT:
                        ctx.obj['profile'] = 'vmc-prod'
                        PROFILE = CONFIG.get_profile('vmc-prod')
                        DOMAIN = 'vmc-prod'
                    else:
                        ctx.obj['profile'] = TENANT
                        PROFILE = CONFIG.get_profile(TENANT)
                        DOMAIN = TENANT
                    ctx.obj['url'] = URL
                    ALL = PROFILE['config']
                    for I in ALL:
                        client_id = ALL[I]['client-id']
                        secret = ALL[I]['client-secret']
                        if client_id and secret:
                            ctx.obj['client-id'] = client_id
                            ctx.obj['client-secret'] = secret
                            break
                    IDP = IDPclient(ctx)
                    CHK = IDP.getUserID(username)
                    if CHK:
                        Log.warn(f'username {username} already exists in tenant: {TENANT}')
                        Log.info('please try again using an alternate username')
                    else:
                        print()
                        print("*****************************************************************************")
                        print(f"Tenant        => {TENANT}")
                        print(f"First Name    => {firstname}")
                        print(f"Last Name     => {lastname}")
                        print(f"Email Address => {email}")
                        print(f"Username      => {username}")
                        print(f"Tenant Email  => {tenant_email}")
                        print("*****************************************************************************")
                        try:
                            wait_for_enter()
                        except:
                            Log.critical('breaking from script due to an unknown interrupt')
                        OTA_LINK = IDP.add_user(username, firstname, lastname, tenant_email, TENANT)
                        if OTA_LINK:
                            try:
                                CONFIG.update_config(OTA_LINK, f"ota-link-{username}", DOMAIN)
                            except:
                                Log.info(f'{DOMAIN} is not saved in the configstore for user: ' + os.environ['LOGNAME'])
                        Log.info(OTA_LINK)
                elif 'Add User to Org' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    IDP = idpc(PROFILE)
                    TENANTS = _get_tenants()
                    TENANTS.sort()
                    INPUT = 'Tenant Manager'
                    CHOICE = runMenu(TENANTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        TENANT = CHOICE.split('\t')[1].strip()
                        if 'VMwareFed' in TENANT:
                            TENANT = 'vmc-prod'
                        elif 'customer.local' in TENANT:
                            TENANT = 'customer-local'
                        URL = CHOICE.split('\t')[0].strip()
                        Log.info(f'gathering users belonging to tenant {TENANT} => {URL}')
                    else:
                        Log.critical("please select a tenancy to gather users")
                    ctx.obj['profile'] = TENANT
                    target_org, name = MenuResults(ctx)
                    IDP = IDPclient(ctx)
                    RESULT = IDP.list_users(ctx)
                    DATA = []
                    for I in RESULT:
                        USERNAME = I['username'].ljust(50)
                        ID = I['id']
                        EMAIL = I['email'].rjust(50)
                        STRING = USERNAME + '\t' + ID + '\t' + EMAIL
                        DATA.append(STRING)
                    DATA.sort()
                    INPUT = 'User Manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        USERNAME = CHOICE.split('\t')[0].strip()
                        ID = CHOICE.split('\t')[1].strip()
                        EMAIL = CHOICE.split('\t')[2].strip() 
                        Log.info(f"adding username {USERNAME} to {name} now, please wait...")
                    else:
                        Log.critical("please select a username to continue...")
                    ROLES = ['org_owner', 'org_member'] 
                    ANS = input("5. Is this an organization owner? [y/n] ")
                    if ANS == 'Y' or ANS == 'y':
                        for user_role in ROLES:
                            OUTPUT = CSP.org_add_user(EMAIL, user_role, target_org, AUTH, PROFILE)
                            try:
                                if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
                                    Log.info(f'added user {USERNAME} to organization {name} with {user_role} permissions')
                                else:
                                    Log.critical(f'failed to add user {USERNAME} to organization {name} with {user_role} permissions')
                            except:
                                Log.json(json.dumps(OUTPUT, indent=2))
                    else:
                        user_role = 'org_member'
                        OUTPUT = CSP.org_add_user(EMAIL, user_role, target_org, AUTH, PROFILE)
                        try:
                            if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
                                Log.info(f'added user {USERNAME} to organization {name} with {user_role} permissions')
                            else:
                                Log.critical(f'failed to add user {USERNAME} to organization {name} with {user_role} permissions')
                        except:
                            Log.json(json.dumps(OUTPUT, indent=2))
                elif 'Delete SDDC' in OPTION:
                    ctx.obj['profile'] = 'operator' 
                    raw = True
                    force = True
                    AUTH, PROFILE = get_operator_context(ctx)
                    aws_ready = False
                    version_only = False
                    VMC = vmc(AUTH, PROFILE)
                    DATA = []
                    org, name = MenuResults(ctx)
                    OUTPUT = CSP.org_show_sddcs(org, aws_ready, version_only, AUTH, PROFILE, raw)
                    for I in OUTPUT:
                        ID = I['id']
                        NAME = I['name'].rjust(50)
                        STRING = ID + '\t' + NAME
                        DATA.append(STRING)
                    INPUT = 'sddc manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        SDDC_NAME = CHOICE.split('\t')[1].strip()
                        sddc_id = CHOICE.split('\t')[0]
                        if SDDC_NAME:
                            Log.info(f"deleting {SDDC_NAME} in {name} now, please wait...")
                        else:
                            Log.critical("please select an sddc-name to continue...")
                    else:
                        Log.critical("please select an sddc-name to continue...")
                    RESULT = VMC.org_sddc_delete(org, sddc_id, force, raw)
                    Log.info(json.dumps(RESULT, indent=2))
                elif 'List Orgs per User' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    IDP = idpc(PROFILE)
                    TENANTS = _get_tenants()
                    TENANTS.sort()
                    INPUT = 'Tenant Manager'
                    CHOICE = runMenu(TENANTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        TENANT = CHOICE.split('\t')[1].strip()
                        if 'VMwareFed' in TENANT:
                            TENANT = 'vmc-prod'
                        elif 'customer.local' in TENANT:
                            TENANT = 'customer-local'
                        elif 'CSP User Local' in TENANT:
                            TENANT = 'csp-user-local'
                        URL = CHOICE.split('\t')[0].strip()
                        Log.info(f'gathering users belonging to tenant {TENANT} => {URL}')
                    else:
                        Log.critical("please select a tenancy to gather users")

                    ctx.obj['profile'] = TENANT
                    IDP = IDPclient(ctx)
                    RESULT = IDP.list_users(ctx)
                    DATA = []
                    for I in RESULT:
                        USERNAME = I['username'].ljust(50)
                        ID = I['id']
                        EMAIL = I['email'].rjust(50)
                        STRING = USERNAME + '\t' + ID + '\t' + EMAIL
                        DATA.append(STRING)
                    DATA.sort()
                    INPUT = 'User Manager'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        USERNAME = CHOICE.split('\t')[0].strip()
                        ID = CHOICE.split('\t')[1].strip()
                        EMAIL = CHOICE.split('\t')[2].strip() 
                        Log.info(f"gathering username {USERNAME} orgs now, please wait...")
                    else:
                        USERNAME = input('enter username: ')
                        USERNAME.strip()

                    OUTPUT = CSP.user_list_orgs(USERNAME, AUTH, PROFILE)
                    if OUTPUT is not None:
                        for ITEM in OUTPUT:
                            AUTH, PROFILE = get_operator_context(ctx)
                            ID = f"{ITEM.split('/')[-1]}"
                            print("*******************************************************")
                            Log.info(ID)
                            print("*******************************************************")
                            OUTPUT = CSP.org_show_details(ID, AUTH, PROFILE)
                            if OUTPUT == []:
                                Log.warn('unable to find org details or org doesnt exist')
                            else:
                                try:
                                    Log.info(f'Display Name:  {OUTPUT["display_name"]}')
                                    Log.info(f'Project State: {OUTPUT["project_state"]}')
                                except:
                                    pass
                elif 'Child Tenant Details' in OPTION:
                    AUTH, PROFILE = get_platform_context(ctx)
                    TENANTS = _get_tenants()
                    TENANTS.sort()
                    INPUT = 'Parent Tenant Selection'
                    CHOICE = runMenu(TENANTS, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        PARENT = CHOICE.split('\t')[1].strip()
                        if 'VMwareFed' in PARENT:
                            PARENT = 'vmc-prod'
                        elif 'customer.local' in PARENT:
                            PARENT = 'customer-local'
                    else:
                        Log.critical("please select a parent tenancy to continue")
                    ctx.obj['profile'] = PARENT
                    IDP = IDPclient(ctx)
                    try:
                        TENANTS = IDP.list_all_tenants()
                    except:
                        Log.critical(f'unable to list child tenants for {PARENT}')
                    DATA = []
                    if TENANTS:
                        for TENANT in TENANTS:
                            NAME = TENANT['name']
                            DATA.append(NAME)
                    else:
                        Log.critical('unable to list all child tenants')
                    INPUT = 'Child Tenant Selection'
                    CHOICE = runMenu(DATA, INPUT)
                    if CHOICE:
                        CHOICE = ''.join(CHOICE)
                        TENANT = CHOICE.split('\t')[0].strip()
                    else:
                        Log.critical("please select a child tenancy to continue")
                    RESULT = IDP.list_tenant(TENANT)
                    if RESULT:
                        Log.json(json.dumps(RESULT.json(), indent=2))
                    else:
                        Log.critical(f'failure while listing tenant {TENANT}')
                wait_for_enter()
                click.clear()
        elif 'Organization Creation' in OPTION:
            CONFIG = Config('csptools')
            try:
                new_org_name = input('Enter the new organization name: ')
            except:
                Log.critical('please provide an org name to create; exiting application')
            AUTH, PROFILE = get_operator_context(ctx)
            ORG_ID = CSP.create_org(new_org_name, AUTH, PROFILE)
            if ORG_ID:
                Log.info(f'New Organization ID: {ORG_ID}')
                ct = datetime.datetime.now()
                ts = ct.timestamp()
                P = CONFIG.get_profile(ORG_ID)
                if P is None or P['config'] == {}:
                    Log.info(f"Profile {ORG_ID} not found; creating a new profile")
                    CONFIG.create_profile(ORG_ID)
                    CONFIG.update_config(new_org_name, "org_name", ORG_ID)
                else:
                    CONFIG.update_config(new_org_name, "org_name", ORG_ID)
            else:
                Log.critical(f'Unable to create organization name: {new_org_name}')
              
            OUTPUT = CSP.show_oauth_service_definition_id(ORG_ID, AUTH, PROFILE, raw)
            for ITEM in OUTPUT:
                for I in ITEM:
                    SERVICE_ID = I['serviceDefinitionId']

            # switch to platform user to add to service-id
            AUTH, PROFILE = get_platform_context(ctx)
            RESULT = CSP.add_to_service_id(ORG_ID, SERVICE_ID, AUTH, PROFILE)
            if RESULT:
                Log.info(f'successfully added the new organization to service ID: {SERVICE_ID}')

            # trigger SS-Backend to import the Org from CSP
            OUTPUT = CSP.trigger_ss_backend(ctx.obj['operator'], 'operator')
            if OUTPUT:
                Log.info('triggered SS-backend to import the new organization from CSP successfully')

            RESULT = CSP.org_default_properties(ORG_ID, ctx.obj['operator'], 'operator')
            if RESULT:
                Log.info('organization default properties added:')
                Log.json(json.dumps(RESULT, indent=2))
                CONFIG.update_config(RESULT, "default_values", ORG_ID)

            if set:
                org_type = set
                RESULT = CSP.org_set_type(ORG_ID, org_type, ctx.obj['operator'], 'operator')
                if RESULT:
                    Log.info(f'organization type set to {org_type}:')
                    Log.json(json.dumps(RESULT, indent=2))

            user_name = os.environ['LOGNAME'].split('@')[0] + '@vmwarefed.com'
            AUTH, PROFILE = get_platform_context(ctx)
            OUTPUT = CSP.org_user_to_admin(SERVICE_ID, user_name, ORG_ID, 'vmc-full', AUTH, PROFILE)
            if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
                Log.info(f'vmc-full admin rights assigned to user {user_name} for {new_org_name}')
            else:
                Log.critical('failed to assign admin rights')
        elif 'User Creation' in OPTION:
            AUTH, PROFILE = get_platform_context(ctx)
            TENANTS = _get_tenants()
            TENANTS.sort()
            INPUT = 'Tenant Manager'
            CHOICE = runMenu(TENANTS, INPUT)
            if CHOICE:
                CHOICE = ''.join(CHOICE)
                tenant = CHOICE.split('\t')[1].strip()
                url = CHOICE.split('\t')[0].strip()
                Log.info(f'adding new users to tenant {tenant} => {url}')
            else:
                Log.critical("please select a tenancy to add users to")

            TARGET_ORG, TARGET_NAME = MenuResults(ctx)
            print()
            print("*****************************************************************************")
            print(f"Tenant            => {tenant}")
            print(f"URL               => {url}")
            print(f"Organization Name => {TARGET_NAME}")
            print(f"Organization ID   => {TARGET_ORG}")
            print("*****************************************************************************")
            print()

            ANS = 'Y'
            while ANS == 'Y':
                try:
                    firstname = input("1. Enter new user firstname: ")
                    lastname = input("2. Enter new user lastname: ")
                    email = input("3. Enter new user email address: ")
                    initial = [*firstname][0]
                    tryusername = lastname.lower().strip() + initial.lower().strip()
                    username = input("4. Enter new username [" + tryusername + "]: ")
                except:
                    Log.critical('encountered an error while capturing new user information; exiting')
                if not username:
                    username = tryusername.strip()
                    tenant_email = username + '@' + tenant
                else:
                    tenant_email = username + '@' + tenant
                if '.' not in username:
                    print()
                    Log.info(f'running add user on username: {username}')
                else:
                    Log.critical('please provide a username without a "." in it')
                CONFIG = Config('idptools')
                if 'customer.local' in tenant:
                    ctx.obj['profile'] = 'customer-local'
                    PROFILE = CONFIG.get_profile('customer-local')
                elif 'VMwareFed' in TENANT:
                    ctx.obj['profile'] = 'vmc-prod'
                    PROFILE = CONFIG.get_profile('vmc-prod')
                else:
                    ctx.obj['profile'] = tenant
                    PROFILE = CONFIG.get_profile(tenant)
                ctx.obj['url'] = url
                ALL = PROFILE['config']
                for I in ALL:
                    client_id = ALL[I]['client-id']
                    secret = ALL[I]['client-secret']
                    if client_id and secret:
                        ctx.obj['client-id'] = client_id
                        ctx.obj['client-secret'] = secret
                        break
                IDP = IDPclient(ctx)
                CHK = IDP.getUserID(username)
                if CHK:
                    Log.warn(f'username {username} already exists in tenant: {tenant}')
                    Log.info('please try again using an alternate username')
                else:
                    print()
                    print("*****************************************************************************")
                    print(f"Tenant        => {tenant}")
                    print(f"First Name    => {firstname}")
                    print(f"Last Name     => {lastname}")
                    print(f"Email Address => {email}")
                    print(f"Username      => {username}")
                    print(f"Tenant Email  => {tenant_email}")
                    print("*****************************************************************************")
                    try:
                        wait_for_enter()
                    except:
                        Log.critical('breaking from script due to an unknown interrupt')
                    OTA_LINK = IDP.add_user(username, firstname, lastname, tenant_email, tenant)
                    if OTA_LINK:
                        try:
                            CONFIG.update_config(OTA_LINK, f"ota-link-{username}", TARGET_ORG)
                        except:
                            Log.info(f'{TARGET_ORG} is not saved in the configstore for user: ' + os.environ['LOGNAME'])
                    ROLES = ['org_owner', 'org_member'] 
                    ANS = input("5. Is this an organization owner? [y/n] ")
                    AUTH, PROFILE = get_platform_context(ctx)
                    if ANS == 'Y' or ANS == 'y':
                        for user_role in ROLES:
                            OUTPUT = CSP.org_add_user(tenant_email, user_role, TARGET_ORG, AUTH, PROFILE)
                            try:
                                if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
                                    Log.info(f'added user {tenant_email} to organization {TARGET_NAME} with {user_role} permissions')
                                else:
                                    Log.critical(f'failed to add user {tenant_email} to organization {TARGET_NAME} with {user_role} permissions')
                            except:
                                Log.json(json.dumps(OUTPUT, indent=2))
                    else:
                        user_role = 'org_member'
                        OUTPUT = CSP.org_add_user(tenant_email, user_role, TARGET_ORG, AUTH, PROFILE)
                        try:
                            if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
                                Log.info(f'added user {tenant_email} to organization {TARGET_NAME} with {user_role} permissions')
                            else:
                                Log.critical(f'failed to add user {tenant_email} to organization {TARGET_NAME} with {user_role} permissions')
                        except:
                            Log.json(json.dumps(OUTPUT, indent=2))
                    OUTPUT = CSP.show_oauth_service_definition_id(TARGET_ORG, AUTH, PROFILE, raw)
                    for ITEM in OUTPUT:
                        for I in ITEM:
                            SERVICE_ID = I['serviceDefinitionId']
                    OUTPUT = CSP.org_user_to_admin(SERVICE_ID, tenant_email, TARGET_ORG, 'vmc-full', AUTH, PROFILE)
                    try:
                        if OUTPUT.status_code == 200 or OUTPUT.status_code == 202:
                            Log.info(f'vmc-full admin rights assigned to user {tenant_email} for {TARGET_ORG}')
                        else:
                            Log.critical('failed to assign admin rights')
                    except:
                        Log.json(json.dumps(OUTPUT, indent=2))
                    OUTPUT = CSP.user_list_roles(tenant_email, TARGET_ORG, AUTH, PROFILE)
                    if OUTPUT:
                        Log.json(json.dumps(OUTPUT, indent=2))
                    subject = 'VMC on GovCloud'
                    body = setup_body(firstname, OTA_LINK, username)
                    body = MIMEText(body, "html")
                    message = MIMEMultipart("alternative")
                    message["Subject"] = subject
                    message["From"] = 'vmc-govcloud-ops@vmware.com'
                    message["To"] = email
                    message.attach(body)
                    Log.info(f"sending email to registered user {username} for account activation")
                    send_email(email, 'vmc-govcloud-ops@vmware.com', message.as_string())
                ANS = input('\nWould you like to continue adding another user? [y/n]: ')
                ANS = ANS.upper()
        elif 'Update Ticket' in OPTION:
            TARGET_ORG, TARGET_NAME = MenuResults(ctx)
            TICKET = setup_project('CSSD', TARGET_NAME.strip(), profile='default')
            if not TICKET:
                TICKET = input('Enter ticket key: ')
            USERNAME = os.environ["LOGNAME"].split("@")[0]
            PROFILE = get_user_profile_based_on_key(TICKET)
            TICKET = (TICKET,)
            RESULT = global_assign(TICKET, USERNAME, PROFILE)
            COMMENT = f'organization creation is complete for org {TARGET_ORG} and all necessary users have been created.'
            RESULT = comment(TICKET, COMMENT, PROFILE)
            if RESULT:
                Log.info(f'ticket commented successfully')
        elif 'Update Organization' in OPTION:
            CONFIG = Config('csptools')
            TARGET_ORG, TARGET_NAME = MenuResults(ctx)
            AUTH, PROFILE = get_operator_context(ctx)
            SID = CONFIG.get_var('sdpSid', 'metadata', 'SID', TARGET_ORG)
            OUTPUT = CSP.update_sid(SID, TARGET_ORG, AUTH, PROFILE)
            if OUTPUT:
                Log.json(json.dumps(OUTPUT, indent=2))
            else:
                Log.critical('unable to update the organization sid')
        elif 'vIDM' in OPTION:
            AUTH, PROFILE = get_platform_context(ctx)
            TENANTS = _get_tenants()
            TENANTS.sort()
            INPUT = 'Parent Tenant Selection'
            CHOICE = runMenu(TENANTS, INPUT)
            if CHOICE:
                CHOICE = ''.join(CHOICE)
                PARENT = CHOICE.split('\t')[1].strip()
                if 'VMwareFed' in PARENT:
                    PARENT = 'vmc-prod'
                elif 'customer.local' in PARENT:
                    PARENT = 'customer-local'
                else:
                    Log.critical("please select a parent tenancy to continue")
            ctx.obj['profile'] = PARENT
            IDP = IDPclient(ctx)
            TARGET_ORG, TENANT = MenuResults(ctx)
            RESULT = IDP.add_tenant(TENANT, 'PAID')
            if RESULT:
                Log.json(json.dumps(RESULT.json(), indent=2))
            else:
                Log.warn(f'failure while creating tenant {TENANT}')
            RESULT = IDP.add_admin(username='ops_admin', email='vmc-public-sector-sre@vmware.com', tenant=TENANT)
            Log.json(json.dumps(RESULT, indent=2))
            try:
                filename = '/tmp/otaLink_' + TENANT + '_' + 'ops_admin'
                otaLink = RESULT["userAuthorizationData"]
                f = open(filename, "w+")
                f.write(otaLink)
                f.close
                Log.info('tenant otaLink file is created: ' + filename)
            except:
                Log.warn('Failed to create otaLink file: ' + filename)
            RESULT = IDP.add_admin(username='tenant_admin', email='vmc-public-sector-sre@vmware.com', tenant=TENANT)
            Log.json(json.dumps(RESULT, indent=2))
            try:
                filename = '/tmp/otaLink_' + TENANT + '_' + 'tenant_admin'
                otaLink = RESULT["userAuthorizationData"]
                f = open(filename, "w+")
                f.write(otaLink)
                f.close
                Log.info('tenant otaLink file is created: ' + filename)
            except:
                Log.warn('Failed to create otaLink file: ' + filename)
        if 'Return' not in OPTION:
            wait_for_enter()
            click.clear()

def send_email(receiver, sender, msg):
    import smtplib
    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(sender, receiver, msg)

def setup_body(firstname, activation_url, username):
    html = f"""\
    <html>
<body>
<br>
<br>
Hi {firstname},
<br>
<br>
Please use the link below to activate your VMC on GovCloud account and set your password. This link expires in 7 days.
<br>
<b> {activation_url} </b>
<br>
<br>
After you set your password at the above link, access the VMC on GovCloud console to login, here:<b> https://console.cloud-us-gov.vmware.com/ </b>
<br>
<br>
Your username to login to the VMC console is: {username}[at]customer.local
<br>
NOTE: ('[at]' should be replaced with '@')
<br>
Regards,
VMC GovCloud Operations
</body>
</html>
"""
    return html

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace("{","").replace("}","")

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'VMC Menu: {INPUT}'
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

def wait_with_message(seconds):
    while True:
        Log.info(f"sleeping for {seconds} seconds, please wait...")
        time.sleep(30)
        seconds = seconds - 30
        if seconds <= 0:
            Log.info("FINISHED")
            break
    return True

def wait_for_enter():
    time.sleep(2)
    print()
    return input('press ENTER to continue: ')

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

def _get_tenants(filter_definition=None):
    CONFIG = Config('csptools')
    PROFILE = CONFIG.get_profile('platform')
    ALL_ORGS = PROFILE['config']
    for ORG_ID in ALL_ORGS:
        AUTH = ORG_ID
        if AUTH:
            break
    IDP = idpc('platform')
    DATA = IDP.get_tenant_names(filter_definition, AUTH)
    return DATA

def convertTuple(tup):
    # initialize an empty string
    str = ''
    for item in tup:
        str = str + item
    return str

def setup_project(project, summary, profile='default'):
    # default to project tuple
    project = (project,)
    # default to logname
    #assignee = (os.environ["LOGNAME"].split("@")[0],)
    # default to descending order
    ascending = False
    descending = True
    # turn on the wizard
    wizard = True
    # set all of these to None
    orderby = jql = key = limit = csv = json =  None
    # these need to be tuples
    assignee = group = reporter = status = description = ()
    summary = (summary,)
    ISSUES, JQL = search_issues(jql, project, key, assignee, group, reporter, status, summary, description, limit, orderby, ascending, descending, profile)
    TOTAL, ISSUES = _dictionarify(ISSUES, csv, json, wizard, profile)
    CHOICE = jiraRunMenu(ISSUES, JQL)
    if CHOICE is not None:
        if CHOICE[0]:
            key = CHOICE[0].strip()
    return key

def _dictionarify(issues, csv, json, wizard, user_profile=None):
    TOTAL = 0
    if user_profile is None:
        try:
            JIRA_SESSION, user_profile = get_jira_session_based_on_key(str(issues[0].key))
        except Exception as e:
            Log.critical('invalid JQL query or the search failed')
    ISSUES = []
    for ISSUE in issues:
        TOTAL = TOTAL + 1
        ISSUE_DICT = {}
        ISSUE_DICT['key'] = str(ISSUE.key)
        ISSUE_DICT['status'] = str(ISSUE.fields.status)
        ISSUE_DICT['assignee'] = str(ISSUE.fields.assignee)
        ISSUE_DICT['reporter'] = str(ISSUE.fields.reporter)
        ISSUE_DICT['summary'] = str(ISSUE.fields.summary)
        if not csv and not json and not wizard:
            ISSUE_DICT['launcher'] = create_link(build_url(str(ISSUE.key), user_profile), str(ISSUE.key))
        elif wizard:
            ISSUE_DICT.pop('assignee')
            ISSUE_DICT.pop('reporter')
        else:
            ISSUE_DICT['launcher'] = build_url(str(ISSUE.key), user_profile)
        ISSUES.append(ISSUE_DICT)
    return TOTAL, ISSUES
