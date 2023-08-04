import unittest
from adhoc.command import run_command

class TestAddMethods(unittest.TestCase):

    def test_run_command(self):
        RESULT = run_command('ls -l')
        self.assertTrue(RESULT)
    

if __name__ == '__main__':
    unittest.main()