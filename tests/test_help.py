from git_gerrit.cli import git_gerrit_help


def test_help():
    argv = []  # do not use sys.argv
    git_gerrit_help(argv)
