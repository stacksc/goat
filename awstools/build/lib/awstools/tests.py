import unittest
from awstools import iam_nongc
from awstools import ec2
from awstools import s3
from awstools import rds
from pathlib import Path
from os import mkdir, remove, rmdir

class TestAddMethods(unittest.TestCase):

    # iam tests

    def test_iam_authenticate(self):
        RESULT = iam_nongc._authenticate('default')
        self.assertIsNotNone(RESULT)

    def test_iam_assume_role(self):
        SESSION, KEY_ID, ACCESS_TOKEN, SESSION_TOKEN = iam_nongc._assume_role(aws_profile_name='vmcdelta')
        self.assertIsNotNone(SESSION)

    # ec2 tests

    def test_ec2_refresh(self):
        RESULT = ec2._refresh('all', 'vmcdelta')
        self.assertTrue(RESULT)

    def test_ec2_show(self):
        RESULT = ec2._show('all', 'vmcdelta', True)
        self.assertTrue(RESULT)

    # s3 tests

    def test_s3_refresh(self):
        RESULT = s3._refresh('vmcdelta')
        self.assertTrue(RESULT)

    def test_s3_show_buckets(self):
        RESULT = s3._show('buckets', 'vmcdelta')
        self.assertTrue(RESULT)

    # disabled for now due to some issue with perms affecting pyps and vmcgov
    #def test_s3_bucket_management(self):
        #RESULTS = []
        #RESULTS.append(s3._create('default', 'pyps_pipeline_test')) 
        #Path("test").touch()
        #RESULTS.append(s3._upload('default', 'test', 'pyps_pipeline_test'))
        #RESULTS.append(s3._show('bucket_files', 'default', 'pyps_pipeline_test'))
        #mkdir('download_test')
        #RESULTS.append(s3._download('default', 'pyps_pipeline_test', 'download_test'))
        #RESULTS.append(s3._delete('pyps_pipeline_test', 'default'))
        #remove('test')
        #rmdir('download_test')
        #for RESULT in RESULTS:
        #    self.assertTrue(RESULT)

    # rds tests

    def test_rds_refresh(self):
        RESULT = rds._refresh('cached_rds_instances', 'vmcdelta')
        self.assertTrue(RESULT)

if __name__ == '__main__':
    unittest.main()
