import unittest
from csptools import cspclient
from csptools import csp_org

class TestAddMethods(unittest.TestCase):

    global CSP
    global DEFAULT_OPERATOR_REFRESH_TOKEN
    global OPERATOR_ORG_ID
    CSP = cspclient.CSPclient()
    DEFAULT_OPERATOR_REFRESH_TOKEN = CSP.get_org_refresh_token(org_name='operator')
    if DEFAULT_OPERATOR_REFRESH_TOKEN is None:
        print("ERROR: please ensure your cspclient has been configured with a default profile and credentials for the operator org before running the test")
    OPERATOR_ORG_ID = CSP.find_org_id('operator')

    # csp_auth tests

    def test_auth_get_refresh_token(self):
        RESULT = CSP.get_org_refresh_token(org_name='operator')
        self.assertIsNotNone(RESULT)
        return RESULT

    def test_auth_refresh_token_convert(self):
        RESULT = CSP.generate_access_token(DEFAULT_OPERATOR_REFRESH_TOKEN)
        self.assertIsNotNone(RESULT)

    def test_auth_org_setup(self):
        RESULT = CSP.setup_org_access(org_name='operator', refresh_token=DEFAULT_OPERATOR_REFRESH_TOKEN, overwrite=True)
        self.assertTrue(RESULT)

    def test_auth_check_token_age(self):
        RESULT = CSP.get_org_access_token_age(org_name='operator')
        try:
            float(RESULT)
            RESULT = True
        except:
            RESULT = False
        self.assertTrue(RESULT)

    def test_auth_lookup_org_id(self):
        RESULT = CSP.find_org_id('operator')
        self.assertIsNotNone(RESULT)
        return RESULT

    def test_auth_lookup_org_name(self):
        RESULT = CSP.find_org_name(OPERATOR_ORG_ID)
        self.assertIsNotNone(RESULT)

    # csp_org tests

    def test_org_methods(self):
        NEW_TEST_ORG = CSP.create_org('test', 'operator')
        self.assertIsNotNone(NEW_TEST_ORG)
        RESULT = CSP.org_property_list('operator', 'operator')
        self.assertIsNotNone(RESULT)
        RESULT = CSP.rename_org(NEW_TEST_ORG, 'renamed_test', 'operator')
        self.assertIsNotNone(RESULT)
        RESULT = CSP.delete_org(NEW_TEST_ORG, 'operator')
        self.assertIsNotNone(RESULT)

    # csp_user tests

    #def test_user_methods(self):
    #    pass

if __name__ == '__main__':
    unittest.main()