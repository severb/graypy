#!/usr/bin/python
# -*- coding: utf-8 -*-

"""setup.py for graypy"""

import codecs
import re
import sys
import os

from setuptools import setup, find_packages
from setuptools.command.test import test


def find_version(*file_paths):
    with codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *file_paths), 'r') as fp:
        version_file = fp.read()
    m = re.search(r"^__version__ = \((\d+), ?(\d+), ?(\d+)\)", version_file, re.M)
    if m:
        return "{}.{}.{}".format(*m.groups())
    raise RuntimeError("Unable to find a valid version")


VERSION = find_version("graypy", "__init__.py")


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
    description="Python logging handler that sends messages in GELF (Graylog Extended Log Format).",
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
        "requests>=2.20.1,<3.0.0"
    ],
    extras_require={'amqp': ['amqplib==1.0.2']},
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],
    cmdclass={"test": PyTest, "lint": Pylint},
)
