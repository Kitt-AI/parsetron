#!/usr/bin/env python

import os
import sys
from parsetron import parsetron

try:
    from setuptools import setup
    from setuptools.command.test import test as TestCommand
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://parsetron.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='parsetron',
    version=parsetron.__version__,
    description='A natural language semantic parser',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='KITT.AI',
    author_email='kittdotai@gmail.com',
    url='https://github.com/Kitt-AI/parsetron',
    packages=[
        'parsetron',
        'parsetron.grammars',
    ],
    package_dir={'parsetron': 'parsetron'},
    include_package_data=True,
    install_requires=[
    ],
    setup_requires=[
        "flake8"
    ],
    license='Apache',
    zip_safe=False,
    keywords='parsetron',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
