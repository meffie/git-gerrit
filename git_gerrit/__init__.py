# Copyright (c) 2018-2019 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Git helpers for the Gerrit code review system, with an emphasis on the Gerrit
old-style numeric identifiers.
"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import stat
import subprocess
import sys

import pygerrit2.rest
import sh
try:
    from urllib.parse import urlencode
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlencode
    from urllib import urlretrieve

from git_gerrit.config import Config
from git_gerrit.unicode import cook
from git_gerrit.error import GitGerritError
from git_gerrit.error import GitGerritConfigError
from git_gerrit.error import GitGerritFormatError
from git_gerrit.error import GitGerritNotFoundError
from git_gerrit.error import GitGerritHookDirNotFound
try:
    from git_gerrit import _version
    VERSION = _version.__version__
except ImportError:
    VERSION = None

_hush_linter = [
    GitGerritError,
    GitGerritConfigError,
    GitGerritFormatError,
    GitGerritNotFoundError,
    GitGerritHookDirNotFound,
]

CHANGE_FIELDS = [
    # Gerrit provided fields.
    'branch',
    'change_id',
    'created',
    'current_revision',
    'deletions',
    'hashtags',
    'id',
    'insertions',
    'owner',
    'project',
    'status',
    'subject',
    'submittable',
    'submitted',
    'topic',  # Defaults to 'no-topic' instead of empty or None.
    'updated',
    # Added from gerrit provided revisions sub-fields.
    'number',
    'patchset',
    'ref',
    'localref',
    'hash',
    'host',
    'url',
]

GIT_HOOK = """\
#!/bin/bash
# Change the gerrit change-id in a commit message. To be used when cherry
# picking already merged commits to a different branch.
#
# usage: GERRIT_CHERRY_PICK=yes git cherry-pick -x <commit>
#
test "$GERRIT_CHERRY_PICK" = "yes" || exit 0
grep '^(cherry picked from commit' "$1" >/dev/null || exit 0
grep '^Change-Id:' "$1" >/dev/null || exit 0
echo "prepare-commit-msg: creating new gerrit Change-Id"
sed -i '/^Change-Id:/d' "$1"
.git/hooks/commit-msg "$1"
"""

def _chmod(filename, mode):
    """
    Wrapper for os.chmod(); converts rwx... string to mode bits.
    """
    bit = [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
           stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
           stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]
    bits = 0
    for i, char in enumerate('rwxrwxrwx'):
        if mode[i] == char:
            bits |= bit[i]
    os.chmod(filename, bits)

def _branch_exists(branch, repodir=None):
    """
    Determine if branch exists in the local repo.
    """
    git = sh.Command('git').bake(_cwd=repodir, _tty_out=False)
    try:
        git('show-ref', '--quiet', 'refs/heads/{0}'.format(branch), _cwd=repodir)
        return True
    except sh.ErrorReturnCode:
        return False

def _get_hashes(branch, repodir=None):
    """
    Returns the commit sha1 hashes for the given branch as a set().
    """
    git = sh.Command('git').bake(_cwd=repodir, _tty_out=False)
    hashes = set()
    for line in git.log(branch, format="%H", _iter=True, _cwd=repodir):
        line = line.rstrip()
        hashes.add(line)
    return hashes

def _get_cherry_picked(branch, repodir=None):
    """
    Find which commits have been cherry picked. Returns a dictionary; for
    each entry, the key is the commit sha1 of the commit on the branch, and
    value is the cherry picked from commit sha1.
    """
    git = sh.Command('git').bake(_cwd=repodir, _tty_out=False)
    picked = {}
    to_ = None
    from_ = None
    for line in git.log(branch, _iter=True, _cwd=repodir):
        line = cook(line)
        line = line.rstrip()
        m = re.match(r'commit (\w+)', line)
        if m:
            if to_ and from_:
                picked[to_] = from_
            to_ = m.group(1)
            from_ = None
            continue
        m = re.match(r'\s+\(cherry picked from commit (\w+)\)', line)
        if m:
            from_ = m.group(1) # Save the last one see in this commit message.
    if to_ and from_:
        picked[to_] = from_
    return picked


