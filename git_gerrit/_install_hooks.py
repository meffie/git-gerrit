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

"""Install gerrit git hooks"""

from __future__ import print_function
from __future__ import unicode_literals
import os
import stat
import sys
import requests
from git_gerrit._cfg import Config, GerritConfigError

class GerritHookDirNotFound(Exception):
    pass

script = """\
#!/bin/bash
# Change the gerrit change-id in a commit message. To be used when cherry
# picking already merged commits to a different branch.
#
# Usage:
#
#    GERRIT_CHERRY_PICK=yes git cherry-pick -x <commit>
#
test "$GERRIT_CHERRY_PICK" = "yes" || exit 0
grep '^(cherry picked from commit' "$1" >/dev/null || exit 0
grep '^Change-Id:' "$1" >/dev/null || exit 0
echo "prepare-commit-msg: creating new gerrit Change-Id"
sed -i '/^Change-Id:/d' "$1"
.git/hooks/commit-msg "$1"
"""

def mode(m):
    bit = [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
           stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
           stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]
    mode = 0
    for i,char in enumerate('rwxrwxrwx'):
        if m[i] == char:
            mode |= bit[i]
    return mode

def install_hooks():
    config = Config()
    hookdir = '.git/hooks'

    if not os.path.isdir(hookdir):
        raise GerritHookDirNotFound()

    # Install the gerrit commit-msg hook.
    commit_msg = os.path.join(hookdir, 'commit-msg')
    if os.path.exists(commit_msg):
        sys.stdout.write('%s hook already present.\n' % commit_msg)
    else:
        url = 'https://%s/tools/hooks/commit-msg' % config['host']
        r = requests.get(url)
        sys.stdout.write('Downloading commit-msg hook to %s ... ' % commit_msg)
        with open(commit_msg, 'wb') as f:
            f.write(r.content)
        os.chmod(commit_msg, mode('rwxr-xr-x'))
        sys.stdout.write('done.\n')

    # Install our custom prepare-commit-msg hook for cherry picking gerrits.
    prepare_commit_msg = os.path.join(hookdir, 'prepare-commit-msg')
    if os.path.exists(prepare_commit_msg):
        sys.stdout.write('%s hook already present.\n' % prepare_commit_msg)
    else:
        sys.stdout.write('Writing file %s ... ' % prepare_commit_msg)
        with open(prepare_commit_msg, 'w') as f:
            f.write(script)
        os.chmod(prepare_commit_msg, mode('rwxr-xr-x'))
        sys.stdout.write('done.\n')

    return 0

def main():
    import argparse
    parser = argparse.ArgumentParser(description='install gerrit git hooks')
    parser.parse_args()

    try:
        code = install_hooks()
    except GerritConfigError as e:
        sys.stderr.write('Error: %s\n' % e.message)
        code = 1
    except GerritHookDirNotFound:
        sys.stderr.write('.git/hook directory not found.\n')
        code = 2
    return code

if __name__ == '__main__':
    sys.exit(main())
