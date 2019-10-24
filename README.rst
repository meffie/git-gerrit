git-gerrit
==========

**git-gerrit** is command line tool for the `Gerrit code review system`_, with an
emphasis on the Gerrit legacy numerical identifiers.  The heavy lifting is done
with the **pygerrit2** package to access the Gerrit REST API.

.. _Gerrit code review system: https://www.gerritcodereview.com/

**git-gerrit** is compatible with Python 2 and Python 3.

Commands::

    git gerrit-help              List commands.
    git gerrit-query             Search gerrit.
    git gerrit-fetch             Fetch by gerrit number.
    git gerrit-checkout          Fetch then checkout by gerrit number.
    git gerrit-log               Show oneline log with gerrit numbers.
    git gerrit-unpicked          Find gerrit numbers on upstream branch not cherry picked.
    git gerrit-cherry-pick       Cherry pick from upstream branch by gerrit number.
    git gerrit-install-hooks     Install git hooks to create gerrit change-ids.

Installation
============

Install with pip::

    $ pip install --user git-gerrit

To install from source, clone the git repo and install with the provided
makefile.  `make` will run `pip` to install the package and
requirements::

    $ git clone https://github.com/meffie/git-gerrit.git
    $ cd git-gerrit
    $ make install

Clone the git project under gerrit review, and in that project directory
set the Gerrit host and project names in the local git configuration::

    $ cd <your-gerrit-project>
    $ git config gerrit.host <gerrit-hostname>
    $ git config gerrit.project <gerrit-project>

Finally, download the git hook provided by gerrit and a git hook provided
by git-gerrit::

    $ git gerrit-install-hooks

Examples
========

Setup a local OpenAFS git repo::

    $ git clone git://git.openafs.org/openeafs.git # (if not already cloned)
    $ cd openafs
    $ git config --local gerrit.host gerrit.openafs.org
    $ git config --local gerrit.project openafs
    $ git gerrit-install-hooks

Find open gerrits on the master branch::

    $ git gerrit-query -n3 is:open branch:master
    13030 redhat: Make separate debuginfo for kmods work with recent rpm
    13031 redhat: PACKAGE_VERSION macro no longer exists
    13021 autoconf: update curses.m4

Find gerrits with subjects containing the term 'debuginfo'::

    $ git gerrit-query -n3 debuginfo
    13030 redhat: Make separate debuginfo for kmods work with recent rpm
    13029 redhat: Create unique debuginfo packages for kmods
    12818 redhat: separate debuginfo package for kmod rpm

Also show the branch name::

    $ git gerrit-query -n3 --format='{branch:>20s} {_number} {subject}' debuginfo
                  master 13030 redhat: Make separate debuginfo for kmods work with recent rpm
    openafs-stable-1_6_x 13029 redhat: Create unique debuginfo packages for kmods
    openafs-stable-1_6_x 12818 redhat: separate debuginfo package for kmod rpm

List the gerrit topics on a branch::

    $ git gerrit-query --format='{topic}' status:open branch:master | sort -u | head -n3
    afsd-cache-verify
    AFS-OSD-integration
    afs_read-EOF

Show gerrit submissions on the master branch I need to review::

    $ git gerrit-query branch:master status:open NOT label:Code-Review=-2 NOT reviewer:tycobb@yoyodyne.com
    ...

Fetch a gerrit by number::

    $ git gerrit-fetch 12977

Checkout a gerrit by number::

    $ git gerrit-checkout 13000

Cherry-pick a gerrit onto the current branch::

    $ git gerrit-fetch --no-branch 13001 && git cherry-pick FETCH_HEAD

Show gerrit numbers in one the checked out branch::

    $ git gerrit-log -n3
    12958 f47cb2d Suppress statement not reached warnings under Solaris Studio
    12957 306f0f3 afs: squash empty declaration warning
    12955 e006609 libafs: git ignore build artifacts on Solaris

Show gerrit numbers by a revision::

    $ git gerrit-log -n3 openafs-stable-1_8_0
    12953 a08327f Update NEWS for 1.8.0 final release
    12938 acb0e84 afs_pioctl: avoid -Wpointer-sign
    12950 b73863b LINUX: fix RedHat 7.5 ENOTDIR issues

Show gerrit numbers by a range of revisions::

    $ git gerrit-log 607eba34d..origin/openafs-stable-1_8_x
    13268 554176bd2 LINUX: Update to Linux struct iattr->ia_ctime to timespec64 with 4.18
    13266 eb107ed5c Make OpenAFS 1.8.1
    13265 8de978420 Update NEWS for 1.8.1

Show just the gerrit numbers and subjects::

    $ git gerrit-log -n3 --format='{number}: {subject}'
    12958: Suppress statement not reached warnings under Solaris Studio
    12957: afs: squash empty declaration warning
    12955: libafs: git ignore build artifacts on Solaris

Show the commits on the master branch which have not been cherry-picked on to
the stable branch. (Gerrits may already exists for them.)::

    $ git gerrit-unpicked -u origin/master origin/openafs-stable-1_8_x
    13656 4eeed830fa31b7b8b5487ba619acbc8d30642aaa afscp: Link against opr/roken/hcrypto
    13659 f5f59cd8d336b153e2b762bb7afd16e6ab1b1ee2 util: serverLog using memory after free
    13665 1210a8d6d96db2d84595d35ef81ec5d176de05e8 LINUX: Run the 'sparse' checker if available
    ...


