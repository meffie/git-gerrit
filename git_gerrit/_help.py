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

def main():
    help = """\

Gerrit Code Review helpers

    git gerrit-help           command help
    git gerrit-install-hooks  install git hooks for gerrit
    git gerrit-query          search for gerrit numbers
    git gerrit-fetch          fetch gerrits by number
    git gerrit-checkout       fetch then checkout gerrit by number
    git gerrit-log            show oneline log with gerrit numbers
    git gerrit-unpicked       gerrit numbers not cherry-picked

Show command details with:

    git gerrit-<command> -h
"""
    print(help)

if __name__ == '__main__':
    main()
