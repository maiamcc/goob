import unittest
import os
import goob
import shutil
import json
import tempfile

class BaseTest(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()
        self._current_dir = os.getcwd()
        os.chdir(self._temp_dir)

    def _clean_goob_dir(self):
        os.chdir(self._current_dir)
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    def tearDown(self):
        self._clean_goob_dir()

class InitTests(BaseTest):
    def test_init(self):
        goob.init()
        for path in goob.PATHS:
            self.assertTrue(os.path.exists(path))

    def test_init_fails_if_repo_exists(self):
        # Given
        goob.init()

        # When/Then
        with self.assertRaises(goob.RepoExistsError) as e:
            goob.init()

class DecoratorTests(BaseTest):
    def test_run_command_fails_when_repo_not_initialized(self):
        with self.assertRaises(goob.NoRepoError) as e:
            goob.add('foo')

class testAddFunc(BaseTest):
    def setUp(self):
        super(testAddFunc, self).setUp()
        goob.init()
        contents = "contents of my testfile"
        with open("testfile", 'w') as f:
            f.write(contents)

    def test_first_time_add_saves_file_in_index(self):
        goob.add("testfile")
        self.assertFileAdded("testfile")

    def test_add_unchanged_file_raises_error(self):
        goob.add("testfile")
        with self.assertRaises(goob.NoChangesError) as e:
            goob.add("testfile")

    def test_add_changed_file_updates_index(self):
        goob.add("testfile")

        # TODO: write 'get hash from index' func
        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)

        old_hash = index_data["testfile"]

        contents = "my testfile has now changed"
        with open("testfile", 'w') as f:
            f.write(contents)

        goob.add("testfile")

        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)

        new_hash = index_data["testfile"]

        self.assertFileAdded("testfile")
        self.assertNotEqual(old_hash, new_hash)
        self.assertEqual(len(index_data), 1)

    def assertFileAdded(self, filename):
        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)
        self.assertTrue(len(index_data) > 0)
        self.assertIn(filename, index_data)
        hash = index_data[filename]
        path = os.path.join(goob.OBJECTS_PATH, hash[:2], hash[2:])
        self.assertTrue(os.path.exists(path))

    def test_add_multiple_files(self):
        second_contents = "contents of another, different testfile"
        with open("second_testfile", 'w') as f:
            f.write(second_contents)

        goob.add("testfile")
        goob.add("second_testfile")
        self.assertFileAdded("testfile")
        self.assertFileAdded("second_testfile")

if __name__ == '__main__':
    unittest.main()