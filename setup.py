import re

try:
    from setuptools import setup
except ImportError:
    # Fallback to standard library distutils.
    from distutils.core import setup

def get_version():
    with open('git_gerrit/__init__.py') as f:
        for line in f.readlines():
            m = re.match(r'VERSION = "(.*)"', line)
            if m:
                return m.group(1)
    raise AssertionError("Unable to find version string.")

setup(
    name='git_gerrit',
    version=get_version(),
    description='Gerrit review system command line tools.',
    long_description=open('README.rst').read(),
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    license='BSD',
    url='https://github.com/meffie/git-gerrit',
    packages=['git_gerrit'],
    install_requires=[
        'sh',
        'pygerrit2',
    ],
    entry_points = {
        'console_scripts': [
            'git-gerrit-checkout=git_gerrit.cli:git_gerrit_checkout',
            'git-gerrit-cherry-pick=git_gerrit.cli:git_gerrit_cherry_pick',
            'git-gerrit-fetch=git_gerrit.cli:git_gerrit_fetch',
            'git-gerrit-help=git_gerrit.cli:git_gerrit_help',
            'git-gerrit-install-hooks=git_gerrit.cli:git_gerrit_install_hooks',
            'git-gerrit-log=git_gerrit.cli:git_gerrit_log',
            'git-gerrit-query=git_gerrit.cli:git_gerrit_query',
            'git-gerrit-unpicked=git_gerrit.cli:git_gerrit_unpicked',
            'git-gerrit-update=git_gerrit.cli:git_gerrit_update',
            'git-gerrit-version=git_gerrit.cli:git_gerrit_version',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
    ],
)
