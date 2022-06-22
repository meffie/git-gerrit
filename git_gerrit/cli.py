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

"""git-gerrit command line interface"""

import sys
import argparse
import pprint
import textwrap

import git_gerrit
from git_gerrit.unicode import asciitize, cook
from git_gerrit.error import GitGerritError, GitGerritFormatError

def commands():
    """ Return a list of command name and description tuples. """
    cmds = []
    for key in sorted(globals().keys()):
        if key.startswith('git_gerrit_'):
            name = key.replace('git_gerrit_', 'git gerrit-').replace('_', '-')
            desc = globals()[key].__doc__.strip().strip()
            cmds.append((name, desc))
    return cmds

def print_error(e):
    """ Display error to stderr. """
    sys.stderr.write('ERROR: {0}\n'.format(e.message))

def print_change(change, template='{number} {subject}', dump=False, out=None):
    """
    Format and print a change to the output stream.  Retry by printing just the
    plain ASCII parts when the unicode encoding fails.

    args:
        change (dict): dictionary of data elements to be printed
        template (str): a format template string
        dump (bool): pprint the data instead of formatting it (intended for debugging)
        out (file): output stream, defaults to stdout
    returns:
        None
    """
    template = cook(template)
    if not out:
        out = sys.stdout
    for pass_ in (1, 2):
        try:
            if dump:
                text = pprint.pformat(change)
            else:
                text = template.format(**change)
            out.write(text)
            out.write('\n')
            return
        except KeyError as e:
            raise GitGerritFormatError(e)
        except UnicodeEncodeError as e:
            # Retry with plain ascii.
            if pass_ == 1:
                for key in change:
                    change[key] = asciitize(change[key])
            else:
                raise GitGerritFormatError(e)

def git_gerrit_checkout(argv=None):
    """ Fetch then checkout by gerrit number. """
    config = git_gerrit.Config()
    branch = config.get('checkoutbranch', 'gerrit/{number}/{patchset}')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-checkout',
        description=git_gerrit_checkout.__doc__.strip(),
        epilog="""
Configuration variables:

  gerrit.host            Specifies the gerrit hostname (required).
  gerrit.project         Specifies the gerrit project name (required).
  gerrit.checkoutbranch  Default git-gerrit-checkout --branch value (optional).
""")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--branch', default=branch,
                        help='local branch to create (default: {0})'.format(branch))
    group.add_argument('--no-branch', default=config.getbool('no-branch'), action='store_true',
                        help='do not create a local branch')
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = vars(parser.parse_args(argv))
    number = args.pop('number')
    args['checkout'] = True
    try:
        git_gerrit.fetch(number, **args)
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_cherry_pick(argv=None):
    """ Cherry pick from upstream branch by gerrit number to make a new gerrit."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-cherry-pick',
        description=git_gerrit_cherry_pick.__doc__.strip(),
        epilog="""
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
""")
    parser.add_argument('-b', '--branch', metavar='<branch>',
                        help='upstream branch (default: origin/master)',
                        default='origin/master')
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = vars(parser.parse_args(argv))
    number = args['number']
    branch = args['branch']
    try:
        git_gerrit.cherry_pick(number, branch)
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_fetch(argv=None):
    """ Fetch by gerrit number. """
    config = git_gerrit.Config()
    branch = config.get('fetchbranch', 'gerrit/{number}/{patchset}')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-fetch',
        description=git_gerrit_fetch.__doc__.strip(),
        epilog="""
Configuration variables:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).
  gerrit.fetchbranch    Default git-gerrit-fetch --branch value (optional).
""")
    parser.add_argument('--checkout', default=False, action='store_true',
                        help='checkout after fetch')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--branch', default=branch,
                        help='local branch to create (default: {0})'.format(branch))
    group.add_argument('--no-branch', default=config.getbool('no-branch'), action='store_true',
                        help='do not create a local branch')
    parser.add_argument('number', metavar='<number>', type=int,
                        help='legacy change number')
    args = vars(parser.parse_args(argv))
    number = args.pop('number')
    try:
        git_gerrit.fetch(number, **args)
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_help(argv=None):
    """ List commands. """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-help',
        description=git_gerrit_help.__doc__.strip())
    parser.parse_args(argv)
    print('\nCommands for gerrit code review:\n')
    for name,desc in commands():
        print('    {0:27}  {1}'.format(name, desc))
    print('\nShow command details with:\n')
    print('    git gerrit-<command> -h')

def git_gerrit_install_hooks(argv=None):
    """ Install git hooks to create gerrit change-ids. """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-install-hooks',
        description=git_gerrit_install_hooks.__doc__.strip(),
        epilog="""
