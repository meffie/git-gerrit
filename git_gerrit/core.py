# Copyright (c) 2018-2025 Sine Nomine Associates
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

import re
import subprocess

import pygerrit2.rest
import urllib.parse
import sh

from git_gerrit.git import Git
from git_gerrit.db import GitGerritDB
from git_gerrit.spinner import Spinner
from git_gerrit.error import (
    GitGerritError,
    GitGerritNotFoundError,
)

CHANGE_FIELDS = [
    # Gerrit provided fields.
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
    'topic',
    'updated',
    # Local fields added for printing changes.
    'number',
    'patchset',
    'ref',
    'localref',
    'hash',
    'host',
    'url',
]

LOG_FIELDS = (
    'author',
    'change_id',
    'email',
    'hash',
    'number',
    'patchset',
    'picked_from',
    'picked_to',
    'ref',
    'reviewed_on',
    'subject',
)


def cherry_pick(number, branch='origin/master'):
    """
    Cherry pick change from upstream branch and create a new gerrit identifier
    in the commit messsage.

    args:
        number (int): gerrit numeric identifier
        branch (str): upstream branch to pick from
    returns:
        non-zero on error
    """
    git = Git()

    sha1 = None
    for commit in log(revision=branch, shorthash=False):
        if commit['number'] == number:
            sha1 = commit['hash']
            break
    if not sha1:
        raise GitGerritError(
            f"Failed to find gerrit number {number} on branch {branch}."
        )
    git.cherry_pick(sha1)


def current_change(number):
    """
    Look up the current change in gerrit.

    args:
        number (int):  the gerrit change number
    returns:
        a current change dictionary (including the current patchset number)
    """
    changes = list(query(f"change:{number}", limit=1, current_revision=True))
    if not changes or len(changes) != 1:
        raise GitGerritNotFoundError(f"gerrit {format} not found")
    change = changes[0]
    return change


def get_current_change(number):
    """
    Lookup the current change in the local database.
    """
    with GitGerritDB() as db:
        change = db.get_current_patchset_by_number(number)
        if change is None:
            raise GitGerritNotFoundError(f"Change {number} not found.")

        # Convert cherry picked from hash to the gerrit number.
        cpf = change['cherry_picked_from']
        change['cherry_picked_from'] = None
        if cpf:
            from_ = db.get_change_by_commit(cpf)
            if from_:
                change['cherry_picked_from'] = from_['number']
                change['cherry_picked_from_hash'] = cpf
        else:
            change['cherry_picked_from'] = None
            change['cherry_picked_from_hash'] = None

        # Find the cherry picked to numbers.
        picks = set()
        commit_id = change['commit_id']
        for commit in db.get_cherry_picks_by_commit(commit_id):
            to = db.get_change_by_commit(commit['commit_id'])
            if to:
                picks.add(to['number'])
        if picks:
            picked_to = [p for p in sorted(picks)]
            change['cherry_picked_to'] = picked_to
        else:
            change['cherry_picked_to'] = []

    number = change['number']
    patchset = change['current_patchset']
    change['ref'] = f"refs/changes/{number % 100:02}/{number}/{patchset}"
    return change


def fetch(
    number,
    branch=None,
    checkout=False,
):
    """
    Fetch a gerrit by the legacy change number.

    args:
        number (int):     legacy gerrit number
        branch (str):     local branch name to fetch to.
        checkout (bool):  checkout after fetch
    returns:
        None
    raises:
        GitGerritNotFoundError
    """
    git = Git()

    print(f"searching for gerrit {number}")
    change = current_change(number)
    patchset = change['patchset']
    print(f"found patchset number {patchset}")

    if not branch:
        refs = str(change['ref'])
        print(f"fetching {number},{patchset}")
        git.fetch(refs)
        print(f"fetched {number},{patchset} to FETCH_HEAD")
        if checkout:
            git.checkout("FETCH_HEAD")
            print("checked out FETCH_HEAD")
    else:
        branch = branch.format(**change)
        if git.does_branch_exist(branch):
            print(f"branch {branch} already exists")
            return 1
        ref = change['ref']
        refs = f"{ref}:{branch}"
        print(f"fetching {number},{patchset} to branch {branch}")
        git.fetch(refs)
        print(f"fetched {number},{patchset} to branch {branch}")
        if checkout:
            git.checkout(branch)
            print(f"checked out branch {branch}")


