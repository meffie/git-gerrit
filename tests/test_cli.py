import os
import stat
import re

import pytest

from git_gerrit.cli import (
    main_git_gerrit_version,
    main_git_gerrit_checkout,
    main_git_gerrit_cherry_pick,
    main_git_gerrit_fetch,
    main_git_gerrit_help,
    main_git_gerrit_install_hooks,
    main_git_gerrit_log,
    main_git_gerrit_number,
    main_git_gerrit_query,
    main_git_gerrit_sync,
    main_git_gerrit_update,
)


def test_help__prints_commands(capsys, mock_modules):
    exit_code = main_git_gerrit_help([])
    assert exit_code == 0
    stdout = capsys.readouterr().out
    expected = """
Available commands:

    git gerrit-checkout          Fetch then checkout by gerrit number.
    git gerrit-cherry-pick       Cherry pick from upstream branch by gerrit number to make a new gerrit.
    git gerrit-fetch             Fetch by gerrit number.
    git gerrit-help              List commands.
    git gerrit-install-hooks     Install git hooks to create gerrit change-ids.
    git gerrit-log               Show oneline log with gerrit numbers.
    git gerrit-number            Show info for a gerrit change number.
    git gerrit-query             Search gerrit.
    git gerrit-sync              Fetch all changes and update the local database.
    git gerrit-update            Update gerrits matching search terms.
    git gerrit-version           Print version and exit.

Show command help with:

    git gerrit-<command> -h
"""  # noqa: E501
    assert stdout == expected


@pytest.mark.parametrize(
    "options",
    [
        [],
        ["-f", "{number} {subject}"],
        ["--format", "{number} {subject}"],
        ["--format={number} {subject}"],
    ],
)
def test_query__number_and_subject(options, capsys, mock_modules):
    options.append("12345")
    exit_code = main_git_gerrit_query(options)
    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "12345 Transmogrify the frobnicator" in stdout


@pytest.mark.parametrize(
    "key,value",
    [
        ("branch", "master"),
        ("change_id", "I0123456789abcdef0123456789abcdef01234567"),
        ("created", "2021-08-11 23:05:36.225000000"),
        ("current_revision", "0123456789abcdef0123456789abcdef01234567"),
        ("deletions", "5"),
        ("hashtags", ""),
        ("id", "mayhem~master~I0123456789abcdef0123456789abcdef01234567"),
        ("insertions", "23"),
        ("owner", "1000000"),
        ("project", "mayhem"),
        ("status", "NEW"),
        ("subject", "Transmogrify the frobnicator"),
        ("submittable", "False"),
        ("submitted", ""),
        ("topic", ""),
        ("updated", "2024-05-23 21:45:57.862000000"),
        ("number", "12345"),
        ("patchset", "7"),
        ("ref", "refs/changes/45/12345/7"),
        ("localref", "origin/changes/45/12345/7"),
        ("hash", "0123456789abcdef0123456789abcdef01234567"),
        ("host", "gerrit.example.org"),
        ("url", "https://gerrit.example.org/12345"),
    ],
)
def test_query__format_key(key, value, capsys, mock_modules):
    exit_code = main_git_gerrit_query(["--format={" + key + "}", "12345"])
    assert exit_code == 0
    got = capsys.readouterr().out.rstrip()
    assert value == got


def test_query__invalid_format_key_fails(capsys, mock_modules):
    exit_code = main_git_gerrit_query(["--format='{bogus}'", "12345"])
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "Invalid --format" in stderr
    assert "bogus" in stderr


def test_query__invalid_format_specifier_fails(capsys, mock_modules):
    exit_code = main_git_gerrit_query(["--format='{number:bogus}'", "12345"])
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "Invalid --format" in stderr
    assert "Invalid format specifier" in stderr


def test_query__fails_when_no_terms_given(capsys, mock_modules):
    with pytest.raises(SystemExit) as e:
        main_git_gerrit_query([])
    assert e.value.code == 2
    stderr = capsys.readouterr().err
    assert "the following arguments are required: <term>" in stderr


def test_number(capsys, mock_modules):
    exit_code = main_git_gerrit_number(["12345"])
    assert exit_code == 1


def test_sync(capsys, mock_modules):
    exit_code = main_git_gerrit_sync([])
    assert exit_code == 0


def test_version__prints_a_version_string(capsys, mock_modules):
    exit_code = main_git_gerrit_version([])
    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert re.search(r'^\d+\.\d+\.\d+', stdout)


def test_checkout__without_branch_succeeds(capsys, mock_modules):
    exit_code = main_git_gerrit_checkout(["12345"])
    assert exit_code == 0
    assert os.path.exists("mock-checkout")
    with open("mock-checkout", "r") as f:
        mock_checkout = f.read().rstrip()
    assert mock_checkout == "FETCH_HEAD"


def test_checkout__to_branch_succeeds(capsys, mock_modules):
    exit_code = main_git_gerrit_checkout(
        ["12345", "--branch", "gerrit/{number}/{patchset}"]
    )
    assert exit_code == 0
    assert os.path.exists("mock-checkout")
    with open("mock-checkout", "r") as f:
        mock_checkout = f.read().rstrip()
    assert mock_checkout == "gerrit/12345/7"


def test_cherry_pick__fails_when_gerrit_is_not_found(capsys, mock_modules):
    exit_code = main_git_gerrit_cherry_pick(["12345"])
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "Failed to find gerrit number" in stderr


def test_fetch__without_branch_succeeds(capsys, mock_modules):
    exit_code = main_git_gerrit_fetch(["12345"])
    assert exit_code == 0
    assert os.path.exists("mock-fetch")
    with open("mock-fetch", "r") as f:
        mock_fetch = f.read().splitlines()
    assert mock_fetch[0] == "https://gerrit.example.org/mayhem"
    assert mock_fetch[1] == "refs/changes/45/12345/7"


def test_fetch__to_branch_succeeds(capsys, mock_modules):
    exit_code = main_git_gerrit_fetch(
        ["12345", "--branch", "gerrit/{number}/{patchset}"]
    )
    assert exit_code == 0
    assert os.path.exists("mock-fetch")
    with open("mock-fetch", "r") as f:
        mock_fetch = f.read().splitlines()
    assert mock_fetch[0] == "https://gerrit.example.org/mayhem"
    assert mock_fetch[1] == "refs/changes/45/12345/7:gerrit/12345/7"


def test_install_hook(capsys, mock_modules):
    assert not os.path.exists(".git/hooks/commit-msg")
    assert not os.path.exists(".git/hooks/prepare-commit-msg")

    exit_code = main_git_gerrit_install_hooks([])
    assert exit_code == 0

    assert os.path.exists(".git/hooks/commit-msg")
    mode = os.stat(".git/hooks/commit-msg").st_mode
    assert mode & stat.S_IXUSR != 0
    assert mode & stat.S_IXGRP != 0

    assert os.path.exists(".git/hooks/prepare-commit-msg")
    mode = os.stat(".git/hooks/prepare-commit-msg").st_mode
    assert mode & stat.S_IXUSR != 0
    assert mode & stat.S_IXGRP != 0


def test_log__succeeeds(capsys, mock_modules):
    exit_code = main_git_gerrit_log([])
    assert exit_code == 0
    stdout = capsys.readouterr().out
    lines = stdout.splitlines()
    # Check results from canned test data.
    assert lines[0] == " 103629bb91 Use wrapper"
    assert lines[1] == "16549 5b0775c48d config: Include afs/lock.h"
    assert lines[2] == "16541 30c9bddef9 afs: Free dynamically allocated memory"


def test_update(capsys, mock_modules):
    exit_code = main_git_gerrit_update(["12345", "--message=test"])
    assert exit_code == 0
