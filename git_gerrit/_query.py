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
import sys
import argparse
from pprint import pprint
from pygerrit2.rest import GerritRestAPI
from git_gerrit._error import GerritConfigError, GerritNotFoundError
from git_gerrit._help import command_desc
from git_gerrit._cfg import Config
from git_gerrit._unicode import cook, asciitize
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
    options.pop('dump', False)
    details = options.pop('details', False)
    repodir = options.pop('repodir', None)
    config = Config(repodir)
    url = "https://{0}".format(config['host'])
    gerrit = GerritRestAPI(url=url)
    if 'project:' not in search:
        search += ' project:{0}'.format(config['project'])
    params = [('q', search)]
    if 'limit' in options:
        if options['limit']:
            params.append(('n', options['limit']))
    if not 'current_revision' in options:
        options['current_revision'] = True
    for option in options:
        if options[option] is True:
            params.append(('o', option.upper()))
    query = '/changes/?{0}'.format(urlencode(params))
    changes = gerrit.get(query)
    for change in changes:
        change['number'] = change['_number']
        change['hash'] = change['current_revision'] # alias
        change['patchset'] = change['revisions'][change['current_revision']]['_number']
        change['ref'] = change['revisions'][change['current_revision']]['ref']
        change['host'] = config['host']
        change['url'] = "https://{0}/{1}".format(config['host'], change['_number'])
        if not 'topic' in change:
            change['topic'] = 'no-topic'  # default for --format "{topic}"
        if details:
            change_id = change['change_id']
            query = '/changes/{0}/detail'.format(change_id)
            change['details'] = gerrit.get(query)
    return changes

def current_change(number, repodir=None):
    """ Look up the current change in gerrit.

    args:
        number (int):  the gerrit change number
        repodir (str): optional path to the git repo directory (for git configuration)
    returns:
        a current change dictionary (including the current patchset number)
    """
    changes = query('change:{0}'.format(number), limit=1, current_revision=True, repodir=repodir)
    if not changes or len(changes) != 1:
        raise GerritNotFoundError('gerrit {0} not found'.format(number))
    change = changes[0]
    return change

def main():
    format_default = '{number} {subject}'
    format_names = [
        # direct fields
        'branch',
        'change_id',
        'created',
        'current_revision',
        'deletions',
        'hashtags',
        'id',
        'insertions',
        'owner',
        'project',
        'status',
        'subject',
        'submittable',
        'submitted',
        'topic',  # synthentic default
        'updated',
        # synthentic fields
        'number',
        'patchset',
        'ref',
        'hash',
        'host',
        'url',
    ]
    parser = argparse.ArgumentParser(
        description=command_desc('query'),
        epilog="Available --format template names: "+', '.join(sorted(format_names)))
    parser.add_argument('--repodir', help='git project directory (default: current directory)')
    parser.add_argument('-n', '--number', dest='limit',metavar='<number>', type=int,
                        help='limit the number of results')
    parser.add_argument('-f', '--format', metavar='<format>', default=None,
                        help='output format template (default: "'+format_default+'")')
    parser.add_argument('--dump', help='debug data dump', action='store_true')
    parser.add_argument('--details', help='get extra details for debug --dump', action='store_true')
    parser.add_argument('term', metavar='<term>', nargs='+', help='search term')
    args = parser.parse_args()
    search = ' '.join(args.term)

    config = Config(repodir=args.repodir)
    format_ = args.format
    if not format_:
        format_ = config.get('queryformat', default=format_default)
    format_ = cook(format_)

    code = 0
    try:
        for change in query(search, **(vars(args))):
            try:
                if args.dump:
                    pprint(change)
                else:
                    print(format_.format(**change))
            except KeyError as ke:
                print('Unknown --format parameter:', ke.message)
                code = 1
                break
            except UnicodeEncodeError:
                # Fall back to plain ascii.
                for c in change:
                    change[c] = asciitize(change[c])
                print(format_.format(**change))

    except GerritConfigError as e:
        sys.stderr.write('Error: {0}\n'.format(e.message))
        code = 2
    return code

if __name__ == '__main__':
    sys.exit(main())
