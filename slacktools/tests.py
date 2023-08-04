import unittest
from slackclient import auth, misc, post, react, unreact, unpost, slack_converter

class TestAddMethods(unittest.TestCase):

    # auth tests

    def test_get_slack_session(self):
        result = auth.get_slack_session('default')
        self.assertIsNotNone(result)

    def test_get_slack_token(self):
        result = auth.get_slack_token('default')
        self.assertIsNotNone(result)

    def test_slackclient_config(self):
        result = auth.get_slackclient_config()
        self.assertIsNotNone(result)

    # misc tests

    def testConvertTupleNoInts(self):
        self.assertEqual(misc.convertTuple(('1', "2", "3")), "123")

    def testConvertTupleWithInts(self):
        self.assertEqual(misc.convertTuple(("1", 2, "3")), "123")

    # post, react, unreact, unpost tests

    def test_slack_message_and_reaction(self):
        stacksalot = ['C040ES12LUU']
        message_result = post.post_slack_message(stacksalot, 'INFO: unittest test_post_slack_message')
        self.assertIsNotNone(message_result)
        thread_ts = message_result[0].get('ts')
        reaction_result = react.post_slack_reaction(stacksalot, thread_ts, 'test_tube')
        reaction_bool = reaction_result.get('ok')
        self.assertTrue(reaction_bool)
        delete_reaction_result = unreact.delete_slack_reaction(stacksalot, thread_ts, 'test_tube')
        delete_reaction_bool = delete_reaction_result.get('ok')
        self.assertTrue(delete_reaction_bool)
        delete_message_result = unpost.delete_slack_message(stacksalot, thread_ts)
        delete_message_bool = delete_message_result.get('ok')
        self.assertTrue(delete_message_bool)

    # slack_converter tests

    def test_channel_converter(self):
        stacksalot = ['C040ES12LUU']
        result = slack_converter.convert_slack_names(stacksalot)
        self.assertIsNotNone(result)        

if __name__ == '__main__':
    unittest.main()