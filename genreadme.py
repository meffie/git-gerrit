#!/usr/bin/python
import re
from git_gerrit._help import command_descriptions
from sh import bash

def command_help():
    return bash(_in="""\
        for cmd in bin/git-gerrit-*; do
            echo "Command $(basename $cmd)::"
            echo ""
            PYTHONPATH=. $cmd -h | sed 's/^/    /'
            echo ""
        done""").stdout

def subst(text, tag, repl):
    return re.sub(
        r'\.\. begin git-gerrit {0}.*\.\. end git-gerrit {0}'.format(tag),
        '.. begin git-gerrit {0}\n\n{1}\n\n.. end git-gerrit {0}'.format(tag, repl),
        text, count=1, flags=re.DOTALL)

with open('README.rst', 'r') as f:
    readme = f.read()

readme = subst(readme, 'desc', '::\n\n' + command_descriptions())
readme = subst(readme, 'help', command_help())

with open('README.rst', 'w') as f:
    f.write(readme)
