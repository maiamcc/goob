import unittest
import os
import goob
import shutil
import cPickle
import tempfile
import pudb
from color import colors

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
        index_data = goob.read_index()
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

        index_data = goob.read_index()

        old_hash = index_data[self.filename]

        make_test_file(self.filename, "my testfile has now changed")

        goob.add(self.filename)

        index_data = goob.read_index()

        new_hash = index_data[self.filename]

        self.assertFileAdded(self.filename)
        self.assertNotEqual(old_hash, new_hash)
        self.assertEqual(len(index_data), 1)

    def test_add_multiple_files(self):
        self.filename2 = "testfile2"
        make_test_file(self.filename2, "contents of another, different testfile")

        goob.add(self.filename)
        goob.add(self.filename2)
        self.assertFileAdded(self.filename)
        self.assertFileAdded(self.filename2)

class testRmFunc(BaseTest):
    def setUp(self):
        super(testRmFunc, self).setUp()
        goob.init()
        self.filename = "testfile"
        self.contents = "contents of my testfile"
        self.filename2 = "testfile2"
        self.contents2 = "this file should remain untouched"
        make_test_file(self.filename, self.contents)
        make_test_file(self.filename2, self.contents2)
        goob.add(self.filename)

    def test_rm_del_file_and_removes_from_index(self):
        goob.rm(self.filename)

        index_data = goob.read_index()
        self.assertNotIn(self.filename, index_data)
        self.assertFalse(os.path.exists(self.filename))

    def test_rm_cached_only_removes_from_index(self):
        goob.rm(self.filename, cached=True)

        index_data = goob.read_index()
        self.assertNotIn(self.filename, index_data)
        # but file should still exist
        self.assertTrue(os.path.exists(self.filename))

    def test_rm_nonadded_file_throws_error(self):
        with self.assertRaises(goob.NoFileError) as e:
            goob.rm(self.filename2)
        self.assertTrue(os.path.exists(self.filename2))
    def test_rm_doesnt_affect_other_files(self):
        goob.add(self.filename2)
        goob.rm(self.filename)

        index_data = goob.read_index()
        self.assertIn(self.filename2, index_data)
        self.assertTrue(os.path.exists(self.filename2))

    def test_rm_cached_doesnt_affect_other_files(self):
        goob.add(self.filename2)
        goob.rm(self.filename, cached=True)

        index_data = goob.read_index()
        self.assertIn(self.filename2, index_data)
        self.assertTrue(os.path.exists(self.filename2))

class DecoratorTests(BaseTest):
    def test_run_command_fails_when_repo_not_initialized(self):
        with self.assertRaises(goob.NoRepoError) as e:
            goob.add('foo')

    def test_run_command_fails_when_nonexistant_file(self):
        goob.init()
        with self.assertRaises(goob.NoFileError) as e:
            goob.add('foo')

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

class testGetHashOfFileContents(BaseTest):
    def setUp(self):
        super(testGetHashOfFileContents, self).setUp()
        goob.init()
        self.filename = "testfile"
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)

    def runTest(self):
        self.assertEqual(goob.get_hash_of_file_contents(self.filename), goob.make_hash(self.contents, "blob"))

class testReadHash(BaseTest):
    def setUp(self):
        super(testReadHash, self).setUp()
        goob.init()
        self.filename = "testfile"
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)
        goob.add(self.filename)

    def test_returns_correct_contents(self):
        file_hash = goob.make_hash(self.contents, "blob")
        returned_content = goob.read_hash(file_hash)
        self.assertEqual(returned_content, self.contents)

    def test_nonexistant_hash_raises_error(self):
        with self.assertRaises(goob.BadHashError) as e:
            goob.read_hash("garuebidwjaofefaef")

class testTreeCreation(BaseTest):
    def setUp(self):
        super(testTreeCreation, self).setUp()
        goob.init()
        self.files = ["a", "b", "c"]
        for filename in self.files:
            make_test_file(filename, "contents of file %s" % filename)
            goob.add(filename)

    def test_make_tree_root_level(self):
        index_data = goob.read_index()

        tree_hash = goob.make_tree(index_data)

        tree_data = goob.read_hash(tree_hash)

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

        index_data = goob.read_index()

        tree_hash = goob.make_tree(index_data)
        tree_data = goob.read_hash(tree_hash)

        subtree0_hash = tree_data[self.subdir0][0]
        subtree0_data = goob.read_hash(subtree0_hash)

        subtree1_hash = subtree0_data[self.subdir1][0]
        subtree1_data = goob.read_hash(subtree1_hash)

        for filename in self.files:
            self.assertIn(filename, tree_data)
        for filename in self.morefiles0:
            self.assertIn(filename, subtree0_data)
        for filename in self.morefiles1:
            self.assertIn(filename, subtree1_data)

