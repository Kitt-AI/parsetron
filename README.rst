===============================================
Parsetron -  A natural language semantic parser
===============================================

.. pypi version and download:
    .. image:: https://pypip.in/d/parsetron/badge.png
        :target: https://pypi.python.org/pypi/parsetron

.. image:: https://travis-ci.org/Kitt-AI/parsetron.svg?branch=develop
    :target: https://travis-ci.org/Kitt-AI/parsetron

.. image:: https://coveralls.io/repos/Kitt-AI/parsetron/badge.svg?branch=develop
    :target: https://coveralls.io/r/Kitt-AI/parsetron?branch=develop

.. image:: https://readthedocs.org/projects/parsetron/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://readthedocs.org/projects/parsetron/


A natural language semantic parser

Installation
------------

``pip install parsetron``

Parsetron is tested under Python 2.7 and Pypy. It doesn't support Python 3 yet.

Quick Start
-----------

The following is a grammar that parses natural language instruction on lights:

.. code-block:: python

    from parsetron import Set, Regex, Optional, OneOrMore, Grammar, RobustParser

    class LightGrammar(Grammar):

        action = Set(['change', 'flash', 'set', 'blink'])
        light = Set(['top', 'middle', 'bottom'])
        color = Regex(r'(red|yellow|blue|orange|purple|...)')
        times = Set(['once', 'twice', 'three times']) | Regex(r'\d+ times')
        one_parse = action + light + Optional(times) + color
        GOAL = OneOrMore(one_parse)

        @staticmethod
        def test():
            parser = RobustParser((LightGrammar()))
            sents = [
                "set my top light to red",
                "set my top light to red and change middle light to yellow",
                "set my top light to red and change middle light to yellow and "
                "flash bottom light twice in blue"
            ]
            for sent in sents:
                tree, result = parser.parse(sent)
                assert result.one_parse[0].color == 'red'

                print '"%s"' % sent
                print "parse tree:"
                print tree
                print "parse result:"
                print result
                print


Dependencies
------------

None. Parsetron is a single ``parsetron.py`` file.

Parsetron is inspired by `pyparsing <https://pyparsing.wikispaces.com/>`_.

Grammar Modules
---------------

Parsetron supports modularized grammars: each grammar focuses on an individual
small domain and can be imported via, for instance:

.. code-block:: python

    from parsetron.grammars.colors import ColorsGrammar

    class YourCustomizedGrammar(Grammar):
        color = ColorsGrammar.GOAL


You are welcome to contribute your own grammar here (under
``parsetron.grammars``). Send us a pull request!

Development
-----------

1. fork this repository
2. install dev-specific packages::

       pip install -r requirements.txt

3. then make your changes and follow the ``Makefile``.


TODO
----

- [ ] Python 3 compatible
- [ ] Unicode support
