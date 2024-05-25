import pytest


@pytest.fixture
def argv():
    return []


@pytest.fixture
def mock_config():
    return {
        "project": "mayhem",
        "host": "gerrit.example.org",
        "remote": "origin",
    }


@pytest.fixture
def mock_change():
    return {
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
