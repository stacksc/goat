from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .aws_config import AWSconfig
from . import iam_nongc
from . import iam_ingc
import datetime
from tabulate import tabulate

CONFIGSTORE = Config('awstools')

class EC2client():

    def __init__(self, aws_profile_name, aws_region='us-gov-west-1', in_boundary=True, cache_only=False):
        self.CONFIG = AWSconfig()
        self.CONFIGSTORE = Config('awstools')
        self.CACHE_UPDATE_INTERVAL = 60*60*24*7 # update cache every week
        self.AWS_PROFILE = aws_profile_name
        self.AWS_REGION = aws_region
        self.INB = in_boundary
        self.CACHE_ONLY = cache_only
        if not self.CACHE_ONLY:
            self.get_session()

    def get_session(self):
        Log.info(f"connecting to EC2 as {self.AWS_PROFILE} via {self.AWS_REGION}...")
        if detect_environment() == 'non-gc':
            if self.CONFIG.profile_or_role(self.AWS_PROFILE):
                self.SESSION = iam_nongc._authenticate(self.AWS_PROFILE, self.AWS_REGION)
            else:
                self.SESSION = iam_nongc._assume_role(aws_profile_name=self.AWS_PROFILE)[0]
        else:    
            MINS = iam_ingc.check_time(self.AWS_PROFILE)
            if MINS >= 60 or MINS is False:
                Log.info(f"reauthentication running against IDP due to session timeout")
                IDP_URL = CONFIGSTORE.get_config('IDP_URL', 'IDP')
                RESULT, self.AWS_PROFILE = iam_ingc._authenticate(IDP_URL, aws_region=self.AWS_REGION, aws_output='json', aws_profile_name=self.AWS_PROFILE, menu=False)
                if RESULT is not None:
                    ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_access_key_id', 'string', 'aws_access_key_id', self.AWS_PROFILE)
                    SECRET_ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_secret_access_key', 'string', 'aws_secret_access_key', self.AWS_PROFILE)
                    TOKEN = self.CONFIG.get_from_config('creds', 'aws_session_token', 'string', 'aws_session_token', self.AWS_PROFILE)
                    self.SESSION = iam_ingc.get_role_session(ACCESS_KEY, SECRET_ACCESS_KEY, TOKEN)
            else:
                Log.info(f"session held with {MINS} minutes since authentication")
                ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_access_key_id', 'string', 'aws_access_key_id', self.AWS_PROFILE)
                SECRET_ACCESS_KEY = self.CONFIG.get_from_config('creds', 'aws_secret_access_key', 'string', 'aws_secret_access_key', self.AWS_PROFILE)
                TOKEN = self.CONFIG.get_from_config('creds', 'aws_session_token', 'string', 'aws_session_token', self.AWS_PROFILE)
                self.SESSION = iam_ingc.get_role_session(ACCESS_KEY, SECRET_ACCESS_KEY, TOKEN)
        return self.SESSION

    def auto_refresh(self, aws_profile_name='default'):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:
            INSTANCES_TS = self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_instances']['last_cache_update']
        except KeyError:
            INSTANCES_TS = 0
        if TIME_NOW - float(INSTANCES_TS) > self.CACHE_UPDATE_INTERVAL:
            self.cache_instances(aws_profile_name)
        try: 
            IPS_TS = self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_public_ips']['last_cache_update']
        except KeyError:
            IPS_TS = 0
        if TIME_NOW - float(IPS_TS) > self.CACHE_UPDATE_INTERVAL:
            self.cache_public_ips(aws_profile_name)
        try:
            REGIONS_TS = self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_regions']['last_cache_update']
        except KeyError:
            REGIONS_TS = 0
        if TIME_NOW - float(REGIONS_TS) > self.CACHE_UPDATE_INTERVAL:
            self.cache_regions(aws_profile_name)
        self.CONFIGSTORE = Config('awstools')

    def refresh(self, aws_profile_name='default'):
        self.cache_instances(aws_profile_name)
        self.cache_public_ips(aws_profile_name)
        self.cache_regions(aws_profile_name)

    def cache_instances(self, aws_profile_name='default'):
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(aws_profile_name)
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
            self.get_session()
        CLIENT = self.SESSION.client('ec2')
        Log.info("caching ec2 instances...")
        INSTANCES = self.get_instances(CLIENT)
        INSTANCES_CACHE = {}
        for INSTANCE in INSTANCES:
            INSTANCE_NAME = None
            for INDEX in range(len(INSTANCE['Tags'])):
                if INSTANCE['Tags'][INDEX]['Key'] == 'Name':
                    INSTANCE_NAME = INSTANCE['Tags'][INDEX]['Value']
            if INSTANCE_NAME is None:
                INSTANCE_NAME = INSTANCE['InstanceId']
            INSTANCE_DICT = {
                'ImageId': INSTANCE['ImageId'],
                'InstanceId': INSTANCE['InstanceId'],
                'InstanceType': INSTANCE['InstanceType'],
                'PrivateDnsName': INSTANCE['PrivateDnsName'],
                'PrivateIpAddress': INSTANCE['PrivateIpAddress'],
            }
            INSTANCES_CACHE[INSTANCE_NAME] = INSTANCE_DICT
        INSTANCES_CACHE['last_cache_update'] = TIMESTAMP
        self.CONFIGSTORE.update_metadata(INSTANCES_CACHE, 'cached_instances', aws_profile_name, True)
        self.CONFIGSTORE = Config('awstools')
    
    def get_instances(self, EC2):
        RESULT = EC2.describe_instances(
            Filters = [
                {
                    'Name': 'instance-state-name',
                    'Values': ['running'] 
                },
                {
                    'Name': 'tag:Name',
                    'Values': ['*']
                }
            ]
        )
        INSTANCES = []
        RESERVATIONS = RESULT['Reservations']
        for INDEX in range(len(RESERVATIONS)):
            RESERVATION = RESERVATIONS[INDEX]
            INSTANCE_LIST = RESERVATION['Instances']
            for INSTANCE in INSTANCE_LIST:
                INSTANCES.append(INSTANCE)
        return INSTANCES

    def cache_public_ips(self, aws_profile_name='default'):
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(aws_profile_name)
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
            self.get_session()
        CLIENT = self.SESSION.client('ec2')
        Log.info("caching ec2 public ips...")
        IPS = CLIENT.describe_addresses()
        IPS_CACHE = {}
        for IP in IPS['Addresses']:
            IP_ADDRESS = IP['PublicIp']
            if 'PrivateIpAddress' in IP:
                IP_PRIVATE = IP['PrivateIpAddress'],
            else:
                IP_PRIVATE = ""
            IP_DICT = {
                'Domain': IP['Domain'],
                'PrivateIpAddress': IP_PRIVATE,
                'NetworkBorderGroup': IP['NetworkBorderGroup']
            }
            IPS_CACHE[IP_ADDRESS] = IP_DICT
        IPS_CACHE['last_cache_update'] = TIMESTAMP
        self.CONFIGSTORE.update_metadata(IPS_CACHE, 'cached_public_ips', aws_profile_name, True)
        self.CONFIGSTORE = Config('awstools')

    def cache_regions(self, aws_profile_name='default'):
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(aws_profile_name)
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
            self.get_session()
        CLIENT = self.SESSION.client('ec2')
        Log.info("caching ec2 regions...")
        REGIONS = CLIENT.describe_regions()
        REGIONS_CACHE = {}
        for REGION in REGIONS['Regions']:
            REGION_NAME = REGION['RegionName']
            REGION_DICT = {
                'Endpoint': REGION['Endpoint'],
                'OptInStatus': REGION['OptInStatus']
            }
            REGIONS_CACHE[REGION_NAME] = REGION_DICT
        REGIONS_CACHE['last_cache_update'] = TIMESTAMP
        self.CONFIGSTORE.update_metadata(REGIONS_CACHE, 'cached_regions', aws_profile_name, True)
        self.CONFIGSTORE = Config('awstools')

    def show_cache(self, aws_profile_name, type, display):
        self.auto_refresh(aws_profile_name)
        DATA = []
        for ENTRY in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type]:
            DATA_ENTRY = {}
            if ENTRY != 'last_cache_update':
                DATA_ENTRY['Name/ID'] = ENTRY
                for PROPERTY in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type][ENTRY]:
                    DATA_ENTRY[PROPERTY] = self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata'][type][ENTRY][PROPERTY]
                DATA.append(DATA_ENTRY)
        if DATA != []:
            if display is True:
                Log.info(f"{type}\n{tabulate(DATA, headers='keys', tablefmt='rst')}\n")
            return DATA

    def show_all_cache(self, aws_profile_name):
        self.show_cache(aws_profile_name, 'cached_instances', display=False)
        self.show_cache(aws_profile_name, 'cached_public_ips', display=False)
        self.show_cache(aws_profile_name, 'cached_regions', display=False)
