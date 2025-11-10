import pytest
import os
import sh

import git_gerrit


class MockCommandBase:
    def __init__(self, *args, **kwargs):
        pass

    def bake(self, *args, **kwargs):
        return self


class MockGitCommand(MockCommandBase):

    def __init__(self, log_test_data, *args, **kwargs):
        self._debug = False
        self._log_test_data = log_test_data
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self._debug:
            print(f"\nMockGitCommand.__call__(): args={args}, kwargs={kwargs}")
        if args == ('rev-parse', '--git-dir'):
            return ".git"
        if args == ('show-ref', '--quiet', 'refs/heads/gerrit/12345/7'):
            sh.ErrorReturnCode.exit_code = 1
            raise sh.ErrorReturnCode("git show-ref", b"", b"ref not found")
        if args == ('show-ref', '--quiet', 'refs/heads/branch-exists'):
            return ""
        if args == ('show-ref', '--quiet', 'refs/heads/branch-is-missing'):
            sh.ErrorReturnCode.exit_code = 1
            raise sh.ErrorReturnCode("git show-ref", b"", b"")
        if args == ('show-ref',):
            return [
                f"{1:040} refs/changes/01/0001/1",
                f"{2:040} refs/changes/01/0001/2",
                f"{3:040} refs/changes/01/0001/3",
                f"{4:040} refs/changes/02/0002/1",
            ]
        raise NotImplementedError(f"MockGitCommand: git {args}")

    def _write_args(self, name, args):
        """Write mocked arguments to a file to be checked by the tests."""
        with open(f"mock-{name}", "w") as f:
            for arg in args:
                f.write(f"{arg}\n")

    def config(self, op, name, *args, **kwargs):
        if self._debug:
            print(
                "\nMockGitCommand.config(): ",
                f"op={op}, name={name}, args={args}, kwargs={kwargs}",
            )
        if op != "--get":
            raise ValueError(f"Unexpected operation: {op}")
        if name == "gerrit.project":
            value = "mayhem"
        elif name == "gerrit.host":
            value = "gerrit.example.org"
        else:
            sh.ErrorReturnCode_1.exit_code = 1
            raise sh.ErrorReturnCode_1(
                f"git config --get gerrit.{name}", b"", b"not found"
            )
        return value

    def log(self, *args, **kwargs):
        if self._debug:
            print(f"\nMockGitCommand.log(): args={args}, kwargs={kwargs}")
        kwargs.pop("_iter", None)  # Remove the magic sh keyword.
        options = kwargs.copy()
        pretty = options.pop("pretty", "")
        options.pop("max_count", None)  # ignore for now

        if options is True:
            # Check for unnhandled options.
            raise NotImplementedError(f"MockGitCommand: git log {args} {kwargs}")

        try:
            log = self._log_test_data(pretty)
        except KeyError:
            raise NotImplementedError(f"MockGitCommand: git log {args} {kwargs}")

        return log

    def fetch(self, *args, **kwargs):
        if self._debug:
            print(f"\nMockGitCommand.fetch(): args={args}, kwargs={kwargs}")
        self._write_args("fetch", args)

    def checkout(self, *args, **kwargs):
        if self._debug:
            print(f"\nMockGitCommand.checkout(): args={args}, kwargs={kwargs}")
        self._write_args("checkout", args)

    def cherry_pick(self, *args, **kwargs):
        if self._debug:
            print(f"\nMockGitCommand.cherry_pick(): args={args}, kwargs={kwargs}")
        self._write_args("cherry-pick", args)


