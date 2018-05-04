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

"""unicode related functions"""

from __future__ import print_function
from __future__ import unicode_literals
import sys

def cook(raw):
    """Convert raw string to unicode string.

    Returns a unicode string, falling back to plain
    ascii characters on decoding errors (others are dropped).
    """
    if sys.version_info[0] < 3:
        # python 2
        if isinstance(raw, str):
            try:
                cooked = raw.decode('utf-8')
            except UnicodeDecodeError:
                cooked = raw.decode('ascii', 'ignore')
        else:
            cooked = raw
    else:
        # python 3
        if isinstance(raw, bytes):
            try:
                cooked = raw.decode('utf-8')
            except UnicodeDecodeError:
                cooked = raw.decode('ascii', 'ignore')
        else:
            cooked = raw
    return cooked

def asciitize(text):
    """Remove non-ascii chars from strings.

    Returns a unicode string consisting of ascii characters, or
    if not given a string, passes the argument back unharmed.
    """
    if sys.version_info[0] < 3:
        # python 2
        if isinstance(text, unicode):
            text = text.encode('ascii', 'ignore')
        if isinstance(text, str):
            text = text.decode('ascii', 'ignore')
    else:
        # python 3
        if isinstance(text, str):
            text = text.encode('ascii', 'ignore')
        if isinstance(text, bytes):
            text = text.decode('ascii', 'ignore')
    return text
