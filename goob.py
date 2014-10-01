import os
import inspect
import cPickle
from hashlib import sha1
from collections import defaultdict
import re
import time

# GLOBAL PATH NAMES
REPO_PATH = "./.goob"
OBJECTS_PATH = os.path.join(REPO_PATH, "objects")
REFS_PATH = os.path.join(REPO_PATH, "refs")
INDEX_PATH = os.path.join(REPO_PATH, "index")
POINTER_PATH = os.path.join(REPO_PATH, "pointer")
BLOB_PATH = os.path.join(OBJECTS_PATH, "bl")
TREE_PATH = os.path.join(OBJECTS_PATH, "tr")
COMMIT_PATH = os.path.join(OBJECTS_PATH, "co")
PATHS = [REPO_PATH, OBJECTS_PATH, REFS_PATH, INDEX_PATH,
    POINTER_PATH, BLOB_PATH, TREE_PATH, COMMIT_PATH]

# ERRORS
class GoobError(Exception): pass

class NoRepoError(GoobError): pass
class RepoExistsError(GoobError): pass
class NoFileError(GoobError): pass
class NoChangesError(GoobError): pass
class BadHashError(GoobError): pass

## DECORATORS
def requires_repo(func):
    def checked_func(*args, **kwargs):
        if os.path.exists(REPO_PATH):
            return func(*args, **kwargs)
        else:
            raise NoRepoError("Not a goob repo.")
    return checked_func

def requires_extant_file(func):
    def checked_func(filename, *args, **kwargs):
        if os.path.exists(filename):
            return func(filename, *args, **kwargs)
        else:
            raise NoFileError("File does not exist.")
    return checked_func

## USER COMMANDS
def init():
    """Makes a new .goob directory in the current directory, populates
        it with the relevant stuff"""

    if os.path.exists(REPO_PATH):
        raise RepoExistsError("This is already a goob repo.")
    else:
        os.mkdir(REPO_PATH)
        os.mkdir(OBJECTS_PATH)
        os.mkdir(REFS_PATH)
        os.mkdir(BLOB_PATH)
        os.mkdir(TREE_PATH)
        os.mkdir(COMMIT_PATH)
        open(INDEX_PATH, "a").close()
        open(POINTER_PATH, "a").close()

@requires_repo
@requires_extant_file
def add(filename):
    """Stages the given file for commit."""

    # TODO: Add("-a") will add all files in the directory (except those in .goobignore)"""

    index_data = read_index()

    # index format: dict where index[filename] = hashhashash

    with open(filename) as f:
        contents = f.read()
    hash = make_hash(contents, 'blob')

    if filename in index_data and index_data[filename] == hash:
        raise NoChangesError("This file hasn't changed. Nothing added.")
    else:
        save_hash(contents, hash)
        index_data[filename] = hash

    write_index(index_data)

@requires_repo
@requires_extant_file
def rm(filename, cached=False):
    """If not 'cached': removes file from index and deletes the file. If 'cached':
        removes file from index but does not delete the file."""

    index_data = read_index()
    try:
        del index_data[filename]
    except KeyError:
        raise NoFileError("%s isn't staged" % filename)
    else:
        write_index(index_data)
        if not cached:
            os.remove(filename)

@requires_repo
def commit(message):
    """Makes a new commit object (with parent = current commit), representing all
        tracked files in a tree(/subtrees), with the given commit message, author,
        date, etc."""

    # QUESTION: does this control flow make sense?
    make_commit(message)

@requires_repo
def status():
    """Displays untracked files, modified files, unmodified files."""
    # untracked = files in dir not in index (or goobignore)
    # modified = files in index: the version saved as a blob (find the hash in index) is DIFFERENT from version in dir
    # unmodified = all other files in index

    # (if dir is goob repo)
    pass

@requires_repo
def checkout(commit_hash):
    """Restores filesystem to state represented by given commit."""
    # if modified files, ask you to add those changes first.
    # (if dir is goob repo, if commit exists)
    pass

@requires_repo
def list_files():
    """Lists all of the files being tracked by goob (from .goob/index)"""
    index_data = read_index
    print "\n".join(sorted(index_data.keys()))

# Files I need
# .goobignore file = this file will tell you which thigns to ignore (i.e. not add)

#.goob/pointer = file containing the hash of the current commit <<< change later for branching, detached head, etc.
#.goob/index = all the files that goob knows about, + hashes

## INTERNAL COMMANDS
def diff(file1, file2):
    """If the files are at all different, return True. Otherwise, false."""
    pass

