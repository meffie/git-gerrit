# Copyright (c) 2018-2025 Sine Nomine Associates
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

import argparse
import pprint
import sys
import textwrap
import json

import git_gerrit
from git_gerrit.git import Git
from git_gerrit.spinner import Spinner
from git_gerrit.error import GitGerritError, GitGerritFormatError


def format_change(template, change):
    try:
        return template.format(**change)
    except KeyError as e:
        raise GitGerritFormatError(e)
    except ValueError as e:
        raise GitGerritFormatError(e)


def main_git_gerrit_version(argv=None):
    """Print version and exit."""
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-version',
        description=main_git_gerrit_version.__doc__.strip(),
    )
    parser.parse_args(argv)
    print(git_gerrit.VERSION)
    return 0


def main_git_gerrit_checkout(argv=None):
    """Fetch then checkout by gerrit number."""
    if argv is None:
        argv = sys.argv[1:]

    git = Git()
    branch = git.config('checkoutbranch')
    if not branch:
        branch_desc = "[do not create a branch]"
    else:
        branch_desc = branch

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-checkout',
        description=main_git_gerrit_checkout.__doc__.strip(),
        epilog="""
git config options:

  gerrit.host            Specifies the gerrit hostname (required).
  gerrit.project         Specifies the gerrit project name (required).
  gerrit.checkoutbranch  Default git-gerrit-checkout --branch value (optional).
""",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--branch',
        default=branch,
        help=f"local branch to create (default: {branch_desc})",
    )
    group.add_argument(
        '--no-branch',
        default=git.config('no-branch'),
        action='store_true',
        help='do not create a local branch',
    )
    parser.add_argument(
        'number', metavar='<number>', type=int, help='legacy change number'
    )
    args = vars(parser.parse_args(argv))
    number = args.pop('number')
    args['checkout'] = True
    no_branch = args.pop('no_branch')
    if no_branch:
        args['branch'] = None

    try:
        git_gerrit.fetch(number, **args)
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_cherry_pick(argv=None):
    """Cherry pick from upstream branch by gerrit number to make a new gerrit."""
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-cherry-pick',
        description=main_git_gerrit_cherry_pick.__doc__.strip(),
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
""",
    )
    parser.add_argument(
        '-b',
        '--branch',
        metavar='<branch>',
        help='upstream branch (default: origin/master)',
        default='origin/master',
    )
    parser.add_argument(
        'number', metavar='<number>', type=int, help='legacy change number'
    )
    args = vars(parser.parse_args(argv))
    number = args['number']
    branch = args['branch']

    try:
        git_gerrit.cherry_pick(number, branch)
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_fetch(argv=None):
    """Fetch by gerrit number."""
    if argv is None:
        argv = sys.argv[1:]

    git = Git()
    branch = git.config('fetchbranch')
    if not branch:
        branch_desc = "[do not create a branch]"
    else:
        branch_desc = branch

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-fetch',
        description=main_git_gerrit_fetch.__doc__.strip(),
        epilog="""
git config options:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).
  gerrit.fetchbranch    Default git-gerrit-fetch --branch value (optional).
""",
    )
    parser.add_argument(
        '--checkout', default=False, action='store_true', help='checkout after fetch'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--branch',
        default=branch,
        help=f"local branch to create (default: {branch_desc})",
    )
    group.add_argument(
        '--no-branch',
        default=git.config('no-branch'),
        action='store_true',
        help='do not create a local branch',
    )
    parser.add_argument(
        'number', metavar='<number>', type=int, help='legacy change number'
    )
    args = vars(parser.parse_args(argv))
    number = args.pop('number')
    no_branch = args.pop('no_branch')
    if no_branch:
        args['branch'] = None

    try:
        git_gerrit.fetch(number, **args)
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_help(argv=None):
    """List commands."""
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-help',
        description=main_git_gerrit_help.__doc__.strip(),
    )

    parser.parse_args(argv)

    # Walk the symbol list of this module to print a summary of commands.
    print("")
    print("Available commands:")
    print("")
    for symbol in sorted(globals().keys()):
        if symbol.startswith("main_git_gerrit_"):
            function = globals()[symbol]
            name = symbol.replace("main_git_gerrit_", "git gerrit-").replace("_", "-")
            desc = function.__doc__.strip()
            print(f"    {name:27}  {desc}")
    print("")
    print("Show command help with:")
    print("")
    print("    git gerrit-<command> -h")
    return 0


def main_git_gerrit_install_hooks(argv=None):
    """Install git hooks to create gerrit change-ids."""
    if argv is None:
        argv = sys.argv[1:]
    git = Git()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-install-hooks',
        description=main_git_gerrit_install_hooks.__doc__.strip(),
        epilog="""
