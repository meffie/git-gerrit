import git_gerrit
import git_gerrit.cli


def test_help(argv, output):
    git_gerrit.cli.git_gerrit_help(argv)
    assert len(output) > 1
    assert "Commands for gerrit code review" in output[0]


def test_query(argv, output, mock_rest):
    argv.append("12345")
    git_gerrit.cli.git_gerrit_query(argv)
    assert len(output) == 1
    assert output[0] == "12345 Transmogrify the frobnicator"


def test_version(argv, output):
    git_gerrit.cli.git_gerrit_version(argv)
    assert len(output) == 1
    assert output[0] == git_gerrit.VERSION


def test_checkout(argv, output, mock_rest):
    argv.append("12345")
    git_gerrit.cli.git_gerrit_checkout(argv)


def test_cherry_pick(argv, output, mock_rest):
    argv.append("12345")
    git_gerrit.cli.git_gerrit_cherry_pick(argv)


def test_fetch(argv, output, mock_rest):
    argv.append("12345")
    git_gerrit.cli.git_gerrit_fetch(argv)


def test_install_hook(argv, output, mock_rest):
    git_gerrit.cli.git_gerrit_install_hooks(argv)


def test_log(argv, output, mock_rest):
    git_gerrit.cli.git_gerrit_log(argv)


def test_unpicked(argv, output, mock_rest):
    argv.append("stable")
    git_gerrit.cli.git_gerrit_unpicked(argv)


def test_update(argv, output, mock_rest):
    argv.append("12345")
    argv.append("--message=test")
    git_gerrit.cli.git_gerrit_update(argv)
