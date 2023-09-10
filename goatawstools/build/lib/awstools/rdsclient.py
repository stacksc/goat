from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .aws_config import AWSconfig
from . import iam_nongc
import datetime
from tabulate import tabulate

CONFIGSTORE = Config('awstools')

class RDSclient():

    def __init__(self, aws_profile_name, aws_region='us-east-1', in_boundary=True, cache_only=False):
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
        if detect_environment() == 'non-gc':
            if self.CONFIG.profile_or_role(self.AWS_PROFILE):
                self.SESSION = iam_nongc._authenticate(self.AWS_PROFILE, self.AWS_REGION)
            else:
                self.SESSION = iam_nongc._assume_role(aws_profile_name=self.AWS_PROFILE)[0]
        return self.SESSION

    def show_rds_instances(self, aws_profile_name):
        CACHE = self.get_cached_rds_instances(aws_profile_name)
        if CACHE is not None:
            return CACHE
        RDS_INSTANCES = self.get_rds_instances()
        if RDS_INSTANCES != {}:
            self.cache_rds_instances(RDS_INSTANCES, aws_profile_name)
        return RDS_INSTANCES

    def describe(self, database):
        self.get_session()
        CLIENT = self.SESSION.client('rds')
        RESPONSE = CLIENT.describe_db_instances(DBInstanceIdentifier=database)
        return RESPONSE

    def get_rds_instances(self):
        C=0
        self.get_session()
        CLIENT = self.SESSION.client('rds')
        RESPONSE = CLIENT.describe_db_instances()
        RDS_INSTANCES = {}
        for INSTANCE in RESPONSE['DBInstances']:
            C = C + 1
            RDS_DICT = {}
            RDS_DICT['DBInstanceArn'] = INSTANCE['DBInstanceArn']
            RDS_DICT['Engine'] = INSTANCE['Engine']
            RDS_DICT['DBInstanceStatus'] = INSTANCE['DBInstanceStatus']
            try:
                RDS_DICT['DBName'] = INSTANCE['DBName']
            except:
                RDS_DICT['DBName'] = "N/A"
            RDS_INSTANCES[INSTANCE['DBInstanceIdentifier']] = RDS_DICT
        if RDS_INSTANCES == {}:
            Log.warn('No RDS instances found in the target AWS account')
        return RDS_INSTANCES

    def get_cached_rds_instances(self, aws_profile_name):
        if aws_profile_name in self.CONFIGSTORE.PROFILES:
            if 'cached_rds_instances' in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']:
                return self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'][self.AWS_REGION]
        else:
            return None

    def cache_rds_instances(self, instances, aws_profile_name):
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(aws_profile_name)
        if 'cached_rds_instances' not in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']:
            self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'] = {}
        self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'] = instances
        self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances']['last_cache_update'] = TIMESTAMP
        self.CONFIGSTORE.update_profile(self.CONFIGSTORE.PROFILES[aws_profile_name])

    def refresh(self, type, aws_profile_name):
        if type == 'cached_rds_instances':
            Log.info("caching rds instances...")
            RDS_INSTANCES = self.get_rds_instances()
            DICT = {}
            DICT[self.AWS_REGION] = RDS_INSTANCES
            self.cache_rds_instances(DICT, aws_profile_name)
        self.CONFIGSTORE = Config('awstools')

    def auto_refresh(self, aws_profile_name):
        TIME_NOW = datetime.datetime.now().timestamp()
        try:    
            RDS_INSTANCES_TS = self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances']['last_cache_update']
        except KeyError:
            RDS_INSTANCES_TS = 0    
        if TIME_NOW - float(RDS_INSTANCES_TS) > self.CACHE_UPDATE_INTERVAL:
            Log.info('automatic refresh of rds instance cache initiated')
            self.refresh('cached_rds_instances', aws_profile_name)

    def get_region_from_profile(self, aws_profile_name):
        AWS_REGION = self.CONFIG.get_from_config('creds', 'region', profile_name=aws_profile_name)
        if AWS_REGION is None: # this is for when the user wants to use a profile which sources another profile for IAM creds
            CREDS_PROFILE = self.CONFIG.get_from_config('creds', 'source_profile', profile_name=aws_profile_name)
            AWS_REGION = self.CONFIG.get_from_config('config', 'region', profile_name=CREDS_PROFILE)
        if AWS_REGION is None:
            Log.critical("unable to get the correct region from the config")
        return AWS_REGION
