.. _parsetron_index:

.. Parsetron documentation master file, created by
   sphinx-quickstart on Mon Apr 13 12:36:49 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. role:: text-success
.. role:: text-primary
.. role:: text-info
.. role:: text-warning
.. role:: text-danger

.. role:: bg-success
.. role:: bg-primary
.. role:: bg-info
.. role:: bg-warning
.. role:: bg-danger


***********************************
Parsetron, a Robust Semantic Parser
***********************************

.. topic:: Abstract

   Parsetron is a robust incremental natural language parser utilizing semantic
   grammars for small focused domains. It is mainly used to convert natural
   language command to executable API calls (e.g.,
   *"set my bedroom light to red"* --> ``set_light('bedroom', [255, 0, 0])``).
   Parsetron is written in pure Python (2.7), portable (a single
   ``parsetron.py`` file), and can be used in conjunction with a speech
   recognizer.

:Author: Xuchen Yao from `KITT.AI <http://kitt.ai>`_


.. rubric:: Table of Contents

.. toctree::
   :maxdepth: 3

   self
   tutorial
   advanced
   api


What It is
==========

Parsetron is a semantic parser that converts natural language text into API calls.
Typical usage scenarios include for instance:

* control your smart light with language, e.g.:

  - :text-success:`give me something romantic`
  - :text-success:`my living room light is too dark`
  - :text-success:`change bedroom light to sky blue`
  - :text-success:`blink living room light twice in red color`

* control your microwave with language, e.g.:

  - :text-success:`defrost this chicken please, the weight is 4 pounds`
  - :text-success:`heat up the pizza for 2 minutes 20 seconds`
  - :text-success:`warm up the milk for 1 minute`

The difficult job here is to extract key information from the natural language
command to help developers call certain APIs to control a smart device.
Conventional approach is writing a bunch of rules, such as regular expressions,
which are difficult to maintain, read, and expand. Computational linguists opt
for writing `Context Free Grammars <https://en.wikipedia.org/wiki/Context-free_grammar>`_.
But the learning curve is high and the parser output -- usually a constituency tree
or a dependency relation -- is not directly helpful in our tasks.

Parsetron is designed to tackle these challenges.  Its design philosophy
is to **make natural language understanding easy** for developers with no background
in computational linguistics, or natural language processing (NLP).

Parsetron has the following properties:

* **easy to use**: grammar definition is in Python; thus developers do not have to
  learn another format (traditionally grammars are usually defined in BNF format).
* **robust**: it omits unknown (not defined in grammar) word when parsing; it also
  parses multi-token phrases (modern NLP parsers are only single-token based).
* **incremental**: it emits parse result as soon as it's available; this helps in
  applications requiring quick responding time, such as through speech interaction.
* **flexible**: users can define their own pre-parsing tokenization and post-parsing
  callback functions in their grammar specification; this assigns developers as much
  power as Python has.


It understands language per definition of a semantic grammar.

How it works
============

Parsetron is a
`Chart Parser <https://en.wikipedia.org/wiki/Chart_parser>`_ for
`Context Free Grammars <https://en.wikipedia.org/wiki/Context-free_grammar>`_
(CFGs).
It works in the following way:

1. Accept a grammar extended from :class:`parsetron.Grammar`, which must have a
   ``GOAL`` defined (similar to the start symbol ``S`` in CFGs). The grammar
   is defined in Python (so :text-warning:`no extra learning curve for
   Python developers`!).
2. Tokenize an input string by white spaces.
3. Construct a :class:`parsetron.Chart` and parse with a default Left Corner
   Top Down strategy.

   * unknown words not defined in the grammar are automatically omitted.
   * if single tokens are not recognized, parsetron also tries to recognize
     phrases.

4. Output a conventional linguistic tree, and a :class:`parsetron.ParseResult`
   for easier interpretation.

   * results are ranked by the minimal tree sizes.
   * in the future parsetron will provide probabilistic ranking.

5. Run post processing on the parse result if any call-back functions are
   defined via the :func:`parsetron.GrammarElement.set_result_action` function
   in the grammar.

Parsetron is inspired by `pyparsing <https://pyparsing.wikispaces.com/>`_,
providing a lot of classes with the same intuitive names. pyparsing implements
a top-down recursive parsing algorithm, which is good for parsing unambiguous
input, but not for natural languages. Parsetron is specifically designed for
parsing natural language instructions.


Installation
============

Parsetron is available through PyPI::

    pip install parsetron

Alternatively, Parsetron comes as a single ``parsetron.py`` file.
Just download it from the
`repository <https://github.com/Kitt-AI/parsetron>`_ and put the file under
your ``PYTHONPATH`` or current directory so that you can do::

    import parsetron

or::

    from parsetron import *

Parsetron can be run with either CPython 2.7 or `PyPy <http://pypy.org>`_.
If PyPy is warmed up, the parsing speed is about 3x that of CPython.
At the current stage Parsetron doesn't support Python 3 yet.


.. Adding disqus and google analytics:
    For sample syntax, refer to:
    http://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html
    https://pythonhosted.org/an_example_pypi_project/sphinx.html
    https://docs.python.org/devguide/documenting.html
    https://raw.githubusercontent.com/rtfd/readthedocs.org/master/docs/index.rst
    http://docs.readthedocs.org/en/latest/index.html
    https://github.com/whiteinge/eseth/blob/master/templates/layout.html#L151


.. Indices and tables
    ==================
    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`

