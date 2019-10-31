# Copyright (c) 2019 Sine Nomine Associates
#
# Update the README.md file with git-gerrit command help text.
#
# usage: python genreadme.py
#

import re
from sh import python
import git_gerrit.cli

def command_descriptions():
    lines = []
    for name, desc in git_gerrit.cli.commands():
        lines.append('    {0:27}  {1}'.format(name, desc))
    return '\n'.join(lines)

def command_usage(fn, indent=4):
    lines = []
    spaces = ' ' * indent
    code = 'from git_gerrit.cli import {0}; {0}(["--help"])'.format(fn)
    for line in python('-c', code, _iter=True):
        lines.append(spaces + line)
    return ''.join(lines)

def command_help():
    help_ = []
    for name, _ in git_gerrit.cli.commands():
        fn = name.replace('git gerrit-', 'git_gerrit_').replace('-', '_')
        cmd = name.replace(' ', '-')
        help_.append('Command {0}::\n\n'.format(cmd))
        help_.append(command_usage(fn))
        help_.append('\n')
    return ''.join(help_)

def update(string, tag, replacement):
    return re.sub(
        r'\.\. begin git-gerrit {0}.*\.\. end git-gerrit {0}'.format(tag),
        '.. begin git-gerrit {0}\n\n{1}\n\n.. end git-gerrit {0}'.format(tag, replacement),
        string, count=1, flags=re.DOTALL)

def main():
    with open('README.rst', 'r') as f:
        readme = f.read()
    readme = update(readme, 'desc', '::\n\n' + command_descriptions())
    readme = update(readme, 'help', command_help())
    with open('README.rst', 'w') as f:
        f.write(readme)

if __name__ == '__main__':
    main()