class testLookupInTree(BaseTest):
    def setUp(self):
        super(testLookupInTree, self).setUp()
        goob.init()

    def test_zero_levels_deep(self):
        self.filename = "testfile"
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)
        goob.add(self.filename)

        tree_hash = goob.make_tree(goob.read_index())
        found_hash = goob.lookup_in_tree(self.filename, tree_hash)
        self.assertEqual(found_hash, goob.make_hash(self.contents, "blob"))

    def test_one_level_deep(self):
        self.subdir0 = "foo"
        os.mkdir(self.subdir0)
        self.filename = os.path.join(self.subdir0, "testfile")
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)
        goob.add(self.filename)

        tree_hash = goob.make_tree(goob.read_index())
        found_hash = goob.lookup_in_tree(self.filename, tree_hash)
        self.assertEqual(found_hash, goob.make_hash(self.contents, "blob"))

    def test_two_levels_deep(self):
        self.subdir0 = "foo"
        self.subdir1 = "bar"
        os.mkdir(self.subdir0)
        os.mkdir(os.path.join(self.subdir0, self.subdir1))
        self.filename = os.path.join(self.subdir0, self.subdir1, "testfile")
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)
        goob.add(self.filename)

        tree_hash = goob.make_tree(goob.read_index())
        found_hash = goob.lookup_in_tree(self.filename, tree_hash)
        self.assertEqual(found_hash, goob.make_hash(self.contents, "blob"))

    def test_return_none_if_file_not_in_tree(self):
        tree_hash = goob.make_tree(goob.read_index())
        found_hash = goob.lookup_in_tree("nofile", tree_hash)
        self.assertIsNone(found_hash)

class testCommitCreation(BaseTest):
    def setUp(self):
        super(testCommitCreation, self).setUp()
        goob.init()
        self.filename = "testfile"
        self.contents = "contents of my testfile"
        make_test_file(self.filename, self.contents)
        goob.add(self.filename)

    def test_encode_preserves_commit(self):
        testCommit=goob.Commit(123,123,"345","#45","435546")
        testCommit.save()
        decoded=goob.read_hash(testCommit.__hash__())
        self.assertEqual(testCommit,decoded)

    def test_commit_includes_expected_file(self):
        message = "testing commit"
        goob.make_commit(message)

        retrieved_commit = goob.read_hash(goob.get_cur_head())
        tree_data = goob.read_hash(retrieved_commit.tree_hash)

        self.assertIn(self.filename, tree_data)
        self.assertEqual(goob.read_hash(tree_data[self.filename][0]), self.contents)

class testStatusFunc(BaseTest):
    def setUp(self):
        super(testStatusFunc, self).setUp()
        goob.init()

    def test_status(self):
        self.files = ["new_file", "modify_and_add_me",  "just_modify_me", "remove_me", "remove_me_cached", "delete_me_in_dir", "untracked_file"]
        for filename in self.files:
            make_test_file(filename, "this is the file %s" % filename)

        goob.add("modify_and_add_me")
        goob.add("just_modify_me")
        goob.add("remove_me")
        goob.add("remove_me_cached")
        goob.add("delete_me_in_dir")
        goob.commit("first commit")

        goob.rm("remove_me")
        goob.rm("remove_me_cached", cached=True)
        os.remove("delete_me_in_dir")

        make_test_file("modify_and_add_me", "the contents of this file have been modified")
        make_test_file("just_modify_me", "this file has been modified as well")
        goob.add("modify_and_add_me")

        goob.add("new_file")

        print "\n"
        goob.status()
class testWalkTree(BaseTest):
    def runTest(self):
        goob.init()
        make_lotsa_test_files()
        goob.commit("first commit")

        cur_commit = goob.read_hash(goob.get_cur_head())
        tree_walk = goob.walk_tree(cur_commit.tree_hash)

        #TODO finish this test

# UTILITY FUNCTIONS

def make_test_file(filename, contents):
    with open(filename, 'w') as f:
        f.write(contents)

def make_lotsa_test_files(add_all=True):
    subdir0 = "foo"
    subdir1 = "bar"
    os.mkdir(subdir0)
    os.mkdir(os.path.join(subdir0, subdir1))
    files = ["a", "b", "c"]
    morefiles0 = ["d", "e", "f"]
    morefiles1 = ["g", "h", "i"]
    for filename in files:
        make_test_file(filename, "contents of file %s" % filename)
    for filename in morefiles0:
        make_test_file(os.path.join(subdir0, filename), "contents of file %s" % filename)
    for filename in morefiles1:
        make_test_file(os.path.join(subdir0, subdir1, filename), "contents of file %s" % filename)
    if add_all:
        for filename in files:
            goob.add(filename)
        for filename in morefiles0:
            goob.add(os.path.join(subdir0, filename))
        for filename in morefiles1:
            goob.add(os.path.join(subdir0, subdir1, filename))

if __name__ == '__main__':
    unittest.main()