def log(number=None, reverse=False, shorthash=True, revision=None):
    """
    Retrieve log entries with gerrit numbers (extracted from the commit
    messages) from the local git repository.

    args:
        number (int):     limit the log to these number of entries [optional]
        reverse (bool):   reverse log order
        shorthash (bool): short sha1
        revision (str):   git revision to log (default is HEAD)
    yields:
        dictionary with keys LOG_FIELDS
    """
    git = Git()

    def blank():
        return {name: "" for name in LOG_FIELDS}

    def populate_gerrit_fields(db, fields, commit_id):
        change = db.get_change_by_commit(commit_id)
        if change:
            number = int(change['number'])
            patchset = int(change['patchset'])
            fields['number'] = number
            fields['patchset'] = patchset
            fields['ref'] = f"refs/changes/{number % 100:02}/{number}/{patchset}"
            if change['change_id']:
                fields['change_id'] = change['change_id']
                if change['cherry_picked_from']:
                    cpf = db.get_change_by_commit(change['cherry_picked_from'])
                    if cpf:
                        fields['picked_from'] = cpf['number']
        picks = set()
        for commit in db.get_cherry_picks_by_commit(commit_id):
            change = db.get_change_by_commit(commit['commit_id'])
            if change:
                picks.add(change['number'])
        if picks:
            picked_to = [str(p) for p in sorted(picks)]
            fields['picked_to'] = ",".join(picked_to)

    # Assemble the --pretty format template.
    tags = {
        "oid": "%H",
        "hash": "%h" if shorthash else "%H",
        "subject": "%s",
        "author": "%an",
        "email": "%ae",
        "body": "%n%b",
    }
    terms = []
    for k, v in tags.items():
        terms.append(f"{k}:{v}")
    terms.append("%%%%")  # End of body marker
    options = {
        'pretty': "%n".join(terms),
        'reverse': reverse,
    }
    if number:
        options['max-count'] = number

    with GitGerritDB() as db:
        fields = blank()
        for line in git.log(revision, **options):
            m = re.match(r'^oid:(.*)', line)
            if m:
                populate_gerrit_fields(db, fields, m.group(1))
                continue
            m = re.match(r'^hash:(.*)', line)
            if m:
                fields['hash'] = m.group(1)
                continue
            m = re.match(r'^subject:(.*)', line)
            if m:
                fields['subject'] = m.group(1)
                continue
            m = re.match(r'^author:(.*)', line)
            if m:
                fields['author'] = m.group(1)
                continue
            m = re.match(r'^email:(.*)', line)
            if m:
                fields['email'] = m.group(1)
                continue
            m = re.match(r'^body:', line)  # Start of body.
            if m:
                continue
            m = re.match(r'^Reviewed-on: .*/([0-9]+)$', line)
            if m:
                # Save the last Reviewed-on one seen in the body,
                # there can be more than one in backported commits.
                fields['reviewed_on'] = int(m.group(1))
                continue
            m = re.match(r'^Change-Id: (I[0-9a-fA-F]+)$', line)
            if m:
                # Save the first one seen. Normally each commit has zero or one
                # change-id trailers.
                if fields['change_id']:
                    fields['change_id'] = m.group(1)
                continue
            m = re.match(r'^%%$', line)  # End of body.
            if m:
                # Fallback to the reviewed-on trailer if the change
                # was not found in the database.
                if not fields['number']:
                    fields['number'] = fields['reviewed_on']
                yield fields
                fields = blank()


def _flatten_change(change, host, remote):
    """Update the change dictionary to make it easier to print."""

    # Auxiliary keys for printing changes.
    number = change['_number']
    change['number'] = number
    change['hash'] = change['current_revision']  # alias
    change['patchset'] = change['revisions'][change['current_revision']]['_number']
    change['ref'] = change['revisions'][change['current_revision']]['ref']
    change['localref'] = change['ref'].replace('refs/', remote + '/')
    change['host'] = host
    change['url'] = f"https://{host}/{number}"

    # The owner is a dict with the account id.
    if isinstance(change['owner'], dict):
        if '_account_id' in change['owner']:
            owner = change['owner']['_account_id']
        else:
            owner = 'Unknown'
        change['owner'] = owner

    # The hashtags is a list of strings.
    change['hashtags'] = ','.join(change['hashtags'])

    # Add empty values for optional fields to avoid key errors when printing.
    for key in CHANGE_FIELDS:
        if key not in change:
            change[key] = ''

    return change


