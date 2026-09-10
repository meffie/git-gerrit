import pytest

from git_gerrit.db import GitGerritDB, Cursor, SCHEMA_VERSION


@pytest.fixture
def db(mock_modules):
    with GitGerritDB() as db:
        yield db


@pytest.fixture
def staged_db(mock_modules):
    with GitGerritDB() as db:
        db.add_patchset(101, 1, "aaa")
        db.add_patchset(101, 2, "bbb")
        db.add_patchset(102, 1, "ccc")
        db.add_patchset(103, 1, "ddd")
        db.add_patchset(103, 2, "eee")
        db.add_patchset(103, 3, "fff")
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
    assert "commits" in names
    assert "gerrit_patchsets" in names
    assert "gerrit_changes" in names
    assert "gerrit_duplicate_changes" in names


def test_db_add_patchset__inserts_into_tables(db):
    db.add_patchset(123, 1, "abc")
    with Cursor(db) as cursor:
        cursor.execute("SELECT * FROM gerrit_patchsets WHERE number=123")
        change = cursor.fetchone()
        assert change is not None
        assert change["patchset"] == 1
        assert change["commit_id"] == "abc"

        cursor.execute("SELECT * FROM commits WHERE commit_id='abc'")
        commit = cursor.fetchone()
        assert commit is not None
        assert commit["flags"] == 0


def _dup_rows(db):
    with Cursor(db) as cursor:
        cursor.execute(
            "SELECT number, change_id, canonical_number "
            "FROM gerrit_duplicate_changes ORDER BY number"
        )
        return [tuple(row) for row in cursor.fetchall()]


def _change_rows(db):
    with Cursor(db) as cursor:
        cursor.execute(
            "SELECT number, current_patchset, change_id "
            "FROM gerrit_changes ORDER BY number"
        )
        return [tuple(row) for row in cursor.fetchall()]


def test_db_record_change__inserts_and_updates_canonical(db):
    assert db.record_change(200, 1, "I200") is True
    assert _change_rows(db) == [(200, 1, "I200")]

    # A rescan of the same change refreshes the patchset in place.
    assert db.record_change(200, 2, "I200") is True
    assert _change_rows(db) == [(200, 2, "I200")]
    assert _dup_rows(db) == []


def test_db_record_change__sidebars_higher_numbered_duplicate(db):
    db.record_change(300, 1, "Ishared")
    assert db.record_change(305, 1, "Ishared") is False

    assert _change_rows(db) == [(300, 1, "Ishared")]
    assert _dup_rows(db) == [(305, "Ishared", 300)]


def test_db_record_change__lower_number_takes_over_as_canonical(db):
    # Changes arrive newest-first, as git-gerrit-sync scans them.
    db.record_change(305, 1, "Ishared")
    db.record_change(303, 1, "Ishared")
    db.record_change(300, 1, "Ishared")

    assert _change_rows(db) == [(300, 1, "Ishared")]
    assert _dup_rows(db) == [(303, "Ishared", 300), (305, "Ishared", 300)]


def test_db_record_change__canonical_stable_when_scanned_oldest_first(db):
    db.record_change(300, 1, "Ishared")
    db.record_change(303, 1, "Ishared")
    db.record_change(305, 1, "Ishared")

    assert _change_rows(db) == [(300, 1, "Ishared")]
    assert _dup_rows(db) == [(303, "Ishared", 300), (305, "Ishared", 300)]


def test_db_record_change__is_idempotent_across_rescans(db):
    for _ in range(2):
        db.record_change(305, 1, "Ishared")
        db.record_change(303, 2, "Ishared")
        db.record_change(300, 3, "Ishared")

    assert _change_rows(db) == [(300, 3, "Ishared")]
    assert _dup_rows(db) == [(303, "Ishared", 300), (305, "Ishared", 300)]


def test_db_get_change__returns_canonical_only(db):
    db.record_change(300, 1, "Ishared")
    db.record_change(305, 2, "Ishared")

    assert db.get_change("Ishared")["number"] == 300
    assert db.get_change("Imissing") is None


def test_db_count_duplicate_changes(db):
    db.record_change(300, 1, "Ishared")
    db.record_change(305, 1, "Ishared")
    db.record_change(400, 1, "Iunique")

    assert db.count_duplicate_changes() == 1


def test_db_update_commit__updates_commit_row(db):
    db.add_patchset(123, 1, "abc")
    db.update_commit("abc", "I123", "def", 1)
    with Cursor(db) as cursor:
        cursor.execute("SELECT * FROM commits WHERE commit_id='abc'")
        commit = cursor.fetchone()
        assert commit is not None
        assert commit["change_id"] == "I123"
        assert commit["cherry_picked_from"] == "def"
        assert commit["flags"] == 1


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