Using git aliases
=================

Commonly used queries can be saved as git aliases. For example to show the
gerrits which have not been reviewed yet::

    [alias]
    # git gerrit-todo [<branch>] [<userid>]
    gerrit-todo = "!f() { git-gerrit-query \"branch:${1-master} is:open NOT label:Code-Review>=+1,${2-$USER}\"; }; f"

Command help
============

Command git-gerrit-checkout::

    usage: git-gerrit-checkout [-h] [--repodir REPODIR]
                               [--branch BRANCH | --no-branch]
                               <number>
    
    Fetch then checkout by gerrit number.
    
    positional arguments:
      <number>           legacy change number
    
    optional arguments:
      -h, --help         show this help message and exit
      --repodir REPODIR  path to the git project directory
      --branch BRANCH    local branch to create (default:
                         gerrit/<number>/<patchset>)
      --no-branch        do not create a local branch

Command git-gerrit-cherry-pick::

    usage: git-gerrit-cherry-pick [-h] [-b <branch>] <number>
    
    Cherry pick from upstream branch by gerrit number.
    
    positional arguments:
      <number>              legacy change number
    
    optional arguments:
      -h, --help            show this help message and exit
      -b <branch>, --branch <branch>
                            upstream branch (default: origin/master)
    
    Note: A new gerrit Change-Id will be created in the cherry-picked commit.
    
    Example usage:
    
        $ git gerrit-query is:merged branch:master 'fix the frobinator'
        1234 fix the frobinator
    
        $ git fetch origin
        $ git checkout -b fix origin/the-stable-branch
        ...
    
        $ git gerrit-cherry-pick 1234 -b origin/master
        [fix f378563c94] fix the frobinator
         Date: Fri Apr 4 10:27:10 2014 -0400
          2 files changed, 37 insertions(+), 12 deletions(-)
    
        $ git push gerrit HEAD:refs/for/the-stable-branch
        ...

Command git-gerrit-fetch::

    usage: git-gerrit-fetch [-h] [--repodir REPODIR] [--checkout]
                            [--branch BRANCH | --no-branch]
                            <number>
    
    Fetch by gerrit number.
    
    positional arguments:
      <number>           legacy change number
    
    optional arguments:
      -h, --help         show this help message and exit
      --repodir REPODIR  path to the git project directory
      --checkout         checkout after fetch
      --branch BRANCH    local branch to create (default:
                         gerrit/<number>/<patchset>)
      --no-branch        do not create a local branch

Command git-gerrit-help::

    
    Commands for gerrit code review:
    
        git gerrit-help              List commands.
        git gerrit-query             Search gerrit.
        git gerrit-fetch             Fetch by gerrit number.
        git gerrit-checkout          Fetch then checkout by gerrit number.
        git gerrit-log               Show oneline log with gerrit numbers.
        git gerrit-unpicked          Find gerrit numbers on upstream branch not cherry picked.
        git gerrit-cherry-pick       Cherry pick from upstream branch by gerrit number.
        git gerrit-install-hooks     Install git hooks to create gerrit change-ids.
    
    Show command details with:
    
        git gerrit-<command> -h

Command git-gerrit-install-hooks::

    usage: git-gerrit-install-hooks [-h]
    
    Install git hooks to create gerrit change-ids.
    
    optional arguments:
      -h, --help  show this help message and exit

Command git-gerrit-log::

    usage: git-gerrit-log [-h] [--repodir REPODIR] [--format FORMAT] [-n NUMBER]
                          [-r] [-l]
                          [revision]
    
    Show oneline log with gerrit numbers.
    
    positional arguments:
      revision              revision range
    
    optional arguments:
      -h, --help            show this help message and exit
      --repodir REPODIR     path to the git project directory
      --format FORMAT       output format (default: "{number} {hash} {subject}")
      -n NUMBER, --number NUMBER
                            number of commits
      -r, --reverse         reverse order
      -l, --long-hash       show full sha1 hash
    
    format fields: number, hash, subject

Command git-gerrit-query::

    usage: git-gerrit-query [-h] [--repodir REPODIR] [-n LIMIT] [--format FORMAT]
                            [--dump] [--details]
                            <term> [<term> ...]
    
    Search gerrit.
    
    positional arguments:
      <term>                search term
    
    optional arguments:
      -h, --help            show this help message and exit
      --repodir REPODIR     path to the git project directory
      -n LIMIT, --number LIMIT
                            limit the number of results
      --format FORMAT       output format string
      --dump                dump data
      --details             get extra details

Command git-gerrit-unpicked::

    usage: git-gerrit-unpicked [-h] [-u UPSTREAM_BRANCH] downstream_branch
    
    Find gerrit numbers on upstream branch not cherry picked.
    
    positional arguments:
      downstream_branch     downstream branch name
    
    optional arguments:
      -h, --help            show this help message and exit
      -u UPSTREAM_BRANCH, --upstream-branch UPSTREAM_BRANCH
                            upstream branch name



See Also
========

See the `git-review`_ project for a more complete git/gerrit workflow tool.

.. _git-review: https://www.mediawiki.org/wiki/Gerrit/git-review

