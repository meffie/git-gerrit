import re

import git_gerrit
import git_gerrit.cli


def test_help(argv, output):
    git_gerrit.cli.git_gerrit_help(argv)
    assert "Commands for gerrit code review" in output[0]


def test_query(argv, output, mock_rest_get):
    argv.append("12345")
    git_gerrit.cli.git_gerrit_query(argv)
    assert len(output) == 1
    assert output[0] == "12345 Transmogrify the frobnicator"


def test_version(argv, output):
    git_gerrit.cli.git_gerrit_version(argv)
    assert len(output) == 1
    assert output[0] == git_gerrit.VERSION