def cherry_pick(number, branch='origin/master', repodir=None):
    """
    Cherry pick change from upstream branch and create a new gerrit identifier
    in the commit messsage.

    args:
        number (int): gerrit numeric identifier
        branch (str): upstream branch to pick from
    returns:
        non-zero on error
    """
    git = sh.Command('git').bake(_cwd=repodir, _tty_out=False)
    hash = None
    for commit in log(revision=branch, shorthash=False):
        if commit['number'] == number:
            hash = commit['hash']
            break
    if not hash:
        sys.stderr.write(
            'Failed to find gerrit number {0} on branch {1}.\n'\
            .format(number, branch))
        return 1

    # We want to generate a new gerrit Change-Id for this commit.  Set the
    # following env var to instruct the prepare-commit-mg hook (created by git
    # gerrit-install-hooks) to remove the old change-id in the commit message
    # and run the gerrit commit-msg hook to generate a brand new Change-Id.
    env = os.environ.copy()
    env['GERRIT_CHERRY_PICK'] = 'yes'
    code = 0
    try:
        print(git('cherry-pick', '-x', hash, _env=env))
    except sh.ErrorReturnCode as e:
        sys.stderr.write('Failed to cherry-pick {0}\n{1}\n'.format(hash, e.stderr))
        code = e.exit_code
    return code

def current_change(number, repodir=None):
    """
    Look up the current change in gerrit.

    args:
        number (int):  the gerrit change number
        repodir (str): optional path to the git repo directory (for git configuration)
    returns:
        a current change dictionary (including the current patchset number)
    """
    changes = list(query('change:{0}'.format(number), limit=1, current_revision=True, repodir=repodir))
    if not changes or len(changes) != 1:
        raise GitGerritNotFoundError('gerrit {0} not found'.format(number))
    change = changes[0]
    return change

def fetch(number, no_branch=False, branch='gerrit/{number}/{patchset}', checkout=False, repodir=None):
    """
    Fetch a gerrit by the legacy change number.

    args:
        number (int):     legacy gerrit number
        no_branch (bool): skip local branch when True
        branch (str):     local branch name to fetch to.
                          default: 'gerrit/{number}/{patchset}'
        checkout (bool):  checkout after fetch
        repodir (str):    local git repo directory (default: current)
    returns:
        None
    raises:
        GitGerritNotFoundError
    """
    config = Config(repodir)
    git = sh.Command('git').bake(_cwd=repodir, _tty_out=False)
    print('searching for gerrit {0}'.format(number))
    change = current_change(number, repodir)
    print('found patchset number {0}'.format(change['patchset']))
    url = 'https://{0}/{1}'.format(config['host'], config['project'])

    if no_branch:
        refs = '{0}'.format(change['ref'])
        print('fetching {0} patchset {1}'.format(number, change['patchset']))
        git.fetch(url, refs, _cwd=repodir)
        print('fetched {0} to FETCH_HEAD'.format(number))
        if checkout:
            git.checkout('FETCH_HEAD', _cwd=repodir)
            print('checked out FETCH_HEAD')
    else:
        if not branch:
            print('no branch specified')
            return 1
        branch = branch.format(**change)
        if _branch_exists(branch):
            print('branch {0} already exists'.format(branch))
            return 1
        patchset = change['patchset']
        refs = '{0}:{1}'.format(change['ref'], branch)
        print('fetching {0},{1} to branch {2}'.format(number, patchset, branch))
        git.fetch(url, refs, _cwd=repodir)
        print('fetched {0},{1} to branch {2}'.format(number, patchset, branch))
        if checkout:
            git.checkout(branch, _cwd=repodir)
            print('checked out branch {0}'.format(branch))