def query(search, limit=None, details=False, **options):
    """Search gerrit for changes.

    args:
        search (str): one or more Gerrit search terms
        options (dict): zero or more Gerrit search options
    returns:
        list of change info dicts
    """
    git = Git()
    remote = git.config('remote')
    host = git.config('host')
    gerrit = pygerrit2.rest.GerritRestAPI(f"https://{host}")

    if 'project:' not in search:
        project = git.config('project')
        search += f" project:{project}"

    if 'current_revision' not in options:
        options['current_revision'] = True

    # Gerrit limits the number of results per request, so loop to
    # retrieve results in batches.
    start = 0
    more_changes = True
    while more_changes:
        # Setup query parameters.
        params = [('q', search)]
        if limit:
            params.append(('n', (limit - start)))
        if start:
            params.append(('S', start))
        for option in options:
            if options[option] is True:
                params.append(('o', option.upper()))
        params = urllib.parse.urlencode(params)

        # Retrieve next batch.
        for change in gerrit.get(f"/changes/?{params}"):
            start += 1
            more_changes = change.get('_more_changes', False)
            change = _flatten_change(change, host, remote)
            if details:
                change_id = change['change_id']
                change['_detail'] = gerrit.get(f"/changes/{change_id}/detail")
            yield change
            if limit and start >= limit:
                more_changes = False


def update(
    number,
    branch=None,
    message=None,
    code_review=None,
    verified=None,
    abandon=False,
    restore=False,
    add_reviewers=None,
    verbose=False,
):
    """Submit review to gerrit using the ssh command line interface.

    Note: This method requires authentication. Create a gerrit account and
    import your ssh public key. See the Gerrit documentation.

    args:
        number (int): gerrit id (requried)
        branch (str): branch change is located (optional)
        message (str): review message to add (optional)
        code_review (str): code review vote to add (optional)
        verified (str): verication vote to add (optional)
        abandon (bool): set change status to abandoned
        restore (bool): set change status back to open if abandoned
    returns:
        None
    """
    ssh = sh.Command('ssh')
    git = Git()

    if abandon and restore:
        raise ValueError('Specify only one of "abandon" or "restore".')

    if add_reviewers is None:
        add_reviewers = []

    host = git.config('host')
    project = git.config('project')
    port = git.config('port')

    def arg(name, value):
        if value is True:
            args.append('--' + name)
        elif value:
            args.append('--' + name)
            args.append(subprocess.list2cmdline([value]))

    args = []
    arg('message', message)
    arg('code-review', code_review)
    arg('verified', verified)
    arg('abandon', abandon)
    arg('restore', restore)
    if args:
        arg('project', project)
        arg('branch', branch)
        change = current_change(number)
        patchset = change['patchset']
        changeid = f"{number},{patchset}"
        args.append(changeid)
        if verbose:
            print('running: ssh', '-p', port, host, 'gerrit', 'review', *args)
        ssh('-p', str(port), host, 'gerrit', 'review', *args)

    args = []
    for reviewer in add_reviewers:
        arg('add', reviewer)
    if args:
        arg('project', project)
        arg('branch', branch)
        args.append(number)
        if verbose:
            print('running: ssh', '-p', port, host, 'gerrit', 'set-reviewers', *args)
        ssh('-p', str(port), host, 'gerrit', 'set-reviewers', *args)

    return 0


def sync(limit=None):
    git = Git()

    with Spinner(f"Fetching changes from {git.remote()}") as spinner:
        git.fetch("refs/changes/*:refs/changes/*", spinner)

    with Spinner("Updating local database") as spinner:
        with GitGerritDB() as db:
            pattern = r"refs/changes/\d\d/\d+/\d+"
            for commit_id, refname in git.show_refs(pattern):
                parts = refname.split("/")
                number = int(parts[3])
                patchset = int(parts[4])
                db.add_change(number, patchset, commit_id)
                spinner.spin()

    # It is not practical to read every commit message, and normally, we only
    # care about the current patchsets, so scan just the current patchsets
    # (that is the max patchset number of each change number). Also, limit the
    # number of changes to be scanned, since we normally care about jus the
    # most recent numbers. This amoritizes the scanning, so the first
    # git-gerrit-sync will scan a reasonable number of changes, and later syncs
    # will process older changes.
    with Spinner("Scanning commit messages") as spinner:
        with GitGerritDB() as db:
            for c in db.get_current_patchsets(limit=limit):
                if c['flags'] != 1:
                    commit_id = c['commit_id']
                    change_id = git.change_id(commit_id)
                    picked_from = git.cherry_picked_from(commit_id)
                    db.update_commit(commit_id, change_id, picked_from, 1)
                    spinner.spin()

    print("Done.")
    return 0
