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

"""Command line gerrit query"""

from __future__ import print_function
from __future__ import unicode_literals
from pygerrit2.rest import GerritRestAPI
from git_gerrit.cfg import config, GerritConfigError
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

def query(search, **options):
    """Search gerrit for changes.

    args:
        search (str): one or more Gerrit search terms
        options (dict): zero or more Gerrit search options
    returns:
        list of change info dicts
    """
    url="https://{0}".format(config['host'])
    gerrit = GerritRestAPI(url=url)
    if 'project:' not in search:
        search += ' project:{0}'.format(config['project'])
    params = [('q', search)]
    if 'limit' in options:
        if options['limit']:
            params.append(('n', options['limit']))
    for option in options:
        if options[option] is True:
            params.append(('o', option.upper()))
    query = '/changes/?{0}'.format(urlencode(params))
    return gerrit.get(query)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='query gerrit')
    parser.add_argument('-n', '--number', help='limit the number of results', type=int)
    parser.add_argument('--format', help='output format string', default='{_number} {subject}')
    parser.add_argument('term', metavar='<term>', nargs='+', help='search term')
    args = parser.parse_args()
    search = ' '.join(args.term)
    format = args.format
    try:
        format = format.decode('utf-8') # convert python2 string to unicode
    except AttributeError:
        pass
    try:
        for change in query(search, limit=args.number):
            try:
                print(format.format(**change))
            except KeyError as ke:
                print('Unknown --format parameter:', ke.message)
                break
    except GerritConfigError as e:
        print("Error:", e.message)

if __name__ == '__main__':
    main()
