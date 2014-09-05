import os
import inspect

## DECORATORS
def requires_repo(func):
    def checked_func(*args):
        if os.path.exists("./.goob"):
            return func(*args)
        else:
            raise ValueError("Not a goob repo!")
    return checked_func

def requires_extant_file(func):
    def checked_func(filename, *args):
        if os.path.exists(filename):
            return func(filename, *args)
        else:
            raise ValueError("File does not exist!")
    return checked_func

## USER COMMANDS
def init():
    """Makes a new .goob directory in the current directory, populates
        it with the relevant stuff"""

    if os.path.exists("./.goob"):
        print "This is already a goob repo! Good job! :D"
    else:
        os.mkdir("./.goob")
        os.mkdir("./.goob/objects")
        os.mkdir("./.goob/refs")
        open("./.goob/index", "a").close()
        open("./.goob/pointer", "a").close()

@requires_extant_file
@requires_repo
def add(filename):
    """Stages the given file for commit. Add("-a") will
        add all files in the directory (except those in .goobignore)"""
    # (if file exists)
    # (if dir is goob repo)

    # check for file in index
        # if file in index: check version in dir for changes vs. the one hashed to in index.
            # if different, add new one (blob file, add name+hash to index)
        # else, blob file, add name+hash to index

    # --> hash = save_in_hash(filecontents, "blob")
    # --> update_index(filename, hash)
    pass

@requires_extant_file
@requires_repo
def unstage(filename):
    """If staged, the given file is unstaged."""
    # (if file exists)
    # (if dir is goob repo)
    pass

@requires_extant_file
@requires_repo
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

def save_in_hash(contents, type):
    """Makes a file path for an object, based on its type and contents."""
    # type -- tr (tree), bl (blob), co(commit)
    # e.g. tr/hash(contents) for a tree
    # saves a file with name hash(contents) in dir 'type', writes 'contents' to that file
    # eventually will be encoded
    # return hash (no slashes)
    pass


### USEFUL COMMANDS
# os.path.: exists / isfile / isdir
# os.mkdir (makes directory)

