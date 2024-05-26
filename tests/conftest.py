import pytest
import git_gerrit
import git_gerrit.cli


@pytest.fixture
def argv():
    argv = []
    return argv


@pytest.fixture
def output(monkeypatch):
    output = []

    def capture(*items, out=None, newline=True):
        message = ' '.join([str(item) for item in items])
        output.append(message)

    monkeypatch.setattr(git_gerrit.cli, "writeln", capture)
    return output


@pytest.fixture
def mock_config(monkeypatch):
    test_config = {
        "project": "mayhem",
        "host": "gerrit.example.org",
    }

    def _get(self, name, default=None):
        return test_config.get(name, default)

    monkeypatch.setattr(git_gerrit.Config, "_get", _get)


@pytest.fixture
def mock_rest_get(monkeypatch, mock_config):
    test_change = {
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
    }

    def get(self, endpoint, return_response=False, **kwargs):
        return [test_change]

    monkeypatch.setattr(git_gerrit.pygerrit2.GerritRestAPI, "get", get)