git config options:

  gerrit.host           Specifies the gerrit hostname (required).
""",
    )
    parser.parse_args(argv)

    try:
        with Spinner("Downloading 'commit-msg' git hook.") as spinner:
            git.download_hook("commit-msg", spinner)
        with Spinner("Writing 'prepare-commit-msg' git hook.") as spinner:
            git.write_hook("prepare-commit-msg", spinner)
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_log(argv=None):
    """Show oneline log with gerrit numbers."""
    if argv is None:
        argv = sys.argv[1:]
    git = Git()
    template = git.config('logformat')
    fields_help = textwrap.fill(', '.join(sorted(git_gerrit.LOG_FIELDS)))
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-log',
        description=main_git_gerrit_log.__doc__.strip(),
        epilog=f"""
Available --format template fields:

{fields_help}

Python string format specifiers are supported in the --format template. For
example, to print the numbers in a fixed with, filled with zeros:

    git gerrit-log --format '{{number:08}}'

git config options:

  gerrit.queryformat    Default git-gerrit-query --format value (optional).
  gerrit.remote         Remote name of the localref --format field (default: origin)
""",
    )
    parser.add_argument(
        '--format',
        default=template,
        help=f"output format (default: '{template}')",
    )
    parser.add_argument('-n', '--number', type=int, help='number of commits')
    parser.add_argument('-r', '--reverse', action='store_true', help='reverse order')
    parser.add_argument(
        '-l',
        '--long-hash',
        dest='shorthash',
        action='store_false',
        default=True,
        help='show full SHA1 hash',
    )
    parser.add_argument('revision', nargs='?', help='revision range')
    args = vars(parser.parse_args(argv))
    template = args.pop('format')

    try:
        for commit in git_gerrit.log(**args):
            print(format_change(template, commit))
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_query(argv=None):
    """Search gerrit."""
    if argv is None:
        argv = sys.argv[1:]
    git = Git()
    template = git.config('queryformat')
    fields_help = textwrap.fill(', '.join(sorted(git_gerrit.CHANGE_FIELDS)))
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-query',
        description=main_git_gerrit_query.__doc__.strip(),
        epilog=f"""
Available --format template fields:

{fields_help}

git config options:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).
  gerrit.queryformat    Default git-gerrit-query --format value (optional).
  gerrit.remote         Remote name of the localref --format field (default: origin)
