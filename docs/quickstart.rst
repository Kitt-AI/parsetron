.. _parsetron_quickstart:

=====================
Parsetron Quick Start
=====================

.. Bootstrap specific class labels

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


Installation
============

Parsetron is available through PyPI::

    pip install parsetron

(if you don't have ``pip``, follow
`these instructions <https://pip.pypa.io/en/latest/installing.html>`_
to install it)

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

Simple Example
==============

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
                "set my top light to red and change middle light to yellow and flash bottom light twice in blue"
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

output:

.. code-block:: python

    "set my top light to red"
    parse tree:
    (GOAL
      (one_parse
        (action "set")
        (light "top")
        (color "red")
      )
    )

    parse result:
    {
      "one_parse": [
        {
          "action": "set",
          "one_parse": [
            "set",
            "top",
            "red"
          ],
          "color": "red",
          "light": "top"
        }
      ],
      "GOAL": [
        [
          "set",
          "top",
          "red"
        ]
      ]
    }

    "set my top light to red and change middle light to yellow"
    parse tree:
    (GOAL
      (one_parse
        (action "set")
        (light "top")
        (color "red")
      )
      (one_parse
        (action "change")
        (light "middle")
        (color "yellow")
      )
    )

    parse result:
    {
      "one_parse": [
        {
          "action": "set",
          "one_parse": [
            "set",
            "top",
            "red"
          ],
          "color": "red",
          "light": "top"
        },
        {
          "action": "change",
          "one_parse": [
            "change",
            "middle",
            "yellow"
          ],
          "color": "yellow",
          "light": "middle"
        }
      ],
      "GOAL": [
        [
          "set",
          "top",
          "red"
        ],
        [
          "change",
          "middle",
          "yellow"
        ]
      ]
    }

    "set my top light to red and change middle light to yellow and flash bottom light twice in blue"
    parse tree:
    (GOAL
      (one_parse
        (action "set")
        (light "top")
        (color "red")
      )
      (one_parse
        (action "change")
        (light "middle")
        (color "yellow")
      )
      (one_parse
        (action "flash")
        (light "bottom")
        (Optional(times)
          (times
            (Set(three times|twice|once) "twice")
          )
        )
        (color "blue")
      )
    )

    parse result:
    {
      "one_parse": [
        {
          "action": "set",
          "one_parse": [
            "set",
            "top",
            "red"
          ],
          "color": "red",
          "light": "top"
        },
        {
          "action": "change",
          "one_parse": [
            "change",
            "middle",
            "yellow"
          ],
          "color": "yellow",
          "light": "middle"
        },
        {
          "one_parse": [
            "flash",
            "bottom",
            "twice",
            "blue"
          ],
          "color": "blue",
          "Set(three times|twice|once)": "twice",
          "Optional(times)": "twice",
          "times": "twice",
          "light": "bottom",
          "action": "flash"
        }
      ],
      "GOAL": [
        [
          "set",
          "top",
          "red"
        ],
        [
          "change",
          "middle",
          "yellow"
        ],
        [
          "flash",
          "bottom",
          "twice",
          "blue"
        ]
      ]
    }


Complex Example
===============

.. code-block:: python

    from parsetron import Set, Regex, Optional, OneOrMore, Grammar, RobustParser


    def regex2int(result):
        # result holds Regex(r'\d+ times') lexicon
        num = int(result.get().split()[0])
        result.set(num)


    def times2int(result):
        r = result.get().lower()
        mapper = {"once": 1, "twice": 2, "three times": 3}
        num = mapper[r]
        result.set(num)


    def color2rgb(result):
        r = result.get().lower()
        # r now holds color lexicons
        mapper = {
            "red": (255, 0, 0),
            "yellow": (255, 255, 0),
            "blue": (0, 0, 255),
            "orange": (255, 165, 0),
            "purple": (128, 0, 128)
        }
        color = mapper[r]
        result.set(color)


    class LightAdvancedGrammar(Grammar):

        action = Set(['change', 'flash', 'set', 'blink'])
        light = Set(['top', 'middle', 'bottom'])

        color = Regex(r'(red|yellow|blue|orange|purple|...)').\
            set_result_action(color2rgb)
        times = Set(['once', 'twice', 'three times']).\
            set_result_action(times2int) | \
            Regex(r'\d+ times').set_result_action(regex2int)

        one_parse = action + light + Optional(times) + color
        GOAL = OneOrMore(one_parse)

        @staticmethod
        def test():
            parser = RobustParser((LightAdvancedGrammar()))
            tree, result = parser.parse("flash my top light twice in red and "
                                        "blink middle light 20 times in yellow")
            print tree
            print result
            assert result.one_parse[0].color == (255, 0, 0)
            assert result.one_parse[0].times == 2
            assert result.one_parse[1].color == (255, 255, 0)
            assert result.one_parse[1].times == 20
            print

output:

.. code-block:: python

    (GOAL
      (one_parse
        (action "flash")
        (light "top")
        (Optional(times)
          (times
            (Set(three times|twice|once) "twice")
          )
        )
        (color "red")
      )
      (one_parse
        (action "blink")
        (light "middle")
        (Optional(times)
          (times
            (Regex(^\d+ times$) "20 times")
          )
        )
        (color "yellow")
      )
    )

    {
      "one_parse": [
        {
          "one_parse": [
            "flash",
            "top",
            2,
            [
              255,
              0,
              0
            ]
          ],
          "color": [
            255,
            0,
            0
          ],
          "Set(three times|twice|once)": 2,
          "Optional(times)": 2,
          "times": 2,
          "light": "top",
          "action": "flash"
        },
        {
          "one_parse": [
            "blink",
            "middle",
            20,
            [
              255,
              255,
              0
            ]
          ],
          "Regex(^\\d+ times$)": 20,
          "color": [
            255,
            255,
            0
          ],
          "light": "middle",
          "Optional(times)": 20,
          "times": 20,
          "action": "blink"
        }
      ],
      "GOAL": [
        [
          "flash",
          "top",
          2,
          [
            255,
            0,
            0
          ]
        ],
        [
          "blink",
          "middle",
          20,
          [
            255,
            255,
            0
          ]
        ]
      ]
    }


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

