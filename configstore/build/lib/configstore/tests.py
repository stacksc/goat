import unittest
from configstore.configstore import Config

class TestAddMethods(unittest.TestCase):

    config = Config('testApp')
    #del_config = Config('delApp')

    profile_data = {
        'config': {
            'credential_test': 'test',
            'test_subconfig_property': {}
        },
        'metadata': {
            'name': 'testApp',
            'metadata_test': 'test'
        }
    }

    config_test = "test2"

    metadata_test = {
        'test1': 'test1.test.com',
        'test2': 'test2.test.com'
    }

    # cfg file methods
    #
    #

    def test_save_cfg_file(self):
        result = self.config.save_cfg_file()
        self.assertTrue(result)
    
    def test_load_cfg_file(self):
        result = self.config.load_cfg_file()
        self.assertIsNotNone(result)



    # create methods
    #
    #

    def test_create_profile(self):
        result = self.config.create_profile("testApp")
        self.assertTrue(result)

    def test_create_preset(self):
        result = self.config.create_preset(self.profile_data)
        self.assertTrue(result)


    # update methods
    #
    #

    def test_update_profile(self):
        result = self.config.update_profile(self.profile_data)
        self.assertTrue(result)

    # def test_update_preset(self):
    #     result = self.config.update_preset(self.profile_data)
    #     self.assertTrue(result)

    def test_update_config(self):
        result = self.config.update_config(self.config_test, "credential_test", "testApp")
        self.assertTrue(result)
    
    def test_update_metadata(self):
        result = self.config.update_metadata(self.metadata_test, "test_urls", "testApp")
        self.assertTrue(result)


    # get methods
    #
    #

    def test_get_profile(self):
        result = self.config.get_profile("testApp")
        self.assertIsNotNone(result)
    
    def test_get_preset(self):
        result = self.config.get_preset()
        self.assertIsNotNone(result)

    def test_get_config(self):
        result = self.config.get_config("credential_test", "testApp")
        self.assertIsNotNone(result)
    
    def test_get_metadata(self):
        result = self.config.get_metadata("metadata_test", "testApp")
        self.assertIsNotNone(result)

    

    # display method tests
    #
    #
    def test_display_configstore(self):
        result = self.config.display_configstore()
        self.assertIsNotNone(result)

    def test_display_profile(self):
        result = self.config.display_profile("testApp")
        self.assertIsNotNone(result)

    def test_display_config(self):
        result = self.config.display_config("testApp")
        self.assertIsNotNone(result)

    def test_display_metadata(self):
        result = self.config.display_metadata("testApp")
        self.assertIsNotNone(result)

    def test_display_metadata(self):
        result = self.config.display_metadata("testApp")
        self.assertIsNotNone(result)
    
    def test_verify_profile(self):
        result = self.config.verify_profile("testApp")
        self.assertIsNotNone(result)


    # delete methods
    #
    #

    # def test_initialize_del_profile(self):
        # self.del_config.create_profile('delApp')
        # self.del_config.update_profile(self.profile_data)

    # def test_clear_preset(self):
        # result = self.del_config.clear_preset()
        # self.assertTrue(result)
    
    # def test_clear_config(self):
    #     result = self.del_config.clear_config('delApp')
    #     self.assertTrue(result)
    
    # def test_clear_metadata(self):
    #     result = self.del_config.clear_metadata('delApp')
    #     self.assertTrue(result)
    
    # def test_clear_section(self):
    #     result = self.del_config.clear_section('delApp')
    #     self.assertTrue(result)

    # def test_clear_profile(self):
    #     result = self.del_config.clear_profile('delApp')
    #     self.assertTrue(result)

    # other methods

    def test_get_from_env(self):
        c = Config('jiraclient')
        result = c.get_from_env('USER', None)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
