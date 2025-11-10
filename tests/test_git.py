import os
import stat
import pytest
import git_gerrit.git


@pytest.fixture
def git(mock_modules):
    return git_gerrit.git.Git()


def test_config__good_name_returns_value(git):
    assert git.config("project") == "mayhem"
    assert git.config("host") == "gerrit.example.org"


def test_config__unknown_name_raises_exception(git):
    with pytest.raises(ValueError):
        git.config("bogus")


def test_git_dir(git):
    assert git.git_dir().startswith("/tmp")  # Verify this is a test sandbox.
    assert git.git_dir().endswith(".git")
    assert os.path.exists(git.git_dir())
    assert os.path.isdir(git.git_dir())


def test_remote(git):
    assert git.remote() == "https://gerrit.example.org/mayhem"


def test_fetch(git):
    git.fetch("test-fetch-branch-name")
    with open("mock-fetch", "r") as f:
        mock_fetch = f.read().splitlines()
    assert mock_fetch[0] == "https://gerrit.example.org/mayhem"
    assert mock_fetch[1] == "test-fetch-branch-name"


def test_checkout(git):
    git.checkout("test-checkout-branch-name")
    with open("mock-checkout", "r") as f:
        mock_checkout = f.read().splitlines()
    assert mock_checkout[0] == "test-checkout-branch-name"


def test_log(git, log_test_data):
    expected = log_test_data("")
    got = list(git.log())
    assert got == expected


def test_cherry_pick(git):
    git.cherry_pick("test-cherry-pick-branch-name")
    with open("mock-cherry-pick", "r") as f:
        mock_cherry_pick = f.read().splitlines()
    assert mock_cherry_pick[0] == "-x"
    assert mock_cherry_pick[1] == "test-cherry-pick-branch-name"


def test_does_branch_exist__returns_true_when_branch_is_present(git):
    assert git.does_branch_exist("branch-exists") is True


def test_does_branch_exist__returns_false_branch_is_missing(git):
    assert git.does_branch_exist("branch-is-missing") is False


def test_download_hook(git):
    git.download_hook("commit-msg")
    assert os.path.exists(".git/hooks/commit-msg")
    mode = os.stat(".git/hooks/commit-msg").st_mode
    assert mode & stat.S_IXUSR != 0
    assert mode & stat.S_IXGRP != 0


def test_write_hook(git):
    git.write_hook("prepare-commit-msg")
    assert os.path.exists(".git/hooks/prepare-commit-msg")
    mode = os.stat(".git/hooks/prepare-commit-msg").st_mode
    assert mode & stat.S_IXUSR != 0
    assert mode & stat.S_IXGRP != 0


def test_change_id(git):
    got = git.change_id("0" * 40)
    assert got == "I68fd140aab7e65bec1ac537d19de89f9d32443c1"