def install_hooks():
    """
    Install git hooks for Gerrit and Git-Gerrit.
    """
    config = Config()
    hookdir = '.git/hooks'

    if not os.path.isdir(hookdir):
        raise GitGerritHookDirNotFound()

    # Install the gerrit commit-msg hook.
    commit_msg = os.path.join(hookdir, 'commit-msg')
    if os.path.exists(commit_msg):
        sys.stdout.write('{0} git hook already present.\n'.format(commit_msg))
    else:
        url = 'https://{0}/tools/hooks/commit-msg'.format(config['host'])
        sys.stdout.write('Downloading git hook to {0} ... '.format(commit_msg))
        urlretrieve(url, commit_msg)
        _chmod(commit_msg, 'rwxr-xr-x')
        sys.stdout.write('done.\n')

    # Install our custom prepare-commit-msg hook for cherry picking gerrits.
    prepare_commit_msg = os.path.join(hookdir, 'prepare-commit-msg')
    if os.path.exists(prepare_commit_msg):
        sys.stdout.write('%s hook already present.\n' % prepare_commit_msg)
    else:
        sys.stdout.write('Writing file %s ... ' % prepare_commit_msg)
        with open(prepare_commit_msg, 'w') as f:
            f.write(GIT_HOOK)
        _chmod(prepare_commit_msg, 'rwxr-xr-x')
        sys.stdout.write('done.\n')

    return 0

def log(number=None, reverse=False, shorthash=True, revision=None, repodir=None):
    """
    Retrieve log entries with gerrit numbers (extracted from the commit
    messages) from the local git repository.

    args:
        number (int):     limit the log to these number of entries [optional]
        reverse (bool):   reverse log order
        shorthash (bool): short sha1
        revision (str):   git revision to log (default is HEAD)
        repodir (str):    local git repo directory (default: current)
    yields:
        dictionary with keys: 'hash', 'subject', 'number', 'author', 'email'
    """
    git = sh.Command('git').bake(_cwd=repodir, _tty_out=False)

    args = []
    if revision:
        args.append(revision)

    if shorthash:
        hashfmt = '%h'
    else:
        hashfmt = '%H'
    options = {}
    options['pretty'] = 'hash:{0}%nsubject:%s%nauthor:%an%nemail:%ae%n%b%%%%'.format(hashfmt)
    options['reverse'] = reverse
    if number:
        options['max-count'] = number
    options['_iter'] = True

    fields = {'hash':'', 'subject':'', 'number':'-', 'author': '', 'email': ''}
    for line in git.log(*args, **options):
        line = cook(line)
        line = line.strip()
        m = re.match(r'^hash:(.*)', line)
        if m:
            fields['hash'] = m.group(1)
            continue
        m = re.match(r'^subject:(.*)', line)
        if m:
            fields['subject'] = m.group(1)
            continue
        m = re.match(r'^author:(.*)', line)
        if m:
            fields['author'] = m.group(1)
            continue
        m = re.match(r'^email:(.*)', line)
        if m:
            fields['email'] = m.group(1)
            continue
        m = re.match(r'^Reviewed-on: .*/([0-9]+)$', line)
        if m:
            fields['number'] = int(m.group(1)) # get last one
            continue
        m = re.match(r'^%%$', line)
        if m:
            yield fields
            fields = {'hash':'', 'subject':'', 'number':'-', 'author': '', 'email': ''}

