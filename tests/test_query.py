import git_gerrit


def test_query(monkeypatch, mock_config, mock_change):

    def mock_config_get(self, name, default=None):
        return mock_config.get(name, default)

    def mock_rest_get(self, endpoint, return_response=False, **kwargs):
        return [mock_change]

    monkeypatch.setattr(git_gerrit.Config, "_get", mock_config_get)
    monkeypatch.setattr(git_gerrit.pygerrit2.GerritRestAPI, "get", mock_rest_get)

    c = git_gerrit.Config()
    assert c["project"] == "mayhem"
    assert c["host"] == "gerrit.example.org"
    assert c["remote"] == "origin"

    search = "change:12345"
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
