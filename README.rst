===============================================
Parsetron -  A natural language semantic parser
===============================================

.. image:: https://badge.fury.io/py/parsetron.png
    :target: http://badge.fury.io/py/parsetron

.. image:: https://travis-ci.org/Kitt-AI/parsetron.png?branch=master
    :target: https://travis-ci.org/Kitt-AI/parsetron

.. image:: https://pypip.in/d/parsetron/badge.png
    :target: https://pypi.python.org/pypi/parsetron

.. image:: https://readthedocs.org/projects/parsetron/badge/
    :alt: Documentation Status
    :scale: 100%
    :target: https://readthedocs.org/projects/parsetron/


A natural language semantic parser

Installation
------------

``pip install parsetron``

Parsetron is tested under Python 2.7 and Pypy. It doesn't support Python 3 yet.

Dependencies
------------

None. Parsetron is a single ``parsetron.py`` file.

Grammar Modules
---------------

Parsetron supports modularized grammars: each grammar focuses on an individual
small domain and can be imported via, for instance::

    from parsetron.grammars.colors import ColorsGrammar

    class YourCustomizedGrammar(Grammar):
        color = ColorsGrammar.GOAL


You are welcome to contribute your own grammar here. Send us a pull request!

Development
-----------

1. fork this repository
2. install dev-specific packages::

       pip install -r requirements.txt

3. then make your changes and follow the ``Makefile``.


Features
--------


TODO
----

[ ] Python 3 compatible
[ ] Unicode support
