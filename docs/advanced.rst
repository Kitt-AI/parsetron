.. _parsetron_advanced:

========================
Parsetron Advanced Usage
========================

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

Call-back Functions
===================

In the last section we defined ``color`` and ``times`` as::

        color = Regex(r'(red|yellow|blue|orange|purple|...)')
        times = Set(['once', 'twice', 'three times']) | Regex(r'\d+ times')

A parse result would look something like::

    { 'GOAL': [['blink', 'top', 'red', 'twice']],
      'one_parse': [ {'action': 'blink',
                      'one_parse': ['blink', 'top', 'red', 'twice'],
                      'color': 'red',
                      'light': 'top',
                      'times': 'twice'}]}

But we'd want something more conveniently like::

    { 'GOAL': [['blink', 'top', 'red', 'twice']],
      'one_parse': [ {'action': 'blink',
                      'one_parse': ['blink', 'top', 'red', 'twice'],
                      'color': [255, 0, 0],
                      'light': 'top',
                      'times': 2}]}

This can be achieved by the :func:`parsetron.GrammarElement.set_result_action`
call back function, for instance::

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

    color = Regex(r'(red|yellow|blue|orange|purple|...)').set_result_action(color2rgb)

The ``color2rgb`` function now first retrieves the lexicon of color by calling
``result.get()`` (:func:`parsetron.ParseResult.get`), then map it to a RGB
tuple, and finally replacing the result with ``result.set()``
(:func:`parsetron.ParseResult.set`).

.. note::

    The return value of :func:`parsetron.GrammarElement.set_result_action`
    is the object itself (``return self``). Thus in the above example
    ``color`` is still assigned with the ``Regex()`` object.

The ``times`` part is only slightly more complicated as it parses numbers
in both digits and words. We define two functions here::

    def regex2int(result):
        # result holds Regex(r'\d+ times') lexicon
        num = int(result.get().split()[0])
        result.set(num)

    def times2int(result):
        r = result.get().lower()
        mapper = {"once": 1, "twice": 2, "three times": 3}
        num = mapper[r]
        result.set(num)

    times = Set(['once', 'twice', 'three times']).set_result_action(times2int) | \
        Regex(r'\d+ times').set_result_action(regex2int)

Here each grammar element (``Set()`` and ``Regex()``) has their own call-back
functions. Together they define the ``times`` variable. The result is that
the ``times`` field in parse result is all converted into an integer number,
no matter whether it's `twice` or `20 times`.

Next we test whether these call-back functions work as expected!

Test Your Grammar
=================

The :class:`parsetron.Grammar` class defines a static
:func:`parsetron.Grammar.test` function for testing your grammar. This function
is also called by parsetron's `pytest <https://pytest.org/>`_  routine for
both bug spotting and test coverage report. One should freely and fully make
use of the ``assert`` function in ``test()`` after defining a grammar.

The following is the full grammar with a simple test function::

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

Here we make sure that the first ``one_parse`` structure has its color as the
RGB value of red (``result.one_parse[0].color == (255, 0, 0)``) and its times
parameter as an integer (``result.one_parse[0].times == 2``). So as the second
``one_parse`` structure.

Corresponding code of this tutorial is hosted on
`Github <https://github.com/Kitt-AI/parsetron-tutorial>`_.

.. note::

    **When is the call-back function called?**

    The call-back function is called when we convert the (usually best) parse
    tree  (:class:`parsetron.TreeNode`) to parse result
    (:class:`parsetron.ParseResult`). It is literally a post-processing
    function *after* parsing. We cannot call it *during* parsing as a CFG
    grammar can potentially output many trees while each of these trees might
    output a different parse result.


Modularized Grammars
====================

So far we have seen how to convert both colors and numbers into more computer
friendly values. However the example code above is too simple to be used in
real world. As a matter of fact, both color and number parsing deserve their
own grammar. Thus we introduce the notion of **modularized grammar**: each
grammar class defines a minimal but fully functional CFG with desired call-back
functions; these grammar classes are shared towards bigger and more complex
grammars.

We have provided a few examples in the
`parsetron/grammars <https://github.com/Kitt-AI/parsetron/tree/master/parsetron/grammars>`_
folder. For instance, the :class:`parsetron.grammars.NumbersGrammar` in
`numbers.py <https://github.com/Kitt-AI/parsetron/blob/develop/parsetron/grammars/numbers.py>`_
parses not only *one/two/three* but even *1 hundred thousand five hundred 61*
(100561). The :class:`parsetron.grammars.ColorsGrammar` in
`colors.py <https://github.com/Kitt-AI/parsetron/blob/develop/parsetron/grammars/colors.py>`_
defined over 100 different kinds of colors. All of these definition can be
accessed via their ``Grammar.GOAL`` variable. Then in our lights grammar, we
can simply do::

    from parsetron.grammars.times import TimesGrammar
    from parsetron.grammars.colors import ColorsGrammar

    class ColoredLightGrammar(Grammar):

        color = ColorsGrammar.GOAL
        times = TimesGrammar.GOAL
        ...

In the future we will be adding more grammars as we find useful. If you'd like
to contribute your own grammar, send us a pull request! And don't forget to
test your grammar (by implementing :func:`parsetron.Grammar.test`)!
