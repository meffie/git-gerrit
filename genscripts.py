# Generate wrapper scripts.

import os
import git_gerrit._help as h

template = """\
#!/usr/bin/env python
import sys
from git_gerrit.{module} import main
try:
    sys.exit(main())
except KeyboardInterrupt:
    sys.stderr.write('Interrupted\\n')
    sys.exit(1)
"""

for name in sorted(dict(h._command_descriptions).keys()):
    module = '_' + name.replace('-', '_')
    script = 'bin/git-gerrit-' + name
    with open(script, 'w') as f:
        f.write(template.format(module=module))
    os.system('chmod +x ' + script)
