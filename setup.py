#!/usr/bin/python
# -*- coding: utf-8 -*-

"""setup.py for graypy"""

import codecs
import re
import sys
import os

from setuptools import setup, find_packages, Command
from setuptools.command.test import test


def find_version(*file_paths):
    with codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *file_paths), 'r') as fp:
        version_file = fp.read()
    m = re.search(r"^__version__ = \((\d+), ?(\d+), ?(\d+)\)", version_file, re.M)
    if m:
        return "{}.{}.{}".format(*m.groups())
    raise RuntimeError("Unable to find a valid version")


VERSION = find_version("graypy", "__init__.py")


class Tag(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from subprocess import call
        version = "v{}".format(VERSION)
        errno = call(['git', 'tag', '--annotate', version,
                      '--message', 'Version {}'.format(version)])
        if errno == 0:
            print("Added tag for version %s" % version)
        sys.exit(errno)


class ReleaseCheck(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from subprocess import check_output
        git_out = check_output(['git', 'describe', '--all',
                                '--exact-match', 'HEAD'])
        tag = git_out.decode("UTF-8").strip().split('/')[-1]
        version = "v{}".format(VERSION)
        if tag != version:
            print('Missing {} tag on release'.format(version))
            sys.exit(1)

        current_branch = check_output(['git', 'rev-parse',
                                       '--abbrev-ref', 'HEAD']).strip()
        if current_branch != 'master':
            print('Only release from master')
            sys.exit(1)

        print("Ok to distribute files")


class Pylint(test):
    def run_tests(self):
        from pylint.lint import Run
        Run(["graypy", "--persistent", "y", "--rcfile", ".pylintrc",
             "--output-format", "colorized"])


class PyTest(test):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        test.initialize_options(self)
        self.pytest_args = "-v --cov={}".format("graypy")

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(
    name='graypy',
    version=VERSION,
    description="Python logging handler that sends messages in Graylog Extended Log Format (GLEF).",
    long_description=open('README.rst').read(),
    keywords='logging gelf graylog2 graylog udp amqp',
    author='Sever Banesiu',
    author_email='banesiu.sever@gmail.com',
    url='https://github.com/severb/graypy',
    license='BSD License',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    tests_require=[
        "pytest",
        "pytest-cov",
        "pylint>=1.9.1,<2.0.0",
        "mock>=2.0.0,<3.0.0",
        "requests>=2.20.1,<3.0.0",
        "amqplib>=1.0.2,<2.0.0"
    ],
    extras_require={'amqp': ['amqplib==1.0.2']},
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: System :: Logging',
    ],
    cmdclass={
        "tag": Tag,
        "release_check": ReleaseCheck,
        "test": PyTest,
        "lint": Pylint
    },
)

