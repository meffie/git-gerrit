git-gerrit
==========

**git-gerrit** is command line tool for the Gerrit code review system, with an
emphasis on the Gerrit legacy numerical identifiers.  The heavy lifting is done
with the **pygerrit2** package to access the Gerrit REST API.

**git-gerrit** is compatible with Python 2 and Python 3.

Commands::

    git gerrit-query -- search for gerrit numbers
    git gerrit-fetch -- fetch gerrits by number
    git gerrit-log   -- log oneline with gerrit numbers

Installation
============

Install with pip::

    pip install git-gerrit

To install from source, clone the git repo and install with the provided
makefile.  If found, the makefile will run **pip** to install the package and
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

    $ git gerrit-query branch:master status:open NOT label:Code-Review=-2 NOT reviewer:$USER

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

Show gerrit numbers by a revision (revision ranges work as well)::

    $ git gerrit-log -n3 openafs-stable-1_8_0
    12953 a08327f Update NEWS for 1.8.0 final release
    12938 acb0e84 afs_pioctl: avoid -Wpointer-sign
    12950 b73863b LINUX: fix RedHat 7.5 ENOTDIR issues

Show just the gerrit numbers and subjects::

    $ git gerrit-log -n3 --format='{number}: {subject}'
    12958: Suppress statement not reached warnings under Solaris Studio
    12957: afs: squash empty declaration warning
    12955: libafs: git ignore build artifacts on Solaris

See Also
========

See the **git-review** project for a more complete git/gerrit workflow tool.
