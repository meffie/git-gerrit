# Copyright (c) 2018 Sine Nomine Associates
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
from __future__ import unicode_literals
from sh.contrib import git
from sh import ErrorReturnCode_1
from git_gerrit.error import GitGerritConfigError

class Config:
    def __init__(self, repodir=None):
        self.repodir = repodir

    def _get(self, name):
        """Read a config value with 'git config --get'."""
        try:
            return git.config('--get', 'gerrit.%s' % name, _cwd=self.repodir).rstrip()
        except ErrorReturnCode_1:
            return None

    def __getitem__(self, variable):
        """Get a value with [] or raise an error if missing."""
        value = self._get(variable)
        if not value:
            raise GitGerritConfigError(variable)
        return value

    def get(self, variable, default=None):
        """Get a value or return a default if misssing."""
        value = self._get(variable)
        if not value:
            value = default
        return value
