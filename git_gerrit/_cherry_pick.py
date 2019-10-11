# Copyright (c) 2019 Sine Nomine Associates
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

"""Cherry pick commits from upstream branch by gerrit number."""

from __future__ import print_function
from __future__ import unicode_literals
import os
import sys
import argparse
from git_gerrit._log import log
from sh.contrib import git
from sh import ErrorReturnCode

BRANCH = 'origin/master'

def cherry_pick(number, branch=BRANCH):
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
        output = git('cherry-pick', '-x', hash, _env=env)
        sys.stdout.write(output.stdout)
    except ErrorReturnCode as e:
        sys.stderr.write('Failed to cherry-pick {0}\n{1}\n'.format(hash, e.stderr))
        code = e.exit_code
    return code

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Cherry pick a commit from an upstream branch by gerrit number.
A new gerrit Change-Id will be created.
""",
        epilog="""\
Example:

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
""")
    parser.add_argument('-b', '--branch', metavar='<branch>',
                        help='upstream branch (default: %s)' % BRANCH,
                        default=BRANCH)
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = parser.parse_args()
    code = cherry_pick(args.number, args.branch)
    return code

if __name__ == '__main__':
    sys.exit(main())
