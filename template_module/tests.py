import unittest

class TestAddMethods(unittest.TestCase):

    def test_submodule_method(self):
        RESULT = True #swap that for a method from a module/submodule
        self.assertTrue(RESULT)

if __name__ == '__main__':
    unittest.main()