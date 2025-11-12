import os
import pytest

from git_gerrit.core import (
    cherry_pick,
    current_change,
    fetch,
    get_current_change,
    log,
    query,
    sync,
    update,
)
from git_gerrit.error import GitGerritError, GitGerritNotFoundError


def test_query(mock_modules):
    search = "12345"
    changes = list(query(search))
    assert len(changes) == 1
    change = changes[0]
    assert change["number"] == 12345
    assert change["hash"] == "0123456789abcdef0123456789abcdef01234567"
    assert change["patchset"] == 7
    assert change["ref"] == "refs/changes/45/12345/7"
    assert change["localref"] == "origin/changes/45/12345/7"
    assert change["host"] == "gerrit.example.org"
    assert change["url"] == "https://gerrit.example.org/12345"
    assert change["topic"] == ""
    assert "details" not in change


def test_fetch__without_branch(capsys, mock_modules):
    fetch(12345)
    output = capsys.readouterr().out.splitlines()
    assert output[0] == "searching for gerrit 12345"
    assert output[1] == "found patchset number 7"
    assert output[2] == "fetching 12345,7"
    assert output[3] == "fetched 12345,7 to FETCH_HEAD"
    assert os.path.exists("mock-fetch")
    with open("mock-fetch", "r") as f:
        mock_fetch = f.read().splitlines()
    assert mock_fetch[0] == "https://gerrit.example.org/mayhem"
    assert mock_fetch[1] == "refs/changes/45/12345/7"


def test_fetch__with_branch(capsys, mock_modules):
    fetch(12345, branch="gerrit/{number}/{patchset}")
    output = capsys.readouterr().out.splitlines()
    assert output[0] == "searching for gerrit 12345"
    assert output[1] == "found patchset number 7"
    assert output[2] == "fetching 12345,7 to branch gerrit/12345/7"
    assert output[3] == "fetched 12345,7 to branch gerrit/12345/7"
    assert os.path.exists("mock-fetch")
    with open("mock-fetch", "r") as f:
        mock_fetch = f.read().splitlines()
    assert mock_fetch[0] == "https://gerrit.example.org/mayhem"
    assert mock_fetch[1] == "refs/changes/45/12345/7:gerrit/12345/7"


def test_update(mock_modules):
    update(12345, message="test")


def test_cherry_pick__succeeds(mock_modules):
    cherry_pick(16549, "master")
    assert os.path.exists("mock-cherry-pick")
    with open("mock-cherry-pick", "r") as f:
        mock_cherry_pick = f.read().splitlines()
    assert mock_cherry_pick == ["-x", "5b0775c48db9d89a2e570c0a3417b240c265df6f"]


def test_cherry_pick__raises_exception_when_change_is_not_found(mock_modules):
    expected = "Failed to find gerrit number 12345 on branch master."
    with pytest.raises(GitGerritError, match=expected):
        cherry_pick(12345, "master")


def test_current_change(mock_modules, change_test_data):
    expected = change_test_data("12345")
    got = current_change(12345)
    assert got["_number"] == expected["_number"]
    assert got["change_id"] == expected["change_id"]
    assert got["branch"] == expected["branch"]


def test_log(mock_modules):
    got = list(log())
    # Mocked test data.
    assert got[0]["author"] == "Bob"
    assert got[0]["hash"] == "103629bb91"
    assert got[0]["number"] == ""
    assert got[0]["subject"] == "Use wrapper"
    assert got[1]["author"] == "Alice"
    assert got[1]["hash"] == "5b0775c48d"
    assert got[1]["number"] == 16549
    assert got[1]["subject"] == "config: Include afs/lock.h"


def test_get_current_change__not_found(mock_modules):
    expected = "Change 12345 not found."
    with pytest.raises(GitGerritNotFoundError, match=expected):
        get_current_change(12345)


def test_sync(capsys, mock_modules):
    sync()
    output = capsys.readouterr().out.splitlines()
    print(output)
    assert os.path.exists("mock-fetch")
    with open("mock-fetch", "r") as f:
        mock_fetch = f.read().splitlines()
    assert mock_fetch[0] == "https://gerrit.example.org/mayhem"
    assert mock_fetch[1] == "refs/changes/*:refs/changes/*"
