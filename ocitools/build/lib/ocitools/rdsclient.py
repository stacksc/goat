from toolbox.logger import Log
from toolbox.misc import detect_environment
from configstore.configstore import Config
from .aws_config import AWSconfig
from . import iam_nongc
from . import iam_ingc
import datetime
from tabulate import tabulate

CONFIGSTORE = Config('awstools')

class RDSclient():

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
        Log.info(f"connecting to RDS as {self.AWS_PROFILE} via {self.AWS_REGION}...")
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

    def show_rds_instances(self, aws_profile_name):
        CACHE = self.get_cached_rds_instances(aws_profile_name)
        if CACHE is not None:
            return CACHE
        RDS_INSTANCES = self.get_rds_instances()
        if RDS_INSTANCES != {}:
            self.cache_rds_instances(RDS_INSTANCES, aws_profile_name)
        return RDS_INSTANCES

    def describe(self, database):
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
            self.get_session()
        CLIENT = self.SESSION.client('rds')
        RESPONSE = CLIENT.describe_db_instances(DBInstanceIdentifier=database)
        return RESPONSE

    def get_rds_instances(self):
        C=0
        if self.CACHE_ONLY and hasattr(self, 'SESSION') is False:
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
                return self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances']
        else:
            return None

    def cache_rds_instances(self, instances, aws_profile_name):
        TIMESTAMP = str(datetime.datetime.now().timestamp())
        if aws_profile_name not in self.CONFIGSTORE.PROFILES:
            self.CONFIGSTORE.create_profile(aws_profile_name)
        if 'cached_rds_instances' not in self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']:
            self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'] = {}
            print(self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'])
        self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances'] = instances
        self.CONFIGSTORE.PROFILES[aws_profile_name]['metadata']['cached_rds_instances']['last_cache_update'] = TIMESTAMP
        self.CONFIGSTORE.update_profile(self.CONFIGSTORE.PROFILES[aws_profile_name])

    def refresh(self, type, aws_profile_name):
        if type == 'cached_rds_instances':
            Log.info("caching rds instances...")
            RDS_INSTANCES = self.get_rds_instances()
            self.cache_rds_instances(RDS_INSTANCES, aws_profile_name)
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

    #def start_maintenance(self):
    #    CLIENT = self.SESSION.client('rds')


'''
        elif action == "apply-maintenance":
            if args.force:
                myargs = ' --force'
            else:
                myargs = ''
            if args.arn:
                cmd = config.base + '/modules/rds/rds_tasks.sh --apply-maintenance --resource-instance %s %s' %(arn, myargs)
            else:
                cmd = config.base + '/modules/rds/rds_tasks.sh --apply-maintenance %s' %(myargs)
            os.system(cmd)
'''                
        
