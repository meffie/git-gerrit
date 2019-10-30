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

"""Command line gerrit review"""

from __future__ import print_function
from __future__ import unicode_literals
import sys
import argparse
from sh import ssh
from subprocess import list2cmdline
from git_gerrit._error import GerritNotFoundError, GerritConfigError
from git_gerrit._cfg import Config
from git_gerrit._help import command_desc
from git_gerrit._query import current_change

VERBOSE = True

def review(number, repodir=None, branch=None,
           message=None, code_review=None, verified=None,
           abandon=False, restore=False,
           add_reviewers=None):
    """ Submit review to gerrit using the ssh command line interface.

    This method requires authentication. Create a gerrit account and
    import your ssh public key. See the Gerrit documentation.
    """
    if (abandon and restore):
        raise ValueError('Specify only one of "abandon" or "restore".')
    if add_reviewers is None:
        add_reviewers = []

    config = Config(repodir)
    host = config['host']
    project = config['project']
    port = config.get('port', default='29418')

    def arg(name, value):
        if value is True:
            args.append('--'+name)
        elif value:
            args.append('--'+name)
            args.append(list2cmdline([value]))

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
        if VERBOSE:
            print('running: ssh', '-p', port, host, 'gerrit', 'review', *args)
        ssh('-p', port, host, 'gerrit', 'review', *args)

    args = []
    for reviewer in add_reviewers:
        arg('add', reviewer)
    if args:
        arg('project', project)
        arg('branch', branch)
        args.append(number)
        if VERBOSE:
            print('running: ssh', '-p', port, host, 'gerrit', 'set-reviewers', *args)
        ssh('-p', port, host, 'gerrit', 'set-reviewers', *args)

    return 0

def main():
    parser = argparse.ArgumentParser(
        description=command_desc('review'),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""\
Examples:

    $ git gerrit-review --message="Good Job" --code-review="+1" 12345
    $ git gerrit-review --message="Works for me" --verified="+1" 12345
    $ git gerrit-review --add-reviewer="tycobb@yoyodyne.com" --add-reviewer="foo@bar.com" 12345
"""
    )
    parser.add_argument('--branch', default=None, metavar='<branch>', help='Branch name')
    parser.add_argument('--message', default=None, metavar='<message>', help='Review message')
    parser.add_argument('--code-review', default=None, choices=('-2','-1','0','+1','+2'), help='Code review vote')
    parser.add_argument('--verified', default=None, choices=('-1', '0', '+1'), help='Verified vote')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--abandon', default=False, action='store_true', help='Set status to abandoned')
    group.add_argument('--restore', default=False, action='store_true', help='Set status to open')
    parser.add_argument('--add-reviewer', dest='add_reviewers', metavar='<email>', action='append',
                        help='Invite reviewer (this option may be given more than once)')
    parser.add_argument('number', metavar='<number>', type=int, help='gerrit change number')
    args = parser.parse_args()

    try:
        args = vars(args)
        code = review(**args)
    except GerritConfigError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 1
    except GerritNotFoundError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 2
    return code

if __name__ == '__main__':
    sys.exit(main())
