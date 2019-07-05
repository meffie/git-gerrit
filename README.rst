git-gerrit
==========

**git-gerrit** is command line tool for the `Gerrit code review system`_, with an
emphasis on the Gerrit legacy numerical identifiers.  The heavy lifting is done
with the **pygerrit2** package to access the Gerrit REST API.

.. _Gerrit code review system: https://www.gerritcodereview.com/

**git-gerrit** is compatible with Python 2 and Python 3.

Commands::

    git gerrit-query -- search for gerrit numbers
    git gerrit-fetch -- fetch gerrits by number
    git gerrit-log   -- log oneline with gerrit numbers
    git gerrit-unpicked -- list gerrit numbers which have not been cherry-picked

Installation
============

Install with pip::

    pip install git-gerrit

To install from source, clone the git repo and install with the provided
makefile.  If found, `make` will run `pip` to install the package and
requirements::

    git clone https://github.com/meffie/git-gerrit.git
    cd git-gerrit
    make install

Set the Gerrit host and project names in the local git configuration before
running the **git-gerrit** commands::

    cd <project>
    git config gerrit.host <gerrit-hostname>
    git config gerrit.project <gerrit-project>

Examples
========

Use the openafs.org gerrit::

    $ git config --local gerrit.host gerrit.openafs.org
    $ git config --local gerrit.project openafs

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

    $ git gerrit-fetch --checkout 13000

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


See Also
========

See the `git-review`_ project for a more complete git/gerrit workflow tool.

.. _git-review: https://www.mediawiki.org/wiki/Gerrit/git-review
