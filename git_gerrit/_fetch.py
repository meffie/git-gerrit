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
from sh.contrib import git
from sh import ErrorReturnCode_1
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

def fetch(number, repodir=None, branch=None, checkout=False, **kwargs):
    """
    Fetch a gerrit by the legacy change number.

    args:
        number (int): legacy gerrit number
        branch (str,None,False):
                      create a local branch unless False
                      use branch 'gerrit/<number>/<patchset> if None
        checkout (bool): checkout the fetched commit
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
    if branch is False:
        refs = '{0}'.format(revision['ref'])
    elif branch is None:
        branch = 'gerrit/{0}/{1}'.format(number, revision['_number'])
        refs = '{0}:{1}'.format(revision['ref'], branch)
    if branch and branch_exists(branch):
        print('branch {0} already exists'.format(branch))
        return

    print('fetching {0} patchset {1}'.format(number, revision['_number']))
    git.fetch(url, refs, _cwd=repodir)
    if branch:
        print('fetched {0} to branch {1}'.format(number, branch))
    else:
        print('fetched {0} to FETCH_HEAD'.format(number))
    if checkout:
        if branch:
            git.checkout(branch, _cwd=repodir)
            print('checked out branch {0}'.format(branch))
        else:
            git.checkout('FETCH_HEAD', _cwd=repodir)
            print('checked out FETCH_HEAD')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='fetch commits from gerrit')
    parser.add_argument('--repodir', help='path to the git project directory', default=None)
    parser.add_argument('--checkout', default=False, action='store_true',
                        help='checkout after fetch')
    parser.add_argument('--no-branch', default=None, dest='branch', action='store_false',
                        help='do not create a local branch')
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = parser.parse_args()
    try:
        fetch(**(vars(args)))
    except GerritConfigError as e:
        print("Error:", e.message)
    except GerritNotFoundError as e:
        print("Error:", e.message)

if __name__ == '__main__':
    main()
