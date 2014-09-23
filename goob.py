import os
import inspect
import json
from hashlib import sha1
from collections import defaultdict
import re

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

## DECORATORS
def requires_repo(func):
    def checked_func(*args):
        if os.path.exists(REPO_PATH):
            return func(*args)
        else:
            raise NoRepoError("Not a goob repo!")
    return checked_func

def requires_extant_file(func):
    def checked_func(filename, *args):
        if os.path.exists(filename):
            return func(filename, *args)
        else:
            raise NoFileError("File does not exist!")
    return checked_func

## USER COMMANDS
def init():
    """Makes a new .goob directory in the current directory, populates
        it with the relevant stuff"""

    if os.path.exists(REPO_PATH):
        raise RepoExistsError("This is already a goob repo!")
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

    with open(INDEX_PATH) as f:
        try:
            index_data = json.load(f)
        except ValueError:
            index_data = {}

    # index format: dict where index[filename] = hashhashash

    with open(filename) as f:
        contents = f.read()
    hash = make_hash(contents, 'blob')

    if filename in index_data and index_data[filename] == hash:
        raise NoChangesError("This file hasn't changed! Nothing added.")
    else:
        save_hash(contents, hash)
        index_data[filename] = hash

    with open(INDEX_PATH, 'w') as f:
            json.dump(index_data, f)

@requires_repo
@requires_extant_file
def unstage(filename):
    """If staged, the given file is unstaged."""
    # if file is in the index
        # if no commits yet (i.e. pointer isn't pointing to a commit)
            # remove file from the index
        # else
            # if hash in index is diff. from hash in most recent commit
                # then change hash in index to most recent commit hash
            # else, file hasn't been staged since modification.
    # else, throw error: "file not added yet"
    pass

@requires_repo
@requires_extant_file
def rm(filename):
    """The given file won't be tracked in the next commit, or subsequently,
        till added again."""

    # (if file exists)
    # (if dir is goob repo)
    pass

@requires_repo
def commit(message):
    """Makes a new commit object (with parent = current commit), representing all
        tracked files in a tree(/subtrees), with the given commit message, author,
        date, etc."""

    pass

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

    # (if dir is goob repo)
    pass

# Files I need
# .goobignore file = this file will tell you which thigns to ignore (i.e. not add)

#.goob/pointer = file containing the hash of the current commit <<< change later for branching, detached head, etc.
#.goob/index = all the files that goob knows about, + hashes

## INTERNAL COMMANDS
def diff(file1, file2):
    """If the files are at all different, return True. Otherwise, false."""
    pass

def make_commit():
    """makes a commit file"""
    # first, make a tree (that contains all files/subtrees)
    # then, make a commit file
    # generate text first, then save w/ save_in_hash

    # OR should this just generate the content, and pass to another func to save?
    """Tree/(Parent)/Author/Timestamp/Message"""
    pass

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
    save_hash(my_tree, hash, encode=True)

    return hash

    # to prettify -- 'subdivide' func that finds everything
        # belonging to a particular folder etc. all at once?

def lookup_by_hash(hash):
    """Returns contents of the file at given hash"""
    # given hash xxyyyyyy, look in .goob/objects/xx/yyyyyy, return contents (text)
        # when I implement contents-encoding, will need to decode here.
        # if it's a tree or a commit, will need prettyprint method?
    pass

def make_hash(contents, type):
    """Return hash of the contents with type prepended."""
    # type -- tr (tree), bl (blob), co(commit)
        # should check if you passed a valid type? or no?
    # e.g. tr/hash(contents) for a tree
    return '%s%s' % (type[:2], sha1(contents).hexdigest())

def save_hash(contents, hash, encode=False):
    """Save the contents at the given hash. """

    path = os.path.join(OBJECTS_PATH, hash[:2], hash[2:])
    with open(path, 'w') as f:
        if encode:
            json.dump(contents, f)
        else:
            f.write(contents)

    # eventually will be encoded

def get_hash_from_index(filename):

    with open(INDEX_PATH) as f:
        try:
            index_data = json.load(f)
        except ValueError:
            index_data = {}
    try:
        return index_data[filename]
    except KeyError:
        raise NoFileError("That file isn't in the index!")

def hash_to_path(hash):
    return os.path.join(OBJECTS_PATH, hash[:2], hash[2:])




### USEFUL COMMANDS
# os.path.: exists / isfile / isdir
# os.mkdir (makes directory)

