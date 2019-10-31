# Copyright (c) 2019 Sine Nomine Associates
#
# Generate git-gerrit wrapper scripts.
#
# usage: python genscripts.py
#

import os
import git_gerrit.cli
from git_gerrit import _chmod as chmod

template = """\
#!/usr/bin/env python
import sys
from git_gerrit.cli import {0}
sys.exit({0}())
"""

for name,_ in git_gerrit.cli.commands():
    fn = name.replace('git gerrit-', 'git_gerrit_').replace('-', '_')
    filename = os.path.join('bin', name.replace(' ', '-').replace('_', '-'))
    with open(filename, 'w') as f:
        f.write(template.format(fn))
    chmod(filename, 'rwxr-xr-x')
