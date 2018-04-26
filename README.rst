git-gerrit
==========

Command line tool for the Gerrit code review system to search and fetch
patchsets, with an emphasis on the human-readable legacy Gerrit numbers.
The heavy lifting is done with the pygerrit2 package.

Usage::

    git gerrit-query <search terms>
    git gerrit-fetch [--no-branch] [--checkout] <number>

Installation
============

The scripts can be installed with the makefile. If in the PATH, pip will
be used for the installation, otherwise the setup.py will be used::

    make install


Configuration
=============

Set the Gerrit host and project names in the local git configuration::

    git config gerrit.host <gerrit-hostname>
    git config gerrit.project <gerrit-project>

Examples
========

Use the openafs.org gerrit::

    $ git config --local gerrit.host gerrit.openafs.org
    $ git config --local gerrit.project openafs

Find open gerrits on the master branch::

    $ git gerrit-query is:open branch:master limit:5
    13030 redhat: Make separate debuginfo for kmods work with recent rpm
    13031 redhat: PACKAGE_VERSION macro no longer exists
    13021 autoconf: update curses.m4
    12202 autoconf: autoupdate macros
    12203 Remove obsolete retsigtype

Find gerrits with subjects containing the term 'debuginfo'::

    $git gerrit-query debuginfo limit:5
    13030 redhat: Make separate debuginfo for kmods work with recent rpm
    13029 redhat: Create unique debuginfo packages for kmods
    12818 redhat: separate debuginfo package for kmod rpm
    12977 redhat: Create unique debuginfo packages for kmods
    12986 redhat: Create unique debuginfo packages for kmods

Fetch a gerrit::

    git gerrit-fetch 12977

Checkout a given gerrit::

    git gerrit-fetch --checkout 13000

Cherry-pick a gerrit onto the current branch::

    git gerrit-fetch --no-branch 13001 && git cherry-pick FETCH_HEAD

See Also
========

See the git-review project for a more complete toolset for git/gerrit
workflows.
