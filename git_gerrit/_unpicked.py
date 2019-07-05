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

"""git log with gerrit numbers"""

from __future__ import print_function
from __future__ import unicode_literals

import re
from git_gerrit._unicode import cook, asciitize
from git_gerrit._log import log
from sh.contrib import git

def _get_hashes(branch):
    """Returns the set of commit hashes for the given branch."""
    hashes = set()
    for line in git.log(branch, format="%H", _iter=True):
        line = line.rstrip()
        hashes.add(line)
    return hashes

def _get_cherry_picked(branch):
    """Find which commits have been cherry picked. Returns a dictionary; for
    each entry, the key is the commit sha1 of the commit on the branch, and
    value is the cherry picked from commit sha1."""
    picked = {}
    to_ = None
    from_ = None
    for line in git.log(branch, _iter=True):
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

def unpicked(upstream_branch='HEAD', downstream_branch=None, repodir=None, **kwargs):
    """
    Find commits on the master branch which are not on the stable branch
    and have not been cherry picked on to the stable branch.
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

def main():
    import argparse
    parser = argparse.ArgumentParser(
               description='find commits which have not been cherry-picked',
               epilog='')
    parser.add_argument('-u', '--upstream-branch',  help='upstream branch name', default='HEAD')
    parser.add_argument('downstream_branch', help='downstream branch name')
    args = vars(parser.parse_args())

    for commit in unpicked(**args):
        try:
            print('{number} {hash} {subject}'.format(**commit))
        except UnicodeEncodeError:
            # Fall back to ascii only.
            commit['subject'] = asciitize(commit['subject'])
            print('{number} {hash} {subject}'.format(**commit))

if __name__ == '__main__':
    main()
