try:
    from setuptools import setup
except ImportError:
    # Fallback to standard library distutils.
    from distutils.core import setup

try:
    version = open('version.txt').read().strip()
except IOError:
    version = '0.0.0'

setup(
    name='git_gerrit',
    version=version,
    description='Gerrit review system command line tools.',
    long_description=open('README.rst').read(),
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    license='BSD',
    url='https://github.com/meffie/git_gerrit',
    packages=['git_gerrit'],
    install_requires=[
        'sh',
        'pygerrit2',
    ],
    entry_points = {
        'console_scripts': [
            'git-gerrit-query=git_gerrit.query:main',
            'git-gerrit-fetch=git_gerrit.fetch:main',
            'git-gerrit-log=git_gerrit.log:main',
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
