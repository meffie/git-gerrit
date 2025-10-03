import pytest

from git_gerrit.db import GitGerritDB, Cursor, SCHEMA_VERSION


@pytest.fixture
def db(mock_modules):
    with GitGerritDB() as db:
        yield db


@pytest.fixture
def staged_db(mock_modules):
    with GitGerritDB() as db:
        db.add_change(101, 1, "aaa")
        db.add_change(101, 2, "bbb")
        db.add_change(102, 1, "ccc")
        db.add_change(103, 1, "ddd")
        db.add_change(103, 2, "eee")
        db.add_change(103, 3, "fff")
        db.update_commit("bbb", "I101", None, 0)
        db.update_commit("ccc", "I102", None, 1)
        db.update_commit("fff", "I103", "ggg", 0)
        yield db


def test_db_get_schema_version__returns_current_schema_version(db):
    assert db._get_schema_version() == SCHEMA_VERSION


def test_db_init__creates_tables(db):
    with Cursor(db) as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        names = [row['name'] for row in cursor.fetchall()]
    assert len(names) != 0


def test_db_add_change__inserts_into_tables(db):
    db.add_change(123, 1, "abc")
    with Cursor(db) as cursor:
        cursor.execute("SELECT * FROM changes WHERE change_number=123")
        change = cursor.fetchone()
        assert change is not None
        assert change["change_patchset"] == 1
        assert change["change_commit_id"] == "abc"

        cursor.execute("SELECT * FROM commits WHERE commit_id='abc'")
        commit = cursor.fetchone()
        assert commit is not None
        assert commit["commit_flags"] == 0


def test_db_update_commit__updates_commit_row(db):
    db.add_change(123, 1, "abc")
    db.update_commit("abc", "I123", "def", 1)
    with Cursor(db) as cursor:
        cursor.execute("SELECT * FROM commits WHERE commit_id='abc'")
        commit = cursor.fetchone()
        assert commit is not None
        assert commit["commit_change_id"] == "I123"
        assert commit["commit_picked_from"] == "def"
        assert commit["commit_flags"] == 1


def test_db_get_current_patchsets__returns_latest_patchsets(staged_db):
    db = staged_db

    # Test without filters
    changes = list(db.get_current_patchsets())
    assert len(changes) == 3
    assert changes[0]["number"] == 103
    assert changes[0]["current_patchset"] == 3
    assert changes[0]["commit_id"] == "fff"
    assert changes[0]["change_id"] == "I103"
    assert changes[0]["cherry_picked_from"] == "ggg"
    assert changes[0]["flags"] == 0

    assert changes[1]["number"] == 102
    assert changes[1]["current_patchset"] == 1
    assert changes[1]["commit_id"] == "ccc"
    assert changes[1]["change_id"] == "I102"
    assert changes[1]["flags"] == 1

    assert changes[2]["number"] == 101
    assert changes[2]["current_patchset"] == 2
    assert changes[2]["commit_id"] == "bbb"
    assert changes[2]["change_id"] == "I101"
    assert changes[2]["flags"] == 0

    # Test with limit
    changes = list(db.get_current_patchsets(limit=1))
    assert len(changes) == 1
    assert changes[0]["number"] == 103


def test_db_get_current_patchset__returns_latest_patchset_by_number(staged_db):
    db = staged_db
    change = db.get_current_patchset_by_number(101)
    assert change["number"] == 101
    assert change["current_patchset"] == 2
    assert change["commit_id"] == "bbb"
    assert change["change_id"] == "I101"
    assert change["flags"] == 0

    change = db.get_current_patchset_by_number(102)
    assert change["number"] == 102
    assert change["current_patchset"] == 1
    assert change["commit_id"] == "ccc"
    assert change["change_id"] == "I102"
    assert change["flags"] == 1

    change = db.get_current_patchset_by_number(103)
    assert change["number"] == 103
    assert change["current_patchset"] == 3
    assert change["commit_id"] == "fff"
    assert change["change_id"] == "I103"
    assert change["cherry_picked_from"] == "ggg"
    assert change["flags"] == 0

    change = db.get_current_patchset_by_number(999)
    assert change is None
