import git_gerrit


def test_query(mock_rest_get):

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