class MockSshCommand(MockCommandBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return


@pytest.fixture
def change_test_data():
    def data(number):
        change = TESTDATA_REST[number]
        return change.copy()  # Return a copy.

    return data


@pytest.fixture
def log_test_data():
    def data(name):
        log = TESTDATA_LOG[name]
        return log.splitlines()  # Return as lines.

    return data


@pytest.fixture
def tmp_gitdir(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    os.mkdir(".git")
    yield
    os.chdir(old_cwd)


@pytest.fixture
def mock_sh(monkeypatch, tmp_gitdir, log_test_data):

    def make_command(name):
        if name == "git":
            command = MockGitCommand(log_test_data)
        elif name == "ssh":
            command = MockSshCommand()
        else:
            raise ValueError(f"Unexpected command: {name}")
        return command

    monkeypatch.setattr(git_gerrit.git.sh, "Command", make_command)
    monkeypatch.setattr(git_gerrit.core.sh, "Command", make_command)


@pytest.fixture
def mock_pygerrit2(monkeypatch, change_test_data):

    def get(self, endpoint, return_response=False, **kwargs):
        change = change_test_data("12345")
        return [change]

    monkeypatch.setattr(git_gerrit.core.pygerrit2.GerritRestAPI, "get", get)


@pytest.fixture
def mock_urlrequest(monkeypatch):

    def urlretrieve(url, path, reporthook=None):
        with open(path, "w") as f:
            f.write("#!/bin/sh\n")

    monkeypatch.setattr(git_gerrit.git.urllib.request, "urlretrieve", urlretrieve)


@pytest.fixture
def mock_modules(mock_sh, mock_pygerrit2, mock_urlrequest):
    return


TESTDATA_REST = {
    "12345": {
        "_number": 12345,
        "branch": "master",
        "change_id": "I0123456789abcdef0123456789abcdef01234567",
        "created": "2021-08-11 23:05:36.225000000",
        "current_revision": "0123456789abcdef0123456789abcdef01234567",
        "deletions": 5,
        "hashtags": [],
        "id": "mayhem~master~I0123456789abcdef0123456789abcdef01234567",
        "insertions": 23,
        "mergeable": False,
        "owner": {"_account_id": 1000000},
        "project": "mayhem",
        "revisions": {
            "0123456789abcdef0123456789abcdef01234567": {
                "_number": 7,
                "created": "2024-05-23 " "20:57:22.491000000",
                "fetch": {
                    "anonymous http": {
                        "ref": "refs/changes/45/12345/7",
                        "url": "https://gerrit.example.org/mayhem",
                    }
                },
                "kind": "TRIVIAL_REBASE",
                "ref": "refs/changes/45/12345/7",
                "uploader": {"_account_id": 1000008},
            }
        },
        "status": "NEW",
        "subject": "Transmogrify the frobnicator",
        "submit_type": "CHERRY_PICK",
        "submittable": False,
        "updated": "2024-05-23 21:45:57.862000000",
    },
}

TESTDATA_LOG = {
    "": """\
commit 5b0775c48db9d89a2e570c0a3417b240c265df6f
Author: Alice <alice@example.com>
Date:   Thu Sep 18 14:00:13 2025 -0500

    config: Include afs/lock.h, not lock.h

    Many source files #include either src/afs/lock.h for kernel code (aka
    <afs/lock.h>), or src/lwp/lock.h for userspace code (aka <lock.h>).

    This one file, src/config/icl.h, includes "lock.h" but refers to the
    kernel afs/lock.h. This works because of how we set our include paths
    while building kernel modules, but is confusing and unnecessary. Change
    this to include "afs/lock.h" instead, to be more consistent about how we
    include this header.

    Change-Id: Id25480174c7fa8465357cc40f9a63e24c9271f95
    Reviewed-on: https://gerrit.openafs.org/16549
    Reviewed-by: Charles <charles@example.com>
    Reviewed-by: Bob <bob@example.com>
    Tested-by: BuildBot <buildbot@example.com>
    Reviewed-by: Alice <alice@example.com>

commit 30c9bddef972ced072771b17554cf0e8cf572970
Author: alice <alice@example.com>
Date:   Wed Sep 10 15:03:14 2025 +0530

    afs: Free dynamically allocated memory for cellName in token.c

    The function ktc_ListTokensEx() allocates memory for cellName,
    which was not being freed in token.c

    This commit frees the allocated memory.

    Co-authored-by: Bob bob@example.com
    Co-authored-by: Bob bob@example.com
    Change-Id: I24dd9a04efe1f13432a8a1b1570a979c7a62d405
    Reviewed-on: https://gerrit.openafs.org/16541
    Reviewed-by: Alice <alice@example.com>
    Reviewed-by: Charles <charles@example.com>
    Tested-by: Charles <charles@example.com>
    Reviewed-by: Charles <charles@example.com>

""",
    "%H": """\
103629bb91257ff5eba181fc82b81692e42e1954
5b0775c48db9d89a2e570c0a3417b240c265df6f
30c9bddef972ced072771b17554cf0e8cf572970
""",
    "oid:%H%nhash:%h%nsubject:%s%nauthor:%an%nemail:%ae%nbody:%n%b%n%%%%": """\
oid:103629bb91257ff5eba181fc82b81692e42e1954
hash:103629bb91
subject:Use wrapper
author:Bob
email:bob@example.com
body:
Replace the single test-runner wrapper with per-binary wrappers so each
%%
oid:5b0775c48db9d89a2e570c0a3417b240c265df6f
hash:5b0775c48d
subject:config: Include afs/lock.h
author:Alice
email:alice@example.com
body:
Many source files #include either src/afs/lock.h for kernel code (aka
<afs/lock.h>), or src/lwp/lock.h for userspace code (aka <lock.h>).

This one file, src/config/icl.h, includes "lock.h" but refers to the
kernel afs/lock.h. This works because of how we set our include paths
while building kernel modules, but is confusing and unnecessary. Change
this to include "afs/lock.h" instead, to be more consistent about how we
include this header.

Change-Id: Id25480174c7fa8465357cc40f9a63e24c9271f95
Reviewed-on: https://gerrit.openafs.org/16549
Tested-by: BuildBot <buildbot@example.com>
%%
oid:30c9bddef972ced072771b17554cf0e8cf572970
hash:30c9bddef9
subject:afs: Free dynamically allocated memory
author:alice
email:alice@example.com
body:
The function ktc_ListTokensEx() allocates memory for cellName,
which was not being freed in token.c

This commit frees the allocated memory.

Change-Id: I24dd9a04efe1f13432a8a1b1570a979c7a62d405
Reviewed-on: https://gerrit.openafs.org/16541
%%
""",
    "oid:%H%nhash:%H%nsubject:%s%nauthor:%an%nemail:%ae%nbody:%n%b%n%%%%": """\
oid:5b0775c48db9d89a2e570c0a3417b240c265df6f
hash:5b0775c48db9d89a2e570c0a3417b240c265df6f
subject:config: Include afs/lock.h, not lock.h
author:Alice
email:alice@example.com
body:
Many source files #include either src/afs/lock.h for kernel code (aka
<afs/lock.h>), or src/lwp/lock.h for userspace code (aka <lock.h>).

This one file, src/config/icl.h, includes "lock.h" but refers to the
kernel afs/lock.h. This works because of how we set our include paths
while building kernel modules, but is confusing and unnecessary. Change
this to include "afs/lock.h" instead, to be more consistent about how we
include this header.

Change-Id: Id25480174c7fa8465357cc40f9a63e24c9271f95
Reviewed-on: https://gerrit.openafs.org/16549
Reviewed-by: Charles <charles@example.com>
Reviewed-by: Bob <bob@example.com>
Tested-by: BuildBot <buildbot@example.com>
Reviewed-by: Alice <alice@example.com>
%%
oid:30c9bddef972ced072771b17554cf0e8cf572970
hash:30c9bddef972ced072771b17554cf0e8cf572970
subject:afs: Free dynamically allocated memory for cellName in token.c
author:alice
email:alice@example.com
body:
The function ktc_ListTokensEx() allocates memory for cellName,
which was not being freed in token.c

This commit frees the allocated memory.

Co-authored-by: Bob bob@example.com
Co-authored-by: Bob bob@example.com
Change-Id: I24dd9a04efe1f13432a8a1b1570a979c7a62d405
Reviewed-on: https://gerrit.openafs.org/16541
Reviewed-by: Alice <alice@example.com>
Reviewed-by: Charles <charles@example.com>
Tested-by: Charles <charles@example.com>
Reviewed-by: Charles <charles@example.com>
%%
oid:84534b5cf468f93ff1e83c8148af90b011124815
hash:84534b5cf468f93ff1e83c8148af90b011124815
subject:Linux: Use a stable dentry name in d_revalidate
author:Charles
email:charles@example.com
body:
Accessing a stable dentry name (dentry.d_name) directly requires taking
the d_lock, which can only be held for a short periods of time and
cannot be easily used in d_revalidate

The Linux 4.13 commit:
    dentry name snapshots (49d31c2f389ac)
provides a utility function, take_dentry_name_snapshot(), that creates a
safe copy of the dentry name.

Update the d_revalidate function to obtain a stable dentry name instead
of making multiple accesses to the dentry name directly in an unsafe
manner.

Create wrapper functions get_stable_dentry_name() and
release_stable_dentry_name() for take_dentry_name_snapshot() and
release_dentry_name_snapshot() to help deal with backward compatibility
with Linux versions prior to the 49d31c2f389ac commit.

For Linux versions where take_dentry_name_snapshot is available, use the
take_dentry_sname_snapshot but also return a pointer to the name that
was obtained (name_snapshot.name).

For Linux versions prior that do not have the take_dentry_name_snapshot
the wrapper function simply returns a pointer to the dentry's
d_name.name, so the existing behavior of accessing the d_name remains
the same.

Add configure checks to determine if take_dentry_name_snapshot exists,
and if so check the datatype used within the name_snapshot structure
to see if it is a qstr or not.  (Some distributions backported the
49d31c2f389ac commit for older Linux kernels, but the name_snapshot
structure uses a char * instead of a qstr).

Add a compile time check to ensure that Linux provides
take_dentry_name_snapshot() after 4.13 so errors during 'configure'
don't cause us to silently use the unsafe code path by mistake.

Note: This commit doesn't address the issues of using an unstable d_name
for Linux versions that do not provide the take_dentry_name_snapshot().
For these versions of Linux, there are problems within the Linux code
base itself surrounding the use of the dentry's name.

Change-Id: Ic99b1e5d7667f6841feea78ccf94db43ede40356
Reviewed-on: https://gerrit.openafs.org/16528
Reviewed-by: Alice <alice@example.com>
Reviewed-by: Charles <charles@example.com>
Reviewed-by: Bob <bob@example.com>
Tested-by: Bob <bob@example.com>
%%
""",
    "%(trailers:key=Change-Id)": """\
Change-Id: I68fd140aab7e65bec1ac537d19de89f9d32443c1

""",
    "%B": """\
Foo bar baz

Update all foos in the tree, and the baz file.

Reviewed-on: https://gerrit.openafs.org/12345
Reviewed-by: Alice <alice@example.com>
Reviewed-by: Charles <charles@example.com>
Reviewed-by: Bob <bob@example.com>
(cherry picked from commit 75a3a91f5086c011e91bf638e2cc8c03ee373266)

Change-Id: Ibc6dab9f4a99d693ea03891ed7222fed9a07a85a
Reviewed-on: https://gerrit.openafs.org/12345
Reviewed-by: Alice <alice@example.com>
Reviewed-by: Charles <charles@example.com>
Reviewed-by: Bob <bob@example.com>

""",
}
