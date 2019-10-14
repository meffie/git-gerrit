#!/usr/bin/python
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

print(
  open('README.rst.in', 'r')\
  .read()\
  .replace('@GIT_GERRIT_CMD_DESC@', command_descriptions())\
  .replace('@GIT_GERRIT_CMD_HELP@', command_help()))