class Commit(object):
    def __init__(self, tree_hash, timestamp, msg, parent=None, author="ME!"):
        self.tree_hash = tree_hash
        self.timestamp = timestamp
        self.msg = msg
        self.parent = parent
        self.author = author

    def __str__(self):
        return "Tree: %s\nTimestamp: %s\nMessage: %s\nParent: %s\nAuthor: %s" % (self.tree_hash, self.timestamp, self.msg, self.parent, self.author)

    def __hash__(self):
        return make_hash(str(self), "commit")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def save(self):
        commit_hash = self.__hash__()
        save_hash(self, commit_hash)

def make_commit(msg):
    """makes a commit file"""
    index_data = read_index()

    tree_hash = make_tree(index_data)
    timestamp = time.ctime()
    parent = get_cur_head()

    new_commit = Commit(tree_hash, timestamp, msg, parent)
    new_commit.save()
    update_head(new_commit.__hash__())

def get_cur_head():
    with open(POINTER_PATH) as f:
        return f.read()

def update_head(commit_hash):
    with open(POINTER_PATH, "w") as f:
        f.write(commit_hash)

def make_tree(path_dict):
    """Makes a tree file and returns the hash."""

    my_tree = {}
    directories = defaultdict(dict)

    for path, hash in path_dict.iteritems():
        if os.sep in path:
            directories[path.split(os.sep, 1)[0]][path.split(os.sep, 1)[1]] = hash
        else:
            my_tree[path] = hash, "blob"

    for dir, filedict in directories.iteritems():
        my_tree[dir] = make_tree(filedict), "tree"

    hash = make_hash(str(sorted(my_tree.items())), "tree")
    save_hash(my_tree, hash)

    return hash

    # to prettify -- 'subdivide' func that finds everything
        # belonging to a particular folder etc. all at once?

def read_hash(hash):
    """Returns contents of the file at given hash"""
    # given hash xxyyyyyy, look in .goob/objects/xx/yyyyyy, return contents (text)
        # when I implement contents-encoding, will need to decode here.
        # if it's a tree or a commit, will need prettyprint method?
    try:
        path = hash_to_path(hash)
        with open(path) as f:
            return cPickle.load(f)
    except IOError:
        raise BadHashError("No file exists at this hash.")

def make_hash(contents, type):
    """Return hash of the contents with type prepended."""
    # type -- tr (tree), bl (blob), co(commit)
        # TODO: should check if you passed a valid type? or no?
    # e.g. tr/hash(contents) for a tree
    return '%s%s' % (type[:2], sha1(contents).hexdigest())

def save_hash(contents, hash):
    """Save the contents at the given hash. """

    path = os.path.join(OBJECTS_PATH, hash[:2], hash[2:])
    with open(path, 'w') as f:
        cPickle.dump(contents, f)

def get_hash_of_file_contents(filename, type="blob"):
    """Returns a hash of the contents of the given file. Assumes a blob."""
    with open(filename) as f:
        contents = f.read()
    return make_hash(contents, type)

def get_hash_from_index(filename):

    with open(INDEX_PATH) as f:
        try:
            index_data = cPickle.load(f)
        except EOFError:
            index_data = {}
    try:
        return index_data[filename]
    except KeyError:
        raise NoFileError("That file isn't in the index.")

def hash_to_path(hash):
    return os.path.join(OBJECTS_PATH, hash[:2], hash[2:])

def read_index():
    """Returns the contents of the INDEX file. If INDEX is empty, returns an empty dict."""
    with open(INDEX_PATH) as f:
        try:
            index_data = cPickle.load(f)
        except EOFError:
            index_data = {}
    return index_data

def write_index(contents):
    """Writes 'contents' (presumably a dict. of filenames and hashes) to INDEX file."""
    with open(INDEX_PATH, 'w') as f:
            cPickle.dump(contents, f)

def lookup_in_tree(filename, tree_hash):
    """Searches given tree and its subtrees for the given filename, returns file's hash."""
    # currently expects the full file-path rather than just the file name: maybe a
        # separate function to seach tree for a specific filename?
    tree_data = read_hash(tree_hash)
    if os.sep in filename:
        subtree_data = tree_data
        while os.sep in filename:
            subtree_data = read_hash(subtree_data[filename.split(os.sep, 1)[0]][0])
            filename = filename.split(os.sep, 1)[1]
        found_hash = subtree_data[filename][0]
    else:
        found_hash = tree_data[filename][0]

    return found_hash

### USEFUL COMMANDS
# os.path.: exists / isfile / isdir
# os.mkdir (makes directory)

# different sub-programs per command?
# TODO: currently goob only runs from the root dir of the project. Should fix this.

