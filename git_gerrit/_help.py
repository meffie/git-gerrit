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

from __future__ import print_function
import sys

_command_descriptions = (
    ('help',           'List commands.'),
    ('query',          'Search gerrit.'),
    ('fetch',          'Fetch by gerrit number.'),
    ('checkout',       'Fetch then checkout by gerrit number.'),
    ('log',            'Show oneline log with gerrit numbers.'),
    ('unpicked',       'Find gerrit numbers on upstream branch not cherry picked.'),
    ('cherry-pick',    'Cherry pick from upstream branch by gerrit number.'),
    ('install-hooks',  'Install git hooks to create gerrit change-ids.'),
)

def command_desc(name):
    return dict(_command_descriptions)[name]

def command_descriptions():
    descs = []
    for name,desc in _command_descriptions:
        descs.append('    git gerrit-{0:16}  {1}'.format(name, desc))
    return '\n'.join(descs)

def main():
    print('\nCommands for gerrit code review:\n')
    print(command_descriptions())
    print('\nShow command details with:\n')
    print('    git gerrit-<command> -h')
    return 0

if __name__ == '__main__':
    sys.exit(main())
