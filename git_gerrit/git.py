# Copyright (c) 2025 Sine Nomine Associates
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


import os
import re
import sh

import urllib.request

from git_gerrit.error import (
    GitGerritError,
    GitGerritNotFoundError,
    GitGerritConfigError,
)


HOOKS = {
    "prepare-commit-msg": """\
#!/bin/bash
#
# Change the gerrit change-id in a commit message. To be used when cherry
# picking already merged commits to a different branch.
#
# usage: GERRIT_CHERRY_PICK=yes git cherry-pick -x <commit>
#
test "$GERRIT_CHERRY_PICK" = "yes" || exit 0
grep '^(cherry picked from commit' "$1" >/dev/null || exit 0
grep '^Change-Id:' "$1" >/dev/null || exit 0
echo "prepare-commit-msg: creating new gerrit Change-Id"
sed -i '/^Change-Id:/d' "$1"
.git/hooks/commit-msg "$1"
"""
}


class Git:
    """Git utilities"""

    config_schema = {
        "host": {
            "type": "string",
        },
        "project": {
            "type": "string",
        },
        "logformat": {
            "type": "string",
            "default": "{number} {hash} {subject}",
        },
        "no-branch": {
            "type": "boolean",
            "default": "false",
        },
        "port": {
            "type": "number",
            "default": "29418",
        },
        "queryformat": {
            "type": "string",
            "default": "{number} {subject}",
        },
        "remote": {
            "type": "string",
            "default": "origin",
        },
        "unpickedformat": {
            "type": "string",
            "default": "{number} {hash} {subject}",
        },
        "fetchbranch": {
            "type": "string",
            "default": "",
        },
        "checkoutbranch": {
            "type": "string",
            "default": "",
        },
    }

    def __init__(self):
        """Initialize the Git utility object."""
        self.git = sh.Command('git').bake(_tty_out=False)

    def config(self, name):
        """Return a git-gerrit config value."""

        if name not in self.config_schema:
            raise ValueError(f"Unknown config item {name}")

        try:
            line = self.git.config("--get", f"gerrit.{name}").rstrip()
            value = line.rstrip()
        except sh.ErrorReturnCode_1:
            if "default" in self.config_schema[name]:
                value = self.config_schema[name]["default"]
            else:
                raise GitGerritConfigError(name)

        type_ = self.config_schema[name]["type"]
        if type_ == "string":
            pass
        elif type_ == "number":
            try:
                value = int(value)
            except ValueError:
                raise GitGerritError(
                    f"git config item gerrit.{name} should be a number."
                )
        elif type_ == "boolean":
            if value.lower() in ("true", "1", "yes"):
                value = True
            elif value.lower() in ("false", "0", "no"):
                value = False
            else:
                raise GitGerritError(
                    f"git config item gerrit.{name} should be a boolean."
                )
        else:
            raise AssertionError(f"Bad config_schema type {type_} for name {name}")

        return value

    def git_dir(self):
        """Return the absolute path to the .git directory.

        Return the $GIT_DIR if defined, otherwise return the path to the .git
        directory.
        """
        try:
            line = self.git("rev-parse", "--git-dir")
        except sh.ErrorReturnCode_128 as e:
            if b"not a git repo" in e.stderr:
                raise GitGerritNotFoundError(e.stderr)
            else:
                raise GitGerritError(e)
        return os.path.abspath(line.rstrip())

    def remote(self):
        """Return the gerrit remote URL."""
        host = self.config("host")
        project = self.config("project")
        remote = f"https://{host}/{project}"
        return remote

    def fetch(self, refspec, spinner=None):
        """Run git fetch."""
        errors = ""

        def handle_output(text):
            nonlocal errors
            if "fatal:" in text:
                errors += text
            if spinner:
                spinner.spin()

        try:
            self.git.fetch(
                self.remote(),
                refspec,
                progress=True,
                verbose=True,
                _out=handle_output,
                _err=handle_output,
                _tee=True,
            )
        except sh.ErrorReturnCode as e:
            raise GitGerritError(f"Command failed: git fetch: {e.exit_code}: {errors}")

    def checkout(self, refname):
        """Run git checkout to checkout a change."""
        self.git.checkout(refname)

    def log(self, refname=None, **options):
        """Run git log to show changes."""

        def decode(line):
            # Convert bytes to a str.  `sh` returns bytes when it is unable to
            # decode using the codec from the current locale.
            try:
                return line.decode('utf-8')
            except UnicodeDecodeError:
                pass
            try:
                return line.decode('cp1252')
            except UnicodeDecodeError:
                pass
            # Last resort. latin-1 maps all byte values so will
            # not fail, but may produce garbage text.
            return line.decode('latin-1', errors='ignore')

        if not refname:
            refname = "HEAD"

        for line in self.git.log(refname, _iter=True, **options):
            if isinstance(line, bytes):
                line = decode(line)
            yield line.rstrip()

    def cherry_pick(self, refname):
        """Run git cherry-pick to cherry pick a change.

        We want to generate a new gerrit Change-Id for this commit.  Set the
        following env var to instruct the prepare-commit-mg hook (created by git
        errit-install-hooks) to remove the old change-id in the commit message
        and run the gerrit commit-msg hook to generate a brand new Change-Id.
        """
        env = os.environ.copy()
        env['GERRIT_CHERRY_PICK'] = 'yes'
        try:
            self.git.cherry_pick('-x', refname, _env=env)
        except sh.ErrorReturnCode:
            raise GitGerritError(f"Failed to cherry-pick {refname}")

    def show_refs(self, pattern=".*", **options):
        for line in self.git("show-ref", _iter=True, **options):
            if m := re.match(f"^([0-9a-fA-F]+) ({pattern})$", line.rstrip()):
                sha1 = m.group(1)
                ref = m.group(2)
                yield [sha1, ref]

    #
    # Odds and ends.
    #

    def does_branch_exist(self, name):
        """Determine if the branch exists in the local repo."""
        try:
            self.git("show-ref", "--quiet", f"refs/heads/{name}")
            return True
        except sh.ErrorReturnCode:
            return False

    def change_id(self, sha1):
        change_id = None
        format_ = "%(trailers:key=Change-Id)"
        for line in self.log(sha1, max_count=1, pretty=format_):
            m = re.match(r'Change-Id: (I[0-9a-fA-F]+)', line)
            if m:
                change_id = m.group(1)
        return change_id

    def cherry_picked_from(self, sha1):
        xsha1 = None
        for line in self.log(sha1, max_count=1, pretty="%B"):
            m = re.match(r'^\(cherry picked from commit ([0-9a-fA-F]+)\)', line)
            if m:
                xsha1 = m.group(1)
        return xsha1

    def _prepare_hook_path(self, name):
        git_dir = self.git_dir()
        hook_dir = os.path.join(git_dir, "hooks")
        if not os.path.exists(hook_dir):
            os.mkdir(hook_dir)
        hook_path = os.path.join(hook_dir, name)
        return hook_path

    def download_hook(self, name, spinner=None):
        """Download a script from the gerrit server into the git hooks directory."""

        def report_progress(block_num, block_size, total_size):
            if spinner:
                spinner.spin()

        hook_path = self._prepare_hook_path(name)
        if not os.path.exists(hook_path):
            host = self.config('host')
            url = f"https://{host}/tools/hooks/{name}"
            urllib.request.urlretrieve(url, hook_path, report_progress)
            os.chmod(hook_path, 0o755)
            if spinner:
                spinner.spin()

    def write_hook(self, name, spinner=None):
        """Write a script into the git hooks directory."""
        if name not in HOOKS:
            raise ValueError(f"Unknown hook name {name}")

        hook_path = self._prepare_hook_path(name)
        if not os.path.exists(hook_path):
            with open(hook_path, 'w') as f:
                f.write(HOOKS[name])
                if spinner:
                    spinner.spin()
            os.chmod(hook_path, 0o755)
            if spinner:
                spinner.spin()
