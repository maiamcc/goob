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

class testAddFunc(BaseTest):
    def assertFileAdded(self, filename):
        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)
        self.assertIn(filename, index_data)
        hash = index_data[filename]
        path = os.path.join(goob.OBJECTS_PATH, hash[:2], hash[2:])
        self.assertTrue(os.path.exists(path))

    def setUp(self):
        super(testAddFunc, self).setUp()
        goob.init()
        self.filename = "testfile"
        make_test_file(self.filename, "contents of my file")

    def test_first_time_add_saves_file_in_index(self):
        goob.add(self.filename)
        self.assertFileAdded(self.filename)

    def test_add_unchanged_file_raises_error(self):
        goob.add(self.filename)
        with self.assertRaises(goob.NoChangesError) as e:
            goob.add(self.filename)

    def test_add_changed_file_updates_index(self):
        goob.add(self.filename)

        # TODO: write 'get hash from index' func
        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)

        old_hash = index_data[self.filename]

        make_test_file(self.filename, "my testfile has now changed")

        goob.add(self.filename)

        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)

        new_hash = index_data[self.filename]

        self.assertFileAdded(self.filename)
        self.assertNotEqual(old_hash, new_hash)
        self.assertEqual(len(index_data), 1)

    def test_add_multiple_files(self):
        # TODO: use make test file here
        second_contents = "contents of another, different testfile"
        with open("second_testfile", 'w') as f:
            f.write(second_contents)

        goob.add("testfile")
        goob.add("second_testfile")
        self.assertFileAdded("testfile")
        self.assertFileAdded("second_testfile")

class DecoratorTests(BaseTest):
    def test_run_command_fails_when_repo_not_initialized(self):
        with self.assertRaises(goob.NoRepoError) as e:
            goob.add('foo')

    # test my other decorator too

class testGetHashFromIndex(BaseTest):
    def setUp(self):
        super(testGetHashFromIndex, self).setUp()
        goob.init()
        self.filename = "testfile"
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)
        goob.add(self.filename)

    def test_retrieves_correct_hash(self):
        retrieved_hash = goob.get_hash_from_index(self.filename)
        real_hash = goob.make_hash(self.contents, "blob")
        self.assertEqual(retrieved_hash, real_hash)

    def test_file_not_in_index_raises_error(self):
        with self.assertRaises(goob.NoFileError) as e:
            goob.get_hash_from_index("nonexistant")

class testTreeCreation(BaseTest):
    def setUp(self):
        super(testTreeCreation, self).setUp()
        goob.init()
        self.files = ["a", "b", "c"]
        for filename in self.files:
            make_test_file(filename, "contents of file %s" % filename)
            goob.add(filename)

    def test_make_tree_root_level(self):
        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)

        tree_hash = goob.make_tree(index_data)
        tree_path = os.path.join(goob.OBJECTS_PATH, tree_hash[:2], tree_hash[2:])

        with open(tree_path) as f:
            tree_data = json.load(f)

        # check file in tree, type = blob, hash points somewhere real
        self.assertEqual(sorted(self.files), sorted(tree_data.keys()))

    def test_make_multilevel_subtrees(self):
        self.subdir0 = "foo"
        self.subdir1 = "bar"
        os.mkdir(self.subdir0)
        os.mkdir(os.path.join(self.subdir0, self.subdir1))
        self.morefiles0 = ["d", "e", "f"]
        self.morefiles1 = ["g", "h", "1"]
        for filename in self.morefiles0:
            make_test_file(os.path.join(self.subdir0, filename), "contents of file %s" % filename)
            goob.add(os.path.join(self.subdir0, filename))
        for filename in self.morefiles1:
            make_test_file(os.path.join(self.subdir0, self.subdir1, filename), "contents of file %s" % filename)
            goob.add(os.path.join(self.subdir0, self.subdir1, filename))

        with open(goob.INDEX_PATH) as f:
            index_data = json.load(f)
        tree_hash = goob.make_tree(index_data)
        tree_path = goob.hash_to_path(tree_hash)

        with open(tree_path) as f:
            tree_data = json.load(f)

        subtree0_hash = tree_data[self.subdir0][0]
        subtree0_path = goob.hash_to_path(subtree0_hash)

        with open(subtree0_path) as f:
            subtree0_data = json.load(f)

        subtree1_hash = subtree0_data[self.subdir1][0]
        subtree1_path = goob.hash_to_path(subtree1_hash)

        with open(subtree1_path) as f:
            subtree1_data = json.load(f)

        for filename in self.files:
            self.assertIn(filename, tree_data)
        for filename in self.morefiles0:
            self.assertIn(filename, subtree0_data)
        for filename in self.morefiles1:
            self.assertIn(filename, subtree1_data)


# UTILITY FUNCTIONS

def make_test_file(filename, contents):
    with open(filename, 'w') as f:
        f.write(contents)

if __name__ == '__main__':
    unittest.main()