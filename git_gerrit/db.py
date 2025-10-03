# Copyright (c) 2025 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import sqlite3
import os

from git_gerrit.git import Git

DATABASE = "git-gerrit.db"
MAGIC = 0x67697467  # "gitg"
SCHEMA_VERSION = 1
MIGRATION_SCRIPTS = [
    """
    CREATE TABLE changes (
        change_number INTEGER,
        change_patchset INTEGER,
        change_commit_id TEXT NOT NULL, /* Not unique */
        PRIMARY KEY (change_number, change_patchset)
    );
    CREATE TABLE commits (
        commit_id TEXT PRIMARY KEY, /* Git object id, e.g., SHA-1 */
        commit_change_id TEXT,      /* Not unique, may be NULL */
        commit_picked_from TEXT,    /* Not unique, may be NULL */
        commit_flags INTEGER,
        FOREIGN KEY (commit_id) REFERENCES commits(change_commit_id)
    );
    """,
]


class Cursor:
    """
    Cursor context manager to ensure cursors are closed.
    """

    def __init__(self, db):
        self._cursor = None
        self._conn = db._conn

    def __enter__(self):
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()
        self._cursor = None


class GitGerritDB:
    """
    Manage a local sqlite database for fast lookups of gerrit numbers.

    This class provides an interface to a local SQLite database to store and
    retrieve information about Gerrit changes, patchsets, and commits. It is
    designed to be used as a context manager to ensure proper handling of the
    database connection.

    Attributes:
        _dirty (bool): True if there are uncommitted changes.
        _database (str): The path to the SQLite database file.
        _exists (bool): True if the database file already exists.
        _conn (sqlite3.Connection): The SQLite database connection object.
    """

    def __init__(self):
        """
        Initializes the GitGerritDB object.

        This method sets up the database connection, creates the database and
        its schema if they don't exist, and handles schema migrations.
        """
        self._dirty = False
        self._database = os.path.join(Git().git_dir(), DATABASE)
        self._exists = os.path.exists(self._database)
        self._conn = sqlite3.connect(self._database)

        # Use a magic number to ensure we created the database.
        if not self._exists:
            self._set_magic()
        else:
            magic = self._get_magic()
            if magic != MAGIC:
                raise ValueError(f"Unexpected magic {magic} in {self._database}")

        # Run SQL migrations to create the tables and update old schemas.
        for version, migrate in enumerate(MIGRATION_SCRIPTS):
            if self._get_schema_version() == version:
                # Migrate from version to version + 1.
                try:
                    self._conn.executescript(migrate)
                except sqlite3.OperationalError as e:
                    raise AssertionError(f"SQL migration error: {e}, {migrate}")
                self._conn.commit()
                self._bump_schema_version()

        # Return rows as dictionaries (instead of tuples).
        self._conn.row_factory = sqlite3.Row

    def __enter__(self):
        """
        Enables the use of the GitGerritDb class as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting the 'with' block to ensure the database connection
        is properly closed.
        """
        self.close()

    def close(self):
        """
        Flush uncommitted changes and close the database connection.
        """
        self._conn.commit()
        self._conn.close()
        self._conn = None

    def _get_magic(self):
        with Cursor(self) as cursor:
            cursor.execute("PRAGMA application_id")
            return cursor.fetchone()[0]

    def _set_magic(self):
        with Cursor(self) as cursor:
            cursor.execute(f"PRAGMA application_id = {MAGIC}")

    def _get_schema_version(self):
        with Cursor(self) as cursor:
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
        return version

    def _bump_schema_version(self):
        version = self._get_schema_version() + 1
        with Cursor(self) as cursor:
            cursor.execute(f"PRAGMA user_version = {version}")
        return version

    def _as_dict(self, row):
        """Convert a row to plain dictionary or None."""
        if row:
            data = dict(zip(row.keys(), row))
        else:
            data = None
        return data

    def add_change(self, number, patchset, commit_id):
        """
        Adds a new change to the database.

        Args:
            number (int): The change number.
            patchset (int): The patchset number.
            commit_id (str): The commit ID (SHA-1).
        """
        with Cursor(self) as cursor:
            cursor.execute(
                """
                INSERT OR IGNORE INTO commits
                (commit_id, commit_flags)
                VALUES (?, 0)
                """,
                (commit_id,),
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO changes
                (change_number, change_patchset, change_commit_id)
                VALUES (?, ?, ?)
                """,
                (number, patchset, commit_id),
            )
            self._dirty = True

    def update_commit(self, commit_id, change_id, picked_from, flags):
        """
        Updates the details of a commit.

        Args:
            commit_id (str): The commit ID (SHA-1).
            change_id (str): The Gerrit Change-Id.
            picked_from (str): The commit ID from which this commit was cherry-picked.
            flags (int): Commit flags.
        """
        with Cursor(self) as cursor:
            cursor.execute(
                """
                UPDATE commits
                SET commit_change_id = ?, commit_picked_from = ?, commit_flags = ?
                WHERE commit_id == ?
                """,
                (change_id, picked_from, flags, commit_id),
            )
            self._dirty = True

    def get_current_patchsets(self, limit=None):
        """
        Retrieves the current patchsets for all changes.

        Args:
            limit (int, optional): The maximum number of patchsets to retrieve.

        Yields:
            dict: A dictionary representing a patchset.
        """
        if self._dirty:
            self._conn.commit()
            self._dirty = False

        if limit is None:
            limit_clause = ""
        else:
            limit_clause = f"LIMIT {limit}"

        with Cursor(self) as cursor:
            cursor.execute(
                f"""
                SELECT
                    ch.change_number AS number,
                    MAX(ch.change_patchset) AS current_patchset,
                    ch.change_commit_id AS commit_id,
                    co.commit_change_id AS change_id,
                    co.commit_picked_from AS cherry_picked_from,
                    co.commit_flags AS flags
                FROM changes AS ch
                LEFT JOIN commits AS co ON co.commit_id = ch.change_commit_id
                GROUP BY ch.change_number
                ORDER BY ch.change_number DESC
                {limit_clause}
                """
            )
            for row in cursor:
                yield self._as_dict(row)

    def get_current_patchset_by_number(self, number):
        """
        Retrieves the current patchset for a given change number.

        Args:
            number (int): The change number.

        Returns:
            dict: A dictionary representing the patchset, or None if not found.
        """
        if self._dirty:
            self._conn.commit()
            self._dirty = False

        with Cursor(self) as cursor:
            cursor.execute(
                """
                SELECT
                    ch.change_number AS number,
                    MAX(ch.change_patchset) AS current_patchset,
                    ch.change_commit_id AS commit_id,
                    co.commit_change_id AS change_id,
                    co.commit_picked_from AS cherry_picked_from,
                    co.commit_flags AS flags
                FROM changes AS ch
                LEFT JOIN commits AS co ON co.commit_id = ch.change_commit_id
                WHERE ch.change_number = ?
                GROUP BY ch.change_number
                ORDER BY ch.change_number DESC
                LIMIT 1
                """,
                (number,),
            )
            row = cursor.fetchone()
            if row:
                return self._as_dict(row)
            return None

    def get_change_by_commit(self, commit_id):
        """
        Retrieves change details by commit ID.

        Args:
            commit_id (str): The commit ID (SHA-1).

        Returns:
            dict: A dictionary representing the change, or None if not found.
        """
        if self._dirty:
            self._conn.commit()
            self._dirty = False

        with Cursor(self) as cursor:
            cursor.execute(
                """
                SELECT
                    ch.change_number AS number,
                    ch.change_patchset AS patchset,
                    ch.change_commit_id AS commit_id,
                    co.commit_change_id AS change_id,
                    co.commit_picked_from AS cherry_picked_from,
                    co.commit_flags AS flags
                FROM changes AS ch
                LEFT JOIN commits AS co ON co.commit_id = ch.change_commit_id
                WHERE ch.change_commit_id = ?
                LIMIT 1
                """,
                (commit_id,),
            )
            # Return the first change that matches the commit hash. It is
            # possible to have more than one, but not common.
            row = cursor.fetchone()
            if row:
                return self._as_dict(row)
            return None

    def get_cherry_picks_by_commit(self, commit_picked_from):
        """
        Retrieves all cherry-picks of a given commit.

        Args:
            commit_picked_from (str): The commit ID of the original commit.

        Yields:
            dict: A dictionary representing a cherry-picked commit.
        """
        if self._dirty:
            self._conn.commit()
            self._dirty = False
        with Cursor(self) as cursor:
            cursor.execute(
                """
                SELECT
                    commit_id,
                    commit_change_id,
                    commit_picked_from,
                    commit_flags
                FROM commits
                WHERE commit_picked_from = ?
                """,
                (commit_picked_from,),
            )
            for row in cursor:
                yield self._as_dict(row)
