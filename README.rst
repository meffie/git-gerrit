git-gerrit
==========

**git-gerrit** is command line tool for the `Gerrit code review system`_, with an
emphasis on the Gerrit legacy numerical identifiers.  The heavy lifting is done
with the **pygerrit2** package to access the Gerrit REST API.

.. _Gerrit code review system: https://www.gerritcodereview.com/

**git-gerrit** is compatible with Python 2 and Python 3.

Commands
========

.. code-block:: console

    git gerrit-checkout          Fetch then checkout by gerrit number.
    git gerrit-cherry-pick       Cherry pick from upstream branch by gerrit number to make a new gerrit.
    git gerrit-fetch             Fetch by gerrit number.
    git gerrit-help              List commands.
    git gerrit-install-hooks     Install git hooks to create gerrit change-ids.
    git gerrit-log               Show oneline log with gerrit numbers.
    git gerrit-query             Search gerrit.
    git gerrit-update            Update gerrits matching search terms.
    git gerrit-unpicked          Find gerrit numbers on upstream branch not cherry picked.
    git gerrit-version           Print version and exit.

Installation
============

.. _pipx: https://pipx.pypa.io/stable/

Install with `pipx`_::

    $ pipx install git-gerrit

Be sure your ``PATH`` has been updated to run **pipx** installed commands::

    $ pipx ensurepath

If **pipx** is not available, then install in a project local virtualenv::

    $ cd <my-project-directory>
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    (.venv) $ pip install -U pip setuptools
    (.venv) $ pip install git-gerrit


Setup
=====

Set the Gerrit host and project names in your local git repo under Gerrit code
review::

    $ cd <my-project-directory>
    $ git config gerrit.host <gerrit-hostname>
    $ git config gerrit.project <gerrit-project>

Install the Gerrit provided ``commit-msg`` git-hook and the git-gerrrit ``prepare-commit-msg``
git hook::

    $ git gerrit-install-hooks

Examples
========

Setup a local OpenAFS git repo::

    $ git clone git://git.openafs.org/openafs.git # (if not already cloned)
    $ cd openafs
    $ git config --local gerrit.host gerrit.openafs.org
    $ git config --local gerrit.project openafs
    $ git gerrit-install-hooks

Find open gerrits on the master branch::

    $ git gerrit-query is:open branch:master
    13030 redhat: Make separate debuginfo for kmods work with recent rpm
    13031 redhat: PACKAGE_VERSION macro no longer exists
    13021 autoconf: update curses.m4

Find the gerrit numbers and current patchset numbers of the gerrits open on the
`master` branch::

    $ git gerrit-query --format='{number},{patchset} {subject}' is:open branch:master
    13832,9 IPV6 prep: introduce helpers for formatting network addrs
    13926,2 afs: client read-only mode
    13927,2 Do not build shared-only libs for --disable-shared

Find links to the open gerrits on the `master` branch::

    $ git gerrit-query --format='{url} {subject}' is:open branch:master
    https://gerrit.example.com/13832 IPV6 prep: introduce helpers for formatting network addrs
    https://gerrit.example.com/13926 afs: client read-only mode
    https://gerrit.example.com/13927 Do not build shared-only libs for --disable-shared

Find gerrits with subjects containing the term 'debuginfo'::

    $ git gerrit-query debuginfo
    13030 redhat: Make separate debuginfo for kmods work with recent rpm
    13029 redhat: Create unique debuginfo packages for kmods
    12818 redhat: separate debuginfo package for kmod rpm

Find the branch names of gerrits with the subject containing the term 'debuginfo'::

    $ git gerrit-query --format='{branch:>20s} {_number} {subject}' debuginfo
                  master 13030 redhat: Make separate debuginfo for kmods work with recent rpm
    openafs-stable-1_6_x 13029 redhat: Create unique debuginfo packages for kmods
    openafs-stable-1_6_x 12818 redhat: separate debuginfo package for kmod rpm

List the gerrit topics on a branch::

    $ git gerrit-query --format='{topic}' is:open branch:master | sort -u
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

Show gerrit numbers in the checked out branch in the local git repo::

    $ git gerrit-log
    12958 f47cb2d Suppress statement not reached warnings under Solaris Studio
    12957 306f0f3 afs: squash empty declaration warning
    12955 e006609 libafs: git ignore build artifacts on Solaris

Show gerrit numbers by a revision in the local git repo::

    $ git gerrit-log openafs-stable-1_8_0
    12953 a08327f Update NEWS for 1.8.0 final release
    12938 acb0e84 afs_pioctl: avoid -Wpointer-sign
    12950 b73863b LINUX: fix RedHat 7.5 ENOTDIR issues

Show gerrit numbers by a range of revisions in the local git repo::

    $ git gerrit-log 607eba34d..origin/openafs-stable-1_8_x
    13268 554176bd2 LINUX: Update to Linux struct iattr->ia_ctime to timespec64 with 4.18
    13266 eb107ed5c Make OpenAFS 1.8.1
    13265 8de978420 Update NEWS for 1.8.1

Show just the gerrit numbers and subjects in the local git repo::

    $ git gerrit-log --format='{number}: {subject}'
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

Add reviewers to the **foobar** topic::

    $ git gerrit-update --add-reviewer="ty@example.com" branch:master is:open topic:foobar

Abandon all of the changes for the **baz** topic::

    $ git gerrit-update --abandon --message="nevermind" branch:master topic:baz


Using git aliases
=================

Complex queries can be saved as git aliases. For example to create an alias
called ``gerrit-assigned`` to show the gerrits which have not been reviewed
yet::

    [alias]
    # Show assigned reviews.
    # (Replace <gerrit-account-id> with your gerrit account number.)
    gerrit-assigned = gerrit-query \
      --format='"{url} ({branch}) {subject}"' \
      is:open \
      AND reviewer:<gerrit-account-id> \
      AND label:Code-Review=0,<gerrit-account-id> \
      AND NOT owner:<gerrit-account-id> \
      AND NOT label:Code-Review=-2

See Also
========

See the `git-review`_ project for a more complete git/gerrit workflow tool.

.. _git-review: https://www.mediawiki.org/wiki/Gerrit/git-review