def query(search, limit=None, details=False, repodir=None, **options):
    """Search gerrit for changes.

    args:
        search (str): one or more Gerrit search terms
        options (dict): zero or more Gerrit search options
    returns:
        list of change info dicts
    """
    config = Config(repodir)
    if 'project:' not in search:
        search += ' project:{0}'.format(config['project'])
    if not 'current_revision' in options:
        options['current_revision'] = True

    params = [('q', search)]
    if limit:
        params.append(('n', limit))
    for option in options:
        if options[option] is True:
            params.append(('o', option.upper()))
    query = '/changes/?{0}'.format(urlencode(params))

    remote = config.get('remote', default='origin')
    url = "https://{0}".format(config['host'])
    gerrit = pygerrit2.rest.GerritRestAPI(url)
    for change in gerrit.get(query):
        change['number'] = change['_number']
        change['hash'] = change['current_revision'] # alias
        change['patchset'] = change['revisions'][change['current_revision']]['_number']
        change['ref'] = change['revisions'][change['current_revision']]['ref']
        change['localref'] = change['ref'].replace('refs/', remote+'/')
        change['host'] = config['host']
        change['url'] = "https://{0}/{1}".format(config['host'], change['_number'])
        if not 'topic' in change:
            change['topic'] = 'no-topic'  # default for --format "{topic}"
        if details:
            change_id = change['change_id']
            change['details'] = gerrit.get('/changes/{0}/detail'.format(change_id))
        yield change

def review(number, repodir=None, branch=None,
           message=None, code_review=None, verified=None,
           abandon=False, restore=False,
           add_reviewers=None, verbose=False):
    """ Submit review to gerrit using the ssh command line interface.

    Note: This method requires authentication. Create a gerrit account and
    import your ssh public key. See the Gerrit documentation.

    args:
        number (int): gerrit id (requried)
        branch (str): branch change is located (optional)
        message (str): review message to add (optional)
        code_review (str): code review vote to add (optional)
        verified (str): verication vote to add (optional)
        abandon (bool): set change status to abandoned
        restore (bool): set change status back to open if abandoned
    returns:
        None
    """
    if (abandon and restore):
        raise ValueError('Specify only one of "abandon" or "restore".')
    if add_reviewers is None:
        add_reviewers = []

    ssh = sh.Command('ssh')
    config = Config(repodir)
    host = config['host']
    project = config['project']
    port = config.get('port', default='29418')

    def arg(name, value):
        if value is True:
            args.append('--'+name)
        elif value:
            args.append('--'+name)
            args.append(subprocess.list2cmdline([value]))

    args = []
    arg('message', message)
    arg('code-review', code_review)
    arg('verified', verified)
    arg('abandon', abandon)
    arg('restore', restore)
    if args:
        arg('project', project)
        arg('branch', branch)
        change = current_change(number, repodir)
        changeid = '{0},{1}'.format(number, change['patchset'])
        args.append(changeid)
        if verbose:
            print('running: ssh', '-p', port, host, 'gerrit', 'review', *args)
        ssh('-p', port, host, 'gerrit', 'review', *args)

    args = []
    for reviewer in add_reviewers:
        arg('add', reviewer)
    if args:
        arg('project', project)
        arg('branch', branch)
        args.append(number)
        if verbose:
            print('running: ssh', '-p', port, host, 'gerrit', 'set-reviewers', *args)
        ssh('-p', port, host, 'gerrit', 'set-reviewers', *args)

    return 0

def unpicked(upstream_branch='HEAD', downstream_branch=None, repodir=None):
    """
    Find commits on the master ('upstream') branch which are not on the stable
    ('downstream') branch and have not been cherry picked on to the stable
    branch.

    args:
        upstream_branch:
        downstream_branch:
    """
    if not downstream_branch:
        raise ValueError('Downstream branch name is required.')

    # Lookup the sha1s for each branch.
    u = _get_hashes(upstream_branch)
    d = _get_hashes(downstream_branch)

    # Find which commits have been cherry picked.
    #
    # Conventionally, commits are cherry picked from the upstream branch on to
    # the downstream branch, but in rare cases cherry picks can go in the
    # opposite direction. A change is merged is merged on the "stable" branch
    # first and cherry picked on to the master branch later.
    cu = set(_get_cherry_picked(upstream_branch).keys())
    cd = set(_get_cherry_picked(downstream_branch).values())

    # Commits not in the downstream branch, and not cherry picked to the down
    # stream branch (nor cherry picked from the downstream branch).
    x = u - (d | cd | cu)

    # Output them in git log order.
    for commit in log(revision=upstream_branch, shorthash=False):
        if commit['hash'] in x:
            yield commit
