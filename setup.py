try:
    from setuptools import setup
except ImportError:
    # Fallback to standard library distutils.
    from distutils.core import setup

exec(open('git_gerrit/_version.py').read())

setup(
    name='git_gerrit',
    version=__version__,
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
    scripts = [
        'bin/git-gerrit-query',
        'bin/git-gerrit-fetch',
        'bin/git-gerrit-log',
        'bin/git-gerrit-unpicked',
    ],
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
