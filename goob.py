import os
import inspect
import cPickle
from hashlib import sha1
from collections import defaultdict, namedtuple
import re
import time
from color import colors

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

ObjectHash = namedtuple("ObjectHash", ["hash", "type"])

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

class Status(object):
    def __init__(self, new=[], modified_added=[], removed=[], modified_not_added=[], untracked=[], deleted=[]):
        self.new = new
        self.modified_added = modified_added
        self.removed = removed
        self.modified_not_added = modified_not_added
        self.untracked = untracked
        self.deleted = deleted

    def __str__(self):
        results = []
        results.append("Changes to be committed:" + colors.GREEN)
        results.extend([("\tNew file: %s" % filename) for filename in self.new])
        results.extend([("\tModified: %s" % filename) for filename in self.modified_added])
        results.extend([("\tDeleted: %s" % filename) for filename in self.removed])
        results.append(colors.ENDC + "Changes not staged for commit:" + colors.RED)
        results.extend([("\tModified: %s" % filename) for filename in self.modified_not_added])
        results.extend([("\tDeleted: %s" % filename) for filename in self.deleted])
        results.append(colors.ENDC + "Untracked files:" + colors.RED)
        results.extend([("\t%s" % filename) for filename in self.untracked])
        results.append(colors.ENDC)
        return "\n".join(results)

    def __eq__(self, other):
        if type(self) == type(other):
            for attr, val in vars(self).iteritems():
                if set(val) != set(other.__getattribute__(attr)):
                    return False
                return True
        else:
            return False


@requires_repo
def status():
    """Displays untracked files, modified files, unmodified files."""
    # changes to be committed:
        # new file = file added to index but not in previous commit
        # modified_added = file in index with different hash from its hash in previous commit but same hash as its hash in the index
        # removed = file in last commit not currently in index
    # changes not staged for commit:
        # modified_not_added = files in index and in last commit, file's hash is diff from hash in index
        # untracked = file in dir not in index (or goobignore)
        # deleted = file in the index not in the directory
            # ^^^ need to change how 'add' deals with this^^^
    new, modified_added, removed, modified_not_added, untracked, deleted = [], [],[],[],[],[]

    # TODO: work in GOOBIGNORE
    cur_status = Status()

    all_files = [os.path.join(root, file)[2:] for root, dirs, files in os.walk(".") \
        for file in files if not ".goob" in root]

    index_data = read_index()

    try:
        cur_commit = read_hash(get_cur_head())
    except BadHashError:
        cur_commit = None

    for filename in all_files: # for every file in directory
        if filename not in index_data: # if not in index:
            if lookup_in_tree(filename, cur_commit.tree_hash): # if in last commit:
                cur_status.removed.append(filename)
            else:
                cur_status.untracked.append(filename)
        else:
            hash_in_commit = lookup_in_tree(filename, cur_commit.tree_hash)
            file_hash = get_hash_of_file_contents(filename)
            if hash_in_commit: # if in previous commit:
                if file_hash != index_data[filename]: # if hash of file diff from its hash in index
                    cur_status.modified_not_added.append(filename)
                elif file_hash != hash_in_commit: # if hash of file (= hash in index) diff from hash in commit:
                    cur_status.modified_added.append(filename)
                else:
                    # unchanged -- no action
                    pass
            else:
                cur_status.new.append(filename)

    files_in_cur_commit = walk_tree(cur_commit.tree_hash)
    for filename in set(files_in_cur_commit).difference(set(all_files)):
        if filename in index_data:
            cur_status.deleted.append(filename) # uncommited delete (deleted)
        else:
            cur_status.removed.append(filename) # committed delete (removed)

    print cur_status
    return cur_status

@requires_repo
def log():
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
            my_tree[path] = ObjectHash(hash, "blob")

    for dir, filedict in directories.iteritems():
        my_tree[dir] = ObjectHash(make_tree(filedict), "tree")

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
    """Given a file, looks up its hash in the index, returns result. If file not
        in index, raises error."""
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
    """Given a hash, turns it into the path to that file in the
        .goob/objects directory."""
    return os.path.join(OBJECTS_PATH, hash[:2], hash[2:])

def read_index():
    """Returns the contents of the INDEX file. If INDEX is empty,
        returns an empty dict."""
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
        try:
            while os.sep in filename:
                subtree_data = read_hash(subtree_data[filename.split(os.sep, 1)[0]].hash)
                filename = filename.split(os.sep, 1)[1]
            found_hash = subtree_data[filename].hash
        except KeyError:
            found_hash = None
    else:
        try:
            found_hash = tree_data[filename].hash
        except KeyError:
            found_hash = None

    return found_hash

def walk_tree(tree_hash, prefix=None):
    """Given a tree, returns a list of files in that tree and all subtrees."""
    results = []
    for filename, (hash, obj_type) in read_hash(tree_hash).iteritems():
        if obj_type == "blob":
            if prefix:
                results.append(os.path.join(prefix, filename))
            else:
                results.append(filename)
        else:
            if prefix:
                results.extend(walk_tree(hash, prefix=os.path.join(prefix,filename)))
            else:
                results.extend(walk_tree(hash, prefix=filename))
    return results


### USEFUL COMMANDS
# os.path.: exists / isfile / isdir
# os.mkdir (makes directory)

# different sub-programs per command?
