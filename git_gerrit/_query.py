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
from git_gerrit._cfg import Config, GerritConfigError
from git_gerrit._unicode import cook, asciitize
from pprint import pprint
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
    dump = options.pop('dump', False)
    details = options.pop('details', False)
    repodir = options.pop('repodir', None)
    config = Config(repodir)
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
    changes = gerrit.get(query)
    for change in changes:
        if not 'topic' in change:
            change['topic'] = 'no-topic'  # default for --format "{topic}"
        if details:
            change_id = change['change_id']
            query = '/changes/{0}/detail'.format(change_id)
            change['details'] = gerrit.get(query)
    return changes

def main():
    import argparse
    parser = argparse.ArgumentParser(description='query gerrit')
    parser.add_argument('--repodir', help='path to the git project directory', default=None)
    parser.add_argument('-n', '--number', dest='limit', help='limit the number of results', type=int)
    parser.add_argument('--format', help='output format string', default='{number} {subject}')
    parser.add_argument('--dump', help='dump data', action='store_true')
    parser.add_argument('--details', help='get extra details', action='store_true')
    parser.add_argument('term', metavar='<term>', nargs='+', help='search term')
    args = parser.parse_args()
    search = ' '.join(args.term)
    format = cook(args.format)
    format = format.replace('{number', '{_number')
    try:
        for change in query(search, **(vars(args))):
            try:
                if args.dump:
                    pprint(change)
                else:
                    print(format.format(**change))
            except KeyError as ke:
                print('Unknown --format parameter:', ke.message)
                break
            except UnicodeEncodeError:
                # Fall back to plain ascii.
                for c in change:
                    change[c] = asciitize(change[c])
                print(format.format(**change))

    except GerritConfigError as e:
        print("Error:", e.message)

if __name__ == '__main__':
    main()
