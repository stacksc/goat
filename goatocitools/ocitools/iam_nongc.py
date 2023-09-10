import click, string, random, subprocess, oci, os
from .oci_config import OCIconfig
from toolbox.logger import Log
from os import environ, chmod, stat
from configstore.configstore import Config
from toolbox.misc import set_terminal_width

CONFIG = OCIconfig()
STORE = Config('ocitools')

@click.command(help='login using existing IAM creds or add new creds to config', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.option('-r', '--region', 'region', help='oci region to connect to', required=False, default='us-ashburn-1')
@click.option('-t', '--tenant', 'tenant', help='tenant ocid to connect to', required=False, default=None)
@click.option('-u', '--user', 'user', help='user ocid to connect with', required=False, default=None)
@click.option('-k', '--keyfile', 'keyfile', help='user oci API private key file to connect with', required=False, default="~/.oci/oci_api_key.pem")
@click.option('-f', '--fingerprint', 'fingerprint', help='fingerprint of oci private key to connect with', required=False, default=None)
@click.option('-p', '--profile', 'profile', help='oci profile to connect with', required=False, default='default')
@click.pass_context
def authenticate(ctx, region, tenant, user, keyfile, fingerprint, profile):
    if profile is None:
        profile_name = ctx.obj['PROFILE']
    else:
        profile_name = profile
    RESULT = _authenticate(tenant, user, fingerprint, keyfile, profile_name, region)
    if RESULT is None:
        MSG = 'setup failed. please verify supplied credentials and try again. settings were not saved'
        LINK = 'https://github.com/stacksc/goat'
        CMD = None
        SUBTITLE = 'CRITICAL'
        TITLE = 'GOAT'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        Log.critical(MSG)
    else:
        Log.info("credentials saved successfully")
        if profile_name not in STORE.PROFILES:
            STORE.create_profile(profile_name)
        # update metadata facts
        try:
            STORE.update_metadata(fingerprint, 'fingerprint', profile_name, True)
            STORE.update_metadata(keyfile, 'key_file', profile_name, True)
            STORE.update_metadata(tenant, 'tenancy', profile_name, True)
            STORE.update_metadata(region, 'region', profile_name, True)
            STORE.update_metadata(user, 'user', profile_name, True)
        except:
            Log.critical('unable to update the configstore with OCI information')
        Log.info(f"you can now use your new profile with 'oci --profile {profile_name}")
        MSG = f'{profile_name} credentials saved successfully!'
        LINK = None
        CMD = None
        SUBTITLE = 'INFO'
        TITLE = 'GOAT'
        Log.notify(MSG, TITLE, SUBTITLE, LINK, CMD)
        cache_all_hack(profile_name, region)
        update_latest_profile(profile_name)

# worker function to make the method portable
def _authenticate(tenant, user, fingerprint, keyfile, profile_name, region='us-ashburn-1'):
    SESSION = None
    try:
        SESSION = oci.config.from_file("~/.oci/config", profile_name)
    except:
        pass
    if SESSION is not None:
        CONFIG.add_oci_profile(tenant, user, region, fingerprint, keyfile, profile_name)
    else:
        CONFIG.add_oci_profile(tenant, user, region, fingerprint, keyfile, profile_name)
    # try again
    try:
        SESSION = oci.config.from_file("~/.oci/config", profile_name)
    except:
        Log.warn('unable to load the new config file')
        return None
    return SESSION

def update_latest_profile(profile_name):
    BASICS = Config('ocitools')
    LATEST = BASICS.get_profile('latest')
    if LATEST is None:
        BASICS.create_profile('latest')
        BASICS.update_config(profile_name, 'name', 'latest')
    else:
        BASICS.update_config(profile_name, 'name', 'latest')

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "")

def force_cache(profile_name, region):
    CONFIG = Config('ocitools')
    Log.info('oci profile caching initialized')
    MODULES = ['oss', 'compute', 'dbs', 'regions', 'vault', 'secrets', 'compartment', 'keys']
    for MODULE in MODULES:
        if MODULE == 'secrets' or MODULE == 'keys':
            os.system(f'goat oci -r {region} -p {profile_name} vault {MODULE} refresh')
        else:
            Log.info(f'caching {MODULE} data...')
            try:
                os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            except:
                pass

def cache_all_hack(profile_name, region):
    CONFIG = Config('ocitools')
    Log.info('oci profile caching initialized')
    MODULES = ['oss', 'compute', 'dbs', 'regions', 'vault', 'secrets', 'compartment', 'keys']
    for MODULE in MODULES:
        if MODULE == 'oss':
            CACHED = {}
            FOUND = False
            try:
                CACHED.update(CONFIG.get_metadata('cached_buckets', profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'vault':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_vaults', profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'compartment':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_compartments', profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'secrets':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_secrets', profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} vault {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} vault {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'keys':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_keys', profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} vault {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} vault {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'regions':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_regions', profile_name))
            except:
                pass
            if not CACHED: 
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'compute':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.get_metadata('cached_instances', profile_name))
            except:
                pass
            if not CACHED:
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')
        elif MODULE == 'dbs':
            FOUND = False
            CACHED = {}
            try:
                CACHED.update(CONFIG.PROFILES[profile_name]['metadata']['cached_dbs_instances'])
            except:
                pass
            if not CACHED:
                Log.info(f'caching {MODULE} data...')
                try:
                    os.system(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
                except:
                    pass
            elif CACHED:
                for REGION in CACHED:
                    if region == REGION:
                        FOUND = True
                        break
                if FOUND is False:
                    Log.info(f'caching {MODULE} data...')
                    run_command(f'goat oci -r {region} -p {profile_name} {MODULE} refresh')
            else:
                Log.info(f'cache exists for {MODULE} data...')

def run_command(command):
    PROC = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

