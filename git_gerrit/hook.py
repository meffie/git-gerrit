GIT_HOOK = """\
#!/bin/bash
# Change the gerrit change-id in a commit message. To be used when cherry
# picking already merged commits to a different branch.
#
# usage: GERRIT_CHERRY_PICK=yes git cherry-pick -x <commit>
#
test "$GERRIT_CHERRY_PICK" = "yes" || exit 0
grep '^(cherry picked from commit' "$1" >/dev/null || exit 0
grep '^Change-Id:' "$1" >/dev/null || exit 0
echo "prepare-commit-msg: creating new gerrit Change-Id"
sed -i '/^Change-Id:/d' "$1"
.git/hooks/commit-msg "$1"
"""
