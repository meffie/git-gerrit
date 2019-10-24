# Copyright (c) 2018 Sine Nomine Associates
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

"""Command line gerrit fetch"""

from __future__ import print_function
from __future__ import unicode_literals
import sys
from sh.contrib import git
from sh import ErrorReturnCode_1
from git_gerrit._help import command_desc
from git_gerrit._query import query
from git_gerrit._cfg import Config, GerritConfigError

class GerritNotFoundError(Exception):
    pass

def branch_exists(branch):
    """Returns true if branch exists."""
    try:
        git('show-ref', '--quiet', 'refs/heads/{0}'.format(branch))
        return True
    except ErrorReturnCode_1:
        return False

def fetch(number, repodir=None, no_branch=False, branch=None, checkout=False, **kwargs):
    """
    Fetch a gerrit by the legacy change number.

    args:
        number (int): legacy gerrit number
        no_branch (bool): skip local branch when True
        branch (str,None): local branch name to fetch to
                           default: 'gerrit/<number>/<patchset>'
        checkout (bool): checkout after fetch
    returns:
        None
    raises:
        GerritNotFoundError
    """
    config = Config(repodir)
    print('searching for gerrit {0}'.format(number))
    changes = query(str(number), current_revision=True, repodir=repodir)
    if not changes:
        raise GerritNotFoundError('gerrit {0} not found'.format(number))
    revisions = changes[0]['revisions']
    revision = list(revisions.values())[0]
    print('found patchset number {0}'.format(revision['_number']))
    url = 'https://{0}/{1}'.format(config['host'], config['project'])

    if no_branch:
        refs = '{0}'.format(revision['ref'])
        print('fetching {0} patchset {1}'.format(number, revision['_number']))
        git.fetch(url, refs, _cwd=repodir)
        print('fetched {0} to FETCH_HEAD'.format(number))
        if checkout:
            git.checkout('FETCH_HEAD', _cwd=repodir)
            print('checked out FETCH_HEAD')
    else:
        if branch is None:
            branch = 'gerrit/{0}/{1}'.format(number, revision['_number'])
        if branch_exists(branch):
            print('branch {0} already exists; remove it or try with --no-branch'.format(branch))
            return 1
        refs = '{0}:{1}'.format(revision['ref'], branch)
        print('fetching {0} patchset {1} to branch {2}'.format(number, revision['_number'], branch))
        git.fetch(url, refs, _cwd=repodir)
        print('fetched {0} to branch {1}'.format(number, branch))
        if checkout:
            git.checkout(branch, _cwd=repodir)
            print('checked out branch {0}'.format(branch))

def main():
    import argparse
    parser = argparse.ArgumentParser(description=command_desc('fetch'))
    parser.add_argument('--repodir', help='path to the git project directory', default=None)
    parser.add_argument('--checkout', default=False, action='store_true',
                        help='checkout after fetch')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--branch', default=None,
                        help='local branch to create (default: gerrit/<number>/<patchset>)')
    group.add_argument('--no-branch', default=False, action='store_true',
                        help='do not create a local branch')
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = parser.parse_args()
    code = 0
    try:
        fetch(**(vars(args)))
    except GerritConfigError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 1
    except GerritNotFoundError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 2
    return code

if __name__ == '__main__':
    sys.exit(main())