""",
    )

    parser.add_argument(
        '-n',
        '--limit',
        dest='limit',
        metavar='<number>',
        type=int,
        help='limit the number of results',
    )
    parser.add_argument(
        '-f',
        '--format',
        metavar='<format>',
        default=template,
        help='output format template (default: "' + template + '")',
    )
    parser.add_argument('--dump', help='debug data dump', action='store_true')
    parser.add_argument(
        '--details', help='get extra details for debug --dump', action='store_true'
    )
    parser.add_argument('term', metavar='<term>', nargs='+', help='search term')
    args = vars(parser.parse_args(argv))
    search = ' '.join(args.pop('term'))
    template = args.pop('format')
    dump = args.pop('dump')

    try:
        for change in git_gerrit.query(search, **args):
            if dump:
                pprint.pprint(change)
            else:
                print(format_change(template, change))
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_number(argv=None):
    """Show info for a gerrit change number."""
    if argv is None:
        argv = sys.argv[1:]
    git = Git()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-number',
        description=main_git_gerrit_number.__doc__.strip(),
    )
    parser.add_argument(
        'number', metavar='<number>', type=int, help="Gerrit number to show"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--hash', action='store_true', help="Show commit id")
    group.add_argument('--ref', action='store_true', help="Show git ref")
    group.add_argument('--change-id', action='store_true', help="Show gerrit id")
    group.add_argument(
        '--cherry-picked-from',
        action='store_true',
        help="Show cherry picked from gerrit number",
    )
    group.add_argument(
        '--cherry-picked-to',
        action='store_true',
        help="Show cherry picked to gerrit numbers",
    )
    group.add_argument(
        '--checkout', action='store_true', help="Checkout the gerrit number"
    )
    group.add_argument(
        '--show',
        action='store_true',
        help="Show the commit",
    )
    args = parser.parse_args(argv)

    try:
        change = git_gerrit.get_current_change(args.number)
        if args.hash:
            print(change['commit_id'] or "")
        elif args.ref:
            print(change['ref'] or "")
        elif args.change_id:
            print(change['change_id'] or "")
        elif args.cherry_picked_from:
            print(change['cherry_picked_from'] or "")
        elif args.cherry_picked_to:
            for p in change['cherry_picked_to']:
                print(p or "")
        elif args.checkout:
            print(git.git.checkout(change['commit_id'], detach=True))
        elif args.show:
            print(git.git.show(change['commit_id']))
        else:
            print(json.dumps(change, indent=4))
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_sync(argv=None):
    """Fetch all changes and update the local database."""
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-sync',
        description=main_git_gerrit_sync.__doc__.strip(),
        epilog="""
git config options:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).
""",
    )
    parser.add_argument(
        '--limit',
        dest='limit',
        metavar='<number>',
        default=1000,
        type=int,
        help='limit the number of commits to scan',
    )
    args = vars(parser.parse_args(argv))

    try:
        git_gerrit.sync(**args)
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0


def main_git_gerrit_update(argv=None):
    """Update gerrits matching search terms."""
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='git-gerrit-update',
        description=main_git_gerrit_update.__doc__.strip(),
        epilog="""
authentication required:

  gerrit account and associated ssh key

git config options:

  gerrit.host           Specifies the gerrit hostname (required).
  gerrit.project        Specifies the gerrit project name (required).

examples:

  $ git gerrit-update --message="Good Job" --code-review="+1" change:12345
  $ git gerrit-update --add-reviewer="ty@example.com" is:open topic:foobar
  $ git gerrit-update --abandon --message="nevermind" branch:master topic:baz
""",
    )
    parser.add_argument(
        '-n', '--dryrun', action='store_true', help='Show gerrits to be changed.'
    )
    parser.add_argument(
        '--message', default=None, metavar='<message>', help='Review message'
    )
    parser.add_argument(
        '--code-review',
        default=None,
        choices=('-2', '-1', '0', '+1', '+2'),
        help='Code review vote',
    )
    parser.add_argument(
        '--verified', default=None, choices=('-1', '0', '+1'), help='Verified vote'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--abandon', default=False, action='store_true', help='Set status to abandoned'
    )
    group.add_argument(
        '--restore', default=False, action='store_true', help='Set status to open'
    )
    parser.add_argument(
        '--add-reviewer',
        dest='add_reviewers',
        metavar='<email>',
        action='append',
        help='Invite reviewer (this option may be given more than once)',
    )
    parser.add_argument('term', metavar='<term>', nargs='+', help='search term')
    args = vars(parser.parse_args(argv))
    dryrun = args.pop('dryrun')
    search = ' '.join(args.pop('term'))

    try:
        for change in git_gerrit.query(search):
            number = change['number']
            subject = change['subject']
            if dryrun:
                print(f"Skipping (dry-run): {number} {subject}")
            else:
                print(f"Updating: {number} {subject}")
                git_gerrit.update(number, **args)
    except GitGerritError as e:
        print(str(e), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, BrokenPipeError):
        return 1

    return 0
