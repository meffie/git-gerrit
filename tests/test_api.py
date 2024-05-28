import pytest
import git_gerrit


def test_config(mock_commands):
    config = git_gerrit.Config()
    assert config["project"] == "mayhem"
    assert config["host"] == "gerrit.example.org"
    assert config.get("remote", "origin") == "origin"
    with pytest.raises(git_gerrit.error.GitGerritConfigError):
        config["bogus"]


def test_query(output, mock_rest):

    search = "12345"
    changes = list(git_gerrit.query(search))
    assert len(changes) == 1

    change = changes[0]
    assert change["number"] == 12345
    assert change["hash"] == "0123456789abcdef0123456789abcdef01234567"
    assert change["patchset"] == 7
    assert change["ref"] == "refs/changes/45/12345/7"
    assert change["localref"] == "origin/changes/45/12345/7"
    assert change["host"] == "gerrit.example.org"
    assert change["url"] == "https://gerrit.example.org/12345"
    assert change["topic"] == "no-topic"
    assert "details" not in change


def test_fetch(output, mock_rest):
    git_gerrit.fetch(12345)
    assert output[0] == "searching for gerrit 12345"
    assert output[1] == "found patchset number 7"
    assert output[2] == "fetching 12345,7 to branch gerrit/12345/7"
    assert output[3] == "fetched 12345,7 to branch gerrit/12345/7"


def test_update(output, mock_rest):
    git_gerrit.update(12345, message="test")
