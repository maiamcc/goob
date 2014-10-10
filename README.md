goob
====
An imitation git, written as an exercise in understanding version control and the inner workings of git. (This README is half README, half Git 101 written for Hacker School Job Prep.)

### How Git Works (sort of)

#### Three kinds of objects: `blobs`, `commits`, and `trees`
When you add a file to git, it's saved as a _blob_ (meaning, file): the file's contents are encoded and it is saved as a file named for the hash of its contents. When you make a commit, a new _commit_ object is created. A commit stores the following information: "tree," "author," "committer," and "commit message." The last three are pretty self-explanatory (though I'm unsure of the distinction between "author" and "committer"...), but "tree" is a little confusing, and the last git object type to explain. A _tree_  contains references to all files or folders (which are also represented as tree objects) in the given commit. Blobs, commits, and trees are all stored in the `.git/objects` directory. Goob has some slight implementation differences as compared to git, but the general structure is the same.

#### How do we know what's going on?
The index (a file stored at `.git/index`) keeps track of all the files we're currently paying attention to; it stores the file name alongside the hash at which its blob-self can be found. `HEAD` is a pointer that tells us what commit we're currently on--that is, it's the hash of the commit in question. What we think of as "branches" have NOTHING to do with the git tree object; really, they themselves are also pointers, containing the hash of the topmost commit of the branch in question. (And then, because each commit knows its own parent, the branch can then trace its history all the way down.) All of these branch pointers are stored the `.git/refs/heads` folder. The `.git/HEAD` file either contains the path to a file in `.git/refs/heads` (the top of the branch that you're on) or, if you're in detached head mode, just the hash of the commit you're currently looking at.

### Tips and tricks for poking around in Git

* `git cat-file -p [hash]` shows you the contents of a git object. (Note that git file addresses look like `.git/objects/xx/yyyyyy...`; the hash of that object--what you should feed to `git cat-file`--is `xxyyyyyy...`)
* `git ls-files --stage` shows you all the files and hashes stored in the index, as well as some information about their permissions

### Commands

* `init()` - makes new goob repo.
* `add(file)` - stages file for commit (saves the file as a blob, adds it to the index).
* `rm(file)` - removes file from the index and deletes the file from disk. (If `cached=True`: removes file from the index but not delete. That is, goob stops watching the file.)
* `commit(message)` - commits the current filestate as captured in the index, with the given message as the commit message. At the moment, author is hardcoded--eventually this will be read from a config file.
* `status()` - displays untracked files, modified files, unmodified files. (Returns it in the form of a `Status` object, which contains distinct lists for all of the different possible file states. The `Status` object will be used later, when `checkout` is implemented.)
* `list_files()` - lists all of the files being tracked by goob in the index. The information-light equivalent of `git ls-files --stage`.

#### Not yet implemented

* `log()` - displays a list of past commits.
* `checkout(commit_hash)` - restores disk to the state as captured in the given commit.

### On Testing
This is the sort of program that's potentially really difficult to test, because you can potentially mess up the state of your project directory--change files, leave extra hidden files lying around, etc. Therefore, all of my tests take place in a temporary directory that is cleaned at the beginning and end of each test.

### To Do

* should be runnable from command line
* goob commands should be runnable from any directory within the repo, not just the root dir
* should tree and blob be classes, for symmetry with the commit class?
* "author" and similar information should be read from a config file, not hard-coded
* what happens when you delete a file from disk but not from the repo? In git, user has to "add" a deleted file so its deletion will be tracked! Goob doesn't handle this yet
* .goobignore