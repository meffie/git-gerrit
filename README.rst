git-gerrit
==========

**git-gerrit** is command line tool for the `Gerrit code review system`_, with an
emphasis on the Gerrit legacy numerical identifiers.  The heavy lifting is done
with the **pygerrit2** package to access the Gerrit REST API.

.. _Gerrit code review system: https://www.gerritcodereview.com/

**git-gerrit** is compatible with Python 2 and Python 3.

Commands
========

.. begin git-gerrit desc

::

    git gerrit-checkout          Fetch then checkout by gerrit number.
    git gerrit-cherry-pick       Cherry pick from upstream branch by gerrit number to make a new gerrit.
    git gerrit-fetch             Fetch by gerrit number.
    git gerrit-help              List commands.
    git gerrit-install-hooks     Install git hooks to create gerrit change-ids.
    git gerrit-log               Show oneline log with gerrit numbers.
    git gerrit-query             Search gerrit.
    git gerrit-review            Submit review by gerrit number.
    git gerrit-unpicked          Find gerrit numbers on upstream branch not cherry picked.

.. end git-gerrit desc

Installation
============

Install with `pip`::

    $ pip install --user git-gerrit

Install from source::

    $ git clone https://github.com/meffie/git-gerrit.git
    $ cd git-gerrit
    $ make install

Set the Gerrit host and project names in your local git repo under Gerrit code
review::

    $ cd <your-git-directory>
    $ git config gerrit.host <gerrit-hostname>
    $ git config gerrit.project <gerrit-project>

Install the Gerrit provided `commit-msg` git-hook and the git-gerrrit `prepare-commit-msg`
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


Using git aliases
=================

Commonly used queries can be saved as git aliases. For example to show the
gerrits which have not been reviewed yet::

    [alias]
    # git gerrit-todo [<branch>] [<userid>]
    gerrit-todo = "!f() { git-gerrit-query \"branch:${1-master} is:open NOT label:Code-Review>=+1,${2-$USER}\"; }; f"

Command help
============

.. begin git-gerrit help

Command git-gerrit-checkout::

    usage: git-gerrit-checkout [-h] [--branch BRANCH | --no-branch] <number>
    
    Fetch then checkout by gerrit number.
    
    positional arguments:
      <number>         legacy change number
    
    optional arguments:
      -h, --help       show this help message and exit
      --branch BRANCH  local branch to create (default:
                       gerrit/{number}/{patchset})
      --no-branch      do not create a local branch
    
    Configuration variables:
    
      gerrit.host            Specifies the gerrit hostname (required).
      gerrit.project         Specifies the gerrit project name (required).
      gerrit.checkoutbranch  Default git-gerrit-checkout --branch value (optional).
      gerrit.no-branch       Do not create local branches (yes/no) (optional).

Command git-gerrit-cherry-pick::

    usage: git-gerrit-cherry-pick [-h] [-b <branch>] <number>
    
    Cherry pick from upstream branch by gerrit number to make a new gerrit.
    
    positional arguments:
      <number>              legacy change number
    
    optional arguments:
      -h, --help            show this help message and exit
      -b <branch>, --branch <branch>
                            upstream branch (default: origin/master)
    
    Notes:
    
    This command will create a new gerrit Change-Id in the new cherry-picked commit
    if the git hooks have been installed with git-gerrit-install-hooks
    
    Example:
    
      $ git gerrit-install-hooks
      $ git gerrit-query is:merged branch:master 'fix the frobinator'
      1234 fix the frobinator
      ...
      $ git fetch origin
      $ git checkout -b fix origin/the-stable-branch
      ...
      $ git gerrit-cherry-pick 1234 -b origin/master
      [fix f378563c94] fix the frobinator
      Date: Fri Apr 4 10:27:10 2014 -0400
      2 files changed, 37 insertions(+), 12 deletions(-)
      $ git push gerrit HEAD:refs/for/the-stable-branch

Command git-gerrit-fetch::

    usage: git-gerrit-fetch [-h] [--checkout] [--branch BRANCH | --no-branch]
                            <number>
    
    Fetch by gerrit number.
    
    positional arguments:
      <number>         legacy change number
    
    optional arguments:
      -h, --help       show this help message and exit
      --checkout       checkout after fetch
      --branch BRANCH  local branch to create (default:
                       gerrit/{number}/{patchset})
      --no-branch      do not create a local branch
    
    Configuration variables:
    
      gerrit.host           Specifies the gerrit hostname (required).
      gerrit.project        Specifies the gerrit project name (required).
      gerrit.fetchbranch    Default git-gerrit-fetch --branch value (optional).
      gerrit.no-branch      Do not create local branches (yes/no) (optional).

