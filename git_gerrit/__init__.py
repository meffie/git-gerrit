# Copyright (c) 2018-2024 Sine Nomine Associates
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

"""
Git helpers for the Gerrit code review system, with an emphasis on the Gerrit
old-style numeric identifiers.
"""

from git_gerrit.__version__ import VERSION
from git_gerrit.git import Git
from git_gerrit.error import (
    GitGerritError,
    GitGerritConfigError,
    GitGerritFormatError,
    GitGerritNotFoundError,
)
from git_gerrit.core import (
    CHANGE_FIELDS,
    LOG_FIELDS,
    cherry_pick,
    fetch,
    get_current_change,
    log,
    query,
    sync,
    update,
)

_hush_linter = [
    VERSION,
    CHANGE_FIELDS,
    LOG_FIELDS,
    Git,
    GitGerritError,
    GitGerritConfigError,
    GitGerritFormatError,
    GitGerritNotFoundError,
    cherry_pick,
    fetch,
    get_current_change,
    log,
    query,
    sync,
    update,
]
