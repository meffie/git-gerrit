import pytest
import git_gerrit
import git_gerrit.cli
import sh


class MockCommandBase:
    def __init__(self, *args, **kwargs):
        pass

    def bake(self, *args, **kwargs):
        return self


class MockGitCommand(MockCommandBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if len(args) > 0 and args[0] == "show-ref":
            # Simulate not-found error.
            sh.ErrorReturnCode.exit_code = 1
            raise sh.ErrorReturnCode("git show-ref", b"", b"ref not found")
        return

    def config(self, op, name, *args, **kwargs):
        if op != "--get":
            raise ValueError("Unexpected operation: {0}".format(op))
        if name == "gerrit.project":
            value = "mayhem"
        elif name == "gerrit.host":
            value = "gerrit.example.org"
        else:
            sh.ErrorReturnCode_1.exit_code = 1
            raise sh.ErrorReturnCode_1("git config", b"", b"not found")
        return value

    def log(self, *args, **kwargs):
        return []

    def fetch(self, *args, **kwargs):
        return

    def checkout(self, *args, **kwargs):
        return


class MockSshCommand(MockCommandBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return


@pytest.fixture
def argv():
    argv = []
    return argv


@pytest.fixture
def output(monkeypatch):
    output = []

    def capture(*items, out=None, newline=True):
        message = " ".join([str(item) for item in items])
        output.append(message)

    monkeypatch.setattr(git_gerrit.cli, "writeln", capture)
    monkeypatch.setattr(git_gerrit, "writeln", capture)
    return output


@pytest.fixture
def mock_commands(monkeypatch):

    def make_command(name):
        if name == "git":
            command = MockGitCommand()
        elif name == "ssh":
            command = MockSshCommand()
        else:
            raise ValueError("Unexpected command: {0}".format(name))
        return command

    monkeypatch.setattr(git_gerrit.config.sh, "Command", make_command)
    monkeypatch.setattr(git_gerrit.sh, "Command", make_command)


@pytest.fixture
def mock_rest(monkeypatch, mock_commands):
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