Command git-gerrit-help::

    usage: git-gerrit-help [-h]
    
    List commands.
    
    optional arguments:
      -h, --help  show this help message and exit

Command git-gerrit-install-hooks::

    usage: git-gerrit-install-hooks [-h]
    
    Install git hooks to create gerrit change-ids.
    
    optional arguments:
      -h, --help  show this help message and exit
    
    Configuration variables:
    
      gerrit.host           Specifies the gerrit hostname (required).

Command git-gerrit-log::

    usage: git-gerrit-log [-h] [--format FORMAT] [-n NUMBER] [-r] [-l] [revision]
    
    Show oneline log with gerrit numbers.
    
    positional arguments:
      revision              revision range
    
    optional arguments:
      -h, --help            show this help message and exit
      --format FORMAT       output format (default: "{number} {hash} {subject}")
      -n NUMBER, --number NUMBER
                            number of commits
      -r, --reverse         reverse order
      -l, --long-hash       show full sha1 hash
    
    Available --format template fields: number, hash, subject
    
    Configuration variables:
    
      gerrit.queryformat    Default git-gerrit-query --format value (optional).
      gerrit.remote         Remote name of the localref --format field (default: origin)

Command git-gerrit-query::

    usage: git-gerrit-query [-h] [-n <number>] [-f <format>] [--dump] [--details]
                            <term> [<term> ...]
    
    Search gerrit.
    
    positional arguments:
      <term>                search term
    
    optional arguments:
      -h, --help            show this help message and exit
      -n <number>, --number <number>
                            limit the number of results
      -f <format>, --format <format>
                            output format template (default: "{number} {subject}")
      --dump                debug data dump
      --details             get extra details for debug --dump
    
    Available --format template fields:
    
    branch, change_id, created, current_revision, deletions, hash,
    hashtags, host, id, insertions, localref, number, owner, patchset,
    project, ref, status, subject, submittable, submitted, topic, updated,
    url
    
    Configuration variables:
    
      gerrit.host           Specifies the gerrit hostname (required).
      gerrit.project        Specifies the gerrit project name (required).
      gerrit.queryformat    Default git-gerrit-query --format value (optional).
      gerrit.remote         Remote name of the localref --format field (default: origin)

Command git-gerrit-review::

    usage: git-gerrit-review [-h] [--branch <branch>] [--message <message>]
                             [--code-review {-2,-1,0,+1,+2}]
                             [--verified {-1,0,+1}] [--abandon | --restore]
                             [--add-reviewer <email>]
                             <number>
    
    Submit review by gerrit number.
    
    positional arguments:
      <number>              gerrit change number
    
    optional arguments:
      -h, --help            show this help message and exit
      --branch <branch>     Branch name
      --message <message>   Review message
      --code-review {-2,-1,0,+1,+2}
                            Code review vote
      --verified {-1,0,+1}  Verified vote
      --abandon             Set status to abandoned
      --restore             Set status to open
      --add-reviewer <email>
                            Invite reviewer (this option may be given more than
                            once)
    
    Examples:
    
      $ git gerrit-review --message="Good Job" --code-review="+1" 12345
      $ git gerrit-review --message="Works for me" --verified="+1" 12345
      $ git gerrit-review --add-reviewer="tycobb@yoyodyne.com" --add-reviewer="foo@bar.com" 12345
    
    Configuration variables:
    
      gerrit.host           Specifies the gerrit hostname (required).
      gerrit.project        Specifies the gerrit project name (required).

Command git-gerrit-unpicked::

    usage: git-gerrit-unpicked [-h] [-u UPSTREAM_BRANCH] [-f <format>]
                               downstream_branch
    
    Find gerrit numbers on upstream branch not cherry picked.
    
    positional arguments:
      downstream_branch     downstream branch name
    
    optional arguments:
      -h, --help            show this help message and exit
      -u UPSTREAM_BRANCH, --upstream-branch UPSTREAM_BRANCH
                            upstream branch name
      -f <format>, --format <format>
                            output format template (default: "{number} {hash}
                            {subject}")
    
    Configuration variables:
    
      gerrit.unpickedformat    Default git-gerrit-query --format value (optional).



.. end git-gerrit help

See Also
========

See the `git-review`_ project for a more complete git/gerrit workflow tool.

.. _git-review: https://www.mediawiki.org/wiki/Gerrit/git-review

