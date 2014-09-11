import os
import inspect
import json
from hashlib import sha1

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

    # later: check if index contains stuff
    with open(INDEX_PATH) as f:
        try:
            index_data = json.load(f)
        except ValueError:
            index_data = {}

    # index format: dict where index[filename] = hashhashash

    with open(filename) as f:
        contents = f.read()
    hash = make_hash(contents, 'blob')
    # (hashes are unique, right?)

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
    # (if file exists)
    # (if dir is goob repo)
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

    # (if dir is goob repo)

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
    """Tree/(Parent)/Author/Timestamp/Message"""
    pass

def make_tree(path_list):
    """makes a tree file"""
    # pass in list of filepaths from index (or elsewhere)
    # for all files in filepath list, if in root dir,
        # add hash+name to tree. Else, make a new tree corresponding to
        # topmost dir (recursive function)
    # generate text first, then save w/ save_in_hash
    pass

def make_blob(filename):
    """Given a file, encodes, hashes, saves encoding to dir w/ name = hash."""
    # --> save_in_hash(filecontents, "blob")
    pass

def update_index(filename, hash):
    """Updates index that file of name 'filename' can be found at hash 'hash'."""
    pass

def check_if_repo():
    """Throws an error if dir not a goob repo (i.e. if dir .goob doesn't exist)"""
    pass

def lookup_by_hash(hash):
    """Returns contents of the file at given hash"""
    # given hash xxyyyyyy, look in .goob/objects/xx/yyyyyy, return contents (text)
        # when I implement contents-encoding, will need to decode here.
    pass

def make_hash(contents, type):
    """Return hash of the contents with type prepended."""
    # type -- tr (tree), bl (blob), co(commit)
    # e.g. tr/hash(contents) for a tree
    return '%s%s' % (type[:2], sha1(contents).hexdigest())

def save_hash(contents, hash):
    """Save the contents at the given hash. """

    path = os.path.join(OBJECTS_PATH, hash[:2], hash[2:])
    with open(path, 'w') as f:
        f.write(contents)

    # eventually will be encoded





### USEFUL COMMANDS
# os.path.: exists / isfile / isdir
# os.mkdir (makes directory)

