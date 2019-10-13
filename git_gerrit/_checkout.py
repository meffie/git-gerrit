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

"""Command line gerrit checkout"""

from __future__ import print_function
from __future__ import unicode_literals
import sys
from git_gerrit._fetch import fetch,GerritNotFoundError
from git_gerrit._cfg import GerritConfigError

def main():
    import argparse
    parser = argparse.ArgumentParser(description='checkout a commit from gerrit')
    parser.add_argument('--repodir', help='path to the git project directory', default=None)
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = parser.parse_args()
    code = 0
    try:
        fetch(args.number, repodir=args.repodir, branch=None, checkout=True)
    except GerritConfigError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 1
    except GerritNotFoundError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 2
    return code

if __name__ == '__main__':
    sys.exit(main())
