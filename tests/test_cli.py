import re

import git_gerrit
import git_gerrit.cli


def test_help(monkeypatch, argv):
    messages = []

    def grab_output(message):
        messages.append(message)

    monkeypatch.setattr(git_gerrit.cli, "print_info", grab_output)
    git_gerrit.cli.git_gerrit_help(argv)
    assert "Commands for gerrit code review" in messages[0]


def test_query(monkeypatch, mock_config, mock_change, argv):
    messages = []

    def mock_config_get(self, name, default=None):
        return mock_config.get(name, default)

    def mock_rest_get(self, endpoint, return_response=False, **kwargs):
        return [mock_change]

    def grab_output(message, out=None):
        messages.append(message)

    monkeypatch.setattr(git_gerrit.Config, "_get", mock_config_get)
    monkeypatch.setattr(git_gerrit.pygerrit2.GerritRestAPI, "get", mock_rest_get)
    monkeypatch.setattr(git_gerrit.cli, "print_info", grab_output)

    argv.append("12345")
    git_gerrit.cli.git_gerrit_query(argv)

    assert len(messages) == 1
    assert messages[0] == "12345 Transmogrify the frobnicator"


def test_version(monkeypatch, argv):
    messages = []

    def grab_output(message):
        messages.append(message)

    monkeypatch.setattr(git_gerrit.cli, "print_info", grab_output)
    git_gerrit.cli.git_gerrit_version(argv)
    version = messages[0]
    assert re.match(r"^\d+\.\d+\.\d+", version)
