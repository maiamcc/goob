import unittest
import os
import goob
import shutil

class initCreatesNewStuff(unittest.TestCase):
    def setUp(self):
        if os.path.exists("./.goob"):
            shutil.rmtree('./.goob')
    def runTest(self):
        goob.init()
        for path in ['./.goob',
                     './.goob/objects',
                     './.goob/index',
                     './.goob/refs',
                     './.goob/pointer']:
            self.assertTrue(os.path.exists(path))
    def tearDown(self):
        shutil.rmtree('./.goob')

if __name__ == '__main__':
    unittest.main()