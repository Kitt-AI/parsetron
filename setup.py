#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
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

setup(
    name='parsetron',
    version='0.1.0',
    description='A natural language semantic parser',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='KITT.AI',
    author_email='kittdotai@gmail.com',
    url='https://github.com/Kitt-AI/parsetron',
    packages=[
        'parsetron',
    ],
    package_dir={'parsetron': 'parsetron'},
    include_package_data=True,
    install_requires=[
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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