Configuration variables:

  gerrit.host           Specifies the gerrit hostname (required).
""")
    vars(parser.parse_args(argv))
    try:
        git_gerrit.install_hooks()
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_log(argv=None):
    """ Show oneline log with gerrit numbers. """
    config = git_gerrit.Config()
    template = config.get('logformat', default='{number} {hash} {subject}')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-log',
        description=git_gerrit_log.__doc__.strip(),
        epilog="""
Available --format template fields: number, hash, subject

Configuration variables:

  gerrit.queryformat    Default git-gerrit-query --format value (optional).
  gerrit.remote         Remote name of the localref --format field (default: origin)
""")
    parser.add_argument('--format', default=template,
                        help='output format (default: "{0}")'.format(template))
    parser.add_argument('-n', '--number', type=int, help='number of commits')
    parser.add_argument('-r', '--reverse', action='store_true', help='reverse order')
    parser.add_argument('-l', '--long-hash', dest='shorthash', action='store_false', default=True,
                        help='show full sha1 hash')
    parser.add_argument('revision', nargs='?', help='revision range')
    args = vars(parser.parse_args(argv))
    template = args.pop('format')
    try:
        for change in git_gerrit.log(**args):
            print_change(change, template)
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_query(argv=None):
    """ Search gerrit. """
    config = git_gerrit.Config()
    template = config.get('queryformat', default='{number} {subject}')
    fields_help = textwrap.fill(', '.join(sorted(git_gerrit.CHANGE_FIELDS)))
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-query',
        description=git_gerrit_query.__doc__.strip(),
        epilog="""
Available --format template fields:

{0}

Configuration variables:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).
  gerrit.queryformat    Default git-gerrit-query --format value (optional).
  gerrit.remote         Remote name of the localref --format field (default: origin)
""".format(fields_help))

    parser.add_argument('-n', '--number', dest='limit',metavar='<number>', type=int,
                        help='limit the number of results')
    parser.add_argument('-f', '--format', metavar='<format>', default=template,
                        help='output format template (default: "'+template+'")')
    parser.add_argument('--dump', help='debug data dump', action='store_true')
    parser.add_argument('--details', help='get extra details for debug --dump', action='store_true')
    parser.add_argument('term', metavar='<term>', nargs='+', help='search term')
    args = vars(parser.parse_args(argv))
    search = ' '.join(args.pop('term'))
    template = args.pop('format')
    dump = args.pop('dump')
    try:
        for change in git_gerrit.query(search, **args):
            print_change(change, template, dump)
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_review(argv=None):
    """ Submit review by gerrit number. """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-review',
        description=git_gerrit_review.__doc__.strip(),
        epilog="""
Examples:

  $ git gerrit-review --message="Good Job" --code-review="+1" 12345
  $ git gerrit-review --message="Works for me" --verified="+1" 12345
  $ git gerrit-review --add-reviewer="tycobb@yoyodyne.com" --add-reviewer="foo@bar.com" 12345

Configuration variables:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).
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
    args = vars(parser.parse_args(argv))
    number = args.pop('number')
    try:
        git_gerrit.review(number, **args)
    except GitGerritError as e:
        print_error(e)
        return 1

def git_gerrit_unpicked(argv=None):
    """ Find gerrit numbers on upstream branch not cherry picked. """
    config = git_gerrit.Config()
    template = config.get('unpickedformat', default='{number} {hash} {subject}')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-unpicked',
        description=git_gerrit_unpicked.__doc__.strip(),
        epilog="""
Configuration variables:

  gerrit.unpickedformat    Default git-gerrit-query --format value (optional).
""")
    parser.add_argument('-u', '--upstream-branch',  help='upstream branch name', default='HEAD')
    parser.add_argument('downstream_branch', help='downstream branch name')
    parser.add_argument('-f', '--format', metavar='<format>', default=template,
                        help='output format template (default: "'+template+'")')
    args = vars(parser.parse_args(argv))
    template = args.pop('format')
    try:
        for commit in git_gerrit.unpicked(**args):
            print_change(commit, template)
    except GitGerritError as e:
        print_error(e)
        return 1
