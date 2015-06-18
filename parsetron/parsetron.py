from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import re
import sys
import itertools
import json
import logging
import copy
from collections import deque
from collections import Counter

__doc__ = \
    """
    **parsetron.py**, a semantic parser written in pure Python.
    """

__title__ = 'parsetron'
__version__ = "0.1.0"
__author__ = 'Xuchen Yao'
__license__ = 'Apache 2.0'


PY_3 = sys.version.startswith('3')
if PY_3:
    _ustr = str
else:
    def _ustr(obj):
        """
        Drop-in replacement for str(obj) that tries to be Unicode friendly.
        It first tries str(obj). If that fails with a UnicodeEncodeError, then
        it tries unicode(obj). It then < returns the unicode object | encodes
        it with the default encoding | ... >.
        """
        if isinstance(obj, unicode):
            return obj
        try:
            # If this works, then _ustr() has the same behaviour as str(),
            # so it won't break any existing code.
            return str(obj)

        except UnicodeEncodeError:
            return unicode(obj)

# ####################################
# ############ User Space ############
# ####################################

# ##### Exception ######


class ParseException(Exception):
    """Exception thrown when we can't parse the whole string.
    """
    pass


class GrammarException(Exception):
    """ Exception thrown when we can't construct the grammar."""
    pass


# ##### Semantic Grammar ######


class MetaGrammar(type):
    """
    A meta grammar used to extract symbol names (expressed as variables)
    during grammar *construction* time. This provides a cleaner way than
    using obj.__class__.__dict__, whose __dict__ has to be accessed via
    an extra and explicit function call.
    """

    def __new__(typ, name, bases, dct):
        if '__metaclass__' not in dct:
            # If user does::
            # >>> from parsetron import *
            # Then __new__() will be called with __metaclass__ in dct
            # If user constructs a real grammar, then __metaclass__ isn't
            # in dct
            if "_grammar_" in dct:
                raise GrammarException("_grammar_ is reserved.")
            if "GOAL" not in dct:
                raise GrammarException("you must define your GOAL in grammar")
            else:
                dct["_grammar_"] = GrammarImpl(name, dct)
        return super(MetaGrammar, typ).__new__(typ, name, bases, dct)


class Grammar(object):
    """
    Grammar user interface. Users should inherit this grammar and define a
    final grammar GOAL as class variable.

    It's a wrapper around :class:`GrammarImpl` but does not expose any internal
    functions. So users can freely define their grammar without worrying about
    name pollution. However, when a :class:`Grammar` is constructed, a
    :class:`GrammarImpl` is *actually* returned::

        >>> g = Grammar()

    now `g` is the real grammar (:class:`GrammarImpl`)


    .. warning:: Grammar elements have to be defined as class variables
        instead of instance variables for the :class:`Grammar` object to
        extract variable names in string

    .. warning:: Users have to define a `GOAL` variable in :class:`Grammar`
        (similar to start variable *S* conventionally used in grammar
        definition)
    """
    __metaclass__ = MetaGrammar

    def __new__(cls):
        return cls.__dict__['_grammar_']

    @staticmethod
    def test():
        """
        A method to be batch called by pytest (through ``test_grammars.py``).
        Users should give examples of what this Grammar parses and use these
        examples for testing.
        """
        raise NotImplementedError

# ##### Unary Grammar Elements ######


class GrammarElement(object):
    """
    Basic grammar symbols (terminal or non-terminal).

    Developers inheriting this class should implement the following functions:

    * :func:`_parse`
    * :func:`default_name`

    A grammar element carries the following attributes:

    - `is_terminal`:  whether this element is terminal or non-terminal. A
      general rule of thumb is:

        * if it's :class:`GrammarElement`,  then terminal;
        * if it's :class:`GrammarExpression`, then non-terminal;
        * if it's :class:`GrammarElementEnhance`, then non-terminal.
    - `name`: the name of this element, usually set by the the
      :func:`set_name()` function or implicitly __call__() function.
    - `variable_name`: automatically extracted variable name in string
      through the :class:`Grammar` construction.
    - `canonical_name`: if neither `name` nor `variable_name` is set, then
      a canonical name is assigned trying to be as expressive as possible.
    - `as_list`: whether saves result in a hierarchy as a list, or just flat
    - `ignore`: whether to be ignored in ParseResult

    """

    def __init__(self):
        self.name = None
        self.variable_name = None
        self.canonical_name = None
        self.str = None
        self.streamlined = False
        self.post_funcs = []
        self.is_terminal = True
        self.as_list = False
        self.ignore_in_result = False
        self.name_is_set = False

    def set_name(self, name):
        """
        Set the name of a grammar symbol. Usually the name of a
        :class:`GrammarElement` is set by its variable name, for instance::

            >>> light = String("light")

        but in on-the-fly construction, one can call :func:`set_name`::

            >>> Optional(light).set_name("optional_light")

        or shorten it to a function call like name setting::

            >>> Optional(light)("optional_light")

        The function returns a new shallow copied :class:`GrammarElement`
        object. This allows reuse of common grammar elements in complex
        grammars without name collision.

        :param str name: name of this grammar symbol
        :return: a self copy (with different id and hash)
        :rtype: :class:`GrammarElement`
        """
        newself = copy.copy(self)
        newself.name = name
        newself.post_funcs = self.post_funcs[:]
        return newself

    def default_name(self):
        """
        default canonical name.

        :return: a string
        :rtype: str
        """
        raise NotImplementedError

    def prefix_with_class(self, default_name):
        return self.__class__.__name__ + "(" + str(default_name) + ")"

    def set_result_action(self, *functions):
        """
        Set functions to call after parsing. For instance::

            >>> number = Regex(r"\d+").set_result_action(lambda x: int(x))

        It can be a list of functions too:

            >>> def f1(): pass  # do something
            >>> def f2(): pass  # do something
            >>> number = Regex(r"\d+").set_result_action(f1, f2)

        :param functions: a list of functions
        :return: self
        """
        self.post_funcs = list(functions)
        return self

    def replace_result_with(self, value):
        """
        replace the result lexicon with ``value``. This is a shortcut to::

            self.set_result_action(lambda r: r.set(value))

        :param value: any object
        :return: self
        """
        return self.set_result_action(lambda r: r.set(value))

    def _check_type(self, other):
        if isinstance(other, basestring):
            return String(other)
        elif not isinstance(other, GrammarElement):
            raise GrammarException("can't construct grammar: %s + %s"
                                   % (self, str(other)))
        else:
            return other

    def __add__(self, other):
        """
        Implement the + operator. Returns :class:`And`.
        """
        other = self._check_type(other)
        return And([self, other])

    def __radd__(self, other):
        """
        Implement the + operator. Returns :class:`And`.
        """
        other = self._check_type(other)
        return other + self

    def __mul__(self, other):
        """

        Implements the * operator, followed by an integer or a tuple/list:

            - ``e * m``: ``m`` repetitions of ``e`` (``m > 0``)
            - ``e * (m, n)`` or ``e * [m, n]``: ``m`` to ``n`` repetitions
              of ``e`` (all inclusive)
            - ``m`` or ``n`` in ``(m,n)/[m,n]`` can be None

        for instance (=> stands for "is equivalent to"):

            - ``e * (m, None)`` or ``e * (m,)`` => ``m`` or more instances of
              ``e`` => ``e * m +`` :class:`ZeroOrMore` ``(e)``
            - ``e * (None, n)`` or ``e * (0, n)`` => ``0`` to ``n`` instances
              of ``e``
            - ``e * (None, None)`` => :class:`ZeroOrMore` ``(e)``
            - ``e * (1, None)`` => :class:`OneOrMore` ``(e)``
            - ``e * (None, 1)`` => :class:`Optional` ``(e)``

        """
        if isinstance(other, int):
            if other == 1:
                return self
            elif other > 1:
                return And([self] * other)
            else:
                raise ValueError("can't multiply with: %s" % str(other))
        elif isinstance(other, (tuple, list)):
            if len(other) == 1:
                m, n = other[0], None
            elif len(other) == 2:
                m, n = other
            else:
                raise ValueError("can't multiply with: %s" % str(other))
            if m is None:
                m = 0
            if type(m) is not int:
                raise ValueError("can't multiply with: %s" % str(other))
            if m < 0:
                raise ValueError("can't multiply with: %s" % str(other))
            if n is None:
                if m == 0:
                    return ZeroOrMore(self)
                elif m == 1:
                    return OneOrMore(self)
                else:
                    return self * m + ZeroOrMore(self)
            elif isinstance(n, int) and n >= m:
                if m == 0 and n == 1:
                    return Optional(self)
                elif m == n:
                    return And([self] * m)
                else:
                    return And([self]*m + [Optional(self)]*(n-m))
            else:
                raise ValueError("can't multiply with: %s" % str(other))
        else:
            raise ValueError("can't multiply with: %s" % str(other))

    def __or__(self, other):
        """Implement the | operator. Returns :class:`Or`."""
        other = self._check_type(other)
        return Or([self, other])

    def __ror__(self, other):
        """Implement the | operator. Returns :class:`Or`."""
        other = self._check_type(other)
        return other | self

    def __call__(self, name):
        """
        Shortcut for :func:`set_name`
        """
        return self.set_name(name)

    def __str__(self):
        if self.name:
            return self.name
        elif self.variable_name:
            return self.variable_name
        elif self.canonical_name:
            return self.canonical_name
        else:
            self.canonical_name = self.prefix_with_class(self.default_name())
            return self.canonical_name

    def __repr__(self):
        return _ustr(self)

    def __eq__(self, other):
        if isinstance(other, GrammarElement):
            return self is other or self.__dict__ == other.__dict__
        elif isinstance(other, basestring):
            try:
                self.parse(_ustr(other))
                return True
            except ParseException:
                return False
        else:
            return super(GrammarElement, self) == other

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(id(self))

    def _parse(self, instring):
        """
        Main parsing method to be implemented by developers.
        Raises ParseException when there is no parse.

        :param str instring:  input string to be parsed
        :return: True if full parse else False
        :rtype: bool
        :raises: :class:`ParseException`
        """
        raise NotImplementedError

    def parse(self, instring):
        """
        Main parsing method to be called by users. Raises ParseException
        when there is no parse. Returns True if the whole string is parsed
        and False if input string is not parsed but no exception is thrown
        either (e.g., parsing with Null element)

        :param str instring: input string
        :return bool: True if the whole string is parsed else False
        """
        if not self.streamlined:
            self.streamline()
        try:
            return self._parse(instring)
        except ParseException as e:
            raise e

    def streamline(self):
        self.streamlined = True
        return self

    def ignore(self):
        """
        Call this function to make this grammar element not appear in parse
        result.
        :return: self
        """
        self.ignore_in_result = True
        return self

    def yield_productions(self):
        """
        Yield how this element/expression produces grammar productions
        """
        yield Production.factory(self)

    def production(self):
        """
        converts this GrammarElement (used by User) to a GrammarProduction
        (used by Parser)
        """
        return Production.factory(self)

    def run_post_funcs(self, result):
        """
        Run functions set by :func:`set_result_action` after getting parsing
        result.

        :param ParseResult result: parsing result
        :return: None
        """
        for f in self.post_funcs:
            if f:
                f(result)


class StringCs(GrammarElement):
    """
    Case-sensitive string (usually a terminal) symbol that can be a
    word or phrase.
    """

    def __init__(self, string):
        super(StringCs, self).__init__()
        if string is None or len(string) == 0:
            raise ValueError("Regex doesn't accept empty pattern")
        self.pattern = string
        self.str = self.pattern

    def _parse(self, instring):
        if self.pattern == instring:
            return True
        else:
            raise ParseException

    def default_name(self):
        return self.str


class String(StringCs):
    """
    Case-insensitive version of :class:`StringCs`.
    """
    def __init__(self, string):
        super(String, self).__init__(string.lower())

    def _parse(self, instring):
        return super(String, self)._parse(instring.lower())


class SetCs(GrammarElement):
    """
    Case-sensitive strings in which matching any will lead to parsing
    success. This is a short cut for disjunction of :class:`StringCs` s (\|),
    or :class:`Regex` (``r'(a\|b\|c\|...)'``).

    Input can be one of the following forms:

    - a string with elements separated by spaces (defined by regex ``r"\s+"``)
    - otherwise an iterable

    For instance, the following input is equivalent::

        >>> "aa bb cc"
        >>> ["aa", "bb", "cc"]
        >>> ("aa", "bb", "cc")
        >>> {"aa", "bb", "cc"}

    The following is also equivalent::

        >>> "0123...9"
        >>> "0 1 2 3 .. 9"
        >>> ["0", "1", "2", "3", ..., "9"]
        >>> ("0", "1", "2", "3", ..., "9")
        >>> {"0", "1", "2", "3", ..., "9"}

    """

    def __init__(self, strings, caseless=False):
        super(SetCs, self).__init__()
        try:
            iter(strings)
        except:
            raise ValueError("input must be iterable: " + str(strings))
        if isinstance(strings, basestring):
            strings = re.split("\s+", strings)
            if len(strings) == 1:
                strings = strings[0]
        if caseless:
            self._set = set(s.lower() for s in strings)
        else:
            self._set = set(s for s in strings)
        self.caseless = caseless
        self.str = "|".join(self._set)

    def _parse(self, instring):
        if self.caseless:
            instring = instring.lower()
        if instring in self._set:
            return True
        else:
            raise ParseException

    def default_name(self):
        return self.str


class Set(SetCs):
    """
    Case-insensitive version of :class:`SetCs`.
    """
    def __init__(self, strings):
        super(Set, self).__init__(strings, caseless=True)


class RegexCs(GrammarElement):
    """
    Case-sensitive string matching with regular expressions. e.g.::

        >>> color = RegexCs(r"(red|blue|orange)")
        >>> digits = RegexCs(r"\d+")

    Or pass a compile regex::

        >>> import re
        >>> color = RegexCs(re.compile(r"(red|blue|orange|a long list)"))

    :param int flags: standard :mod:`re` flags
    :param bool match_whole: whether matching the whole string (default: True).

    .. warning:: if ``match_whole=False``, then ``r"(week|weeks)"`` will throw
        a :class:`ParseException` when parsing "weeks", but ``r"(weeks|week)"``
        will succeed to parse "weeks"
    """
    RegexType = type(re.compile(''))

    def __init__(self, pattern, flags=0, match_whole=True):
        super(RegexCs, self).__init__()
        self.flags = flags
        self.match_whole = match_whole
        if isinstance(pattern, basestring):
            if len(pattern) == 0:
                raise ValueError("Regex doesn't accept empty pattern")
            if match_whole:
                self.pattern = "^" + pattern + "$"
            else:
                self.pattern = pattern
            self.re = re.compile(self.pattern, self.flags)
        elif isinstance(pattern, RegexCs.RegexType):
            self.re = pattern
            self.pattern = pattern.pattern
        else:
            raise ValueError("Regex only accept string or compiled re \
                             as pattern")
        self.str = self.pattern

    def _parse(self, instring):
        result = self.re.match(instring)
        if not result:
            raise ParseException
        else:
            # commented out: blocked by ^ + ... + $ patterns above
            # if self.match_whole and result.end() != len(instring):
            #     # partial match
            #     raise ParseException
            # else:
            return True

    def default_name(self):
        return self.str


class Regex(RegexCs):
    """
    Case-insensitive version of :class:`RegexCs`.
    """
    def __init__(self, pattern, flags=re.IGNORECASE, match_whole=True):
        super(Regex, self).__init__(pattern, flags, match_whole)

# ##### Binary Grammar Elements ######


class GrammarExpression(GrammarElement):
    """
    An expression usually involving a binary combination of
    two :class:`GrammarElement`'s. The resulting GrammarExpression is a
    non-terminal and does not implement the parsing function :func:`_parse`.
    """

    def __init__(self, exprs):
        super(GrammarExpression, self).__init__()

        self.is_terminal = False
        if isinstance(exprs, basestring):
            self.exprs = [String(exprs)]
        elif isinstance(exprs, (list, tuple)):
            # if sequence of strings provided, wrap with String
            if all(isinstance(expr, basestring) for expr in exprs):
                exprs = list(map(String, exprs))
            self.exprs = exprs
        else:
            try:
                self.exprs = list(exprs)
            except:
                raise GrammarException("Can't construct grammar:" +
                                       str(exprs))
        self.str = ", ".join([_ustr(e) for e in self.exprs])

    def default_name(self):
        return self.str

    def __getitem__(self, i):
        return self.exprs[i]

    def _parse(self, instring):
        # grammar should take care of this
        raise GrammarException("GrammarExpression shouldn't implement" +
                               "the _parse() function (or: this function" +
                               "shouldn't be called).")

    def append(self, other):
        self.exprs.append(other)
        self.str = None
        return self

    def streamline(self):
        super(GrammarExpression, self).streamline()

        for e in self.exprs:
            e.streamline()

        # collapse nested And's of the form And(And(And(a,b), c), d) to
        # And(a,b,c,d), but only if there are no parse actions on the
        # nested And's (likewise for Or)
        if len(self.exprs) == 2:
            other = self.exprs[0]
            if (isinstance(other, self.__class__) and not other.post_funcs and
               other.name is None and other.variable_name is None):
                self.exprs = other.exprs[:] + [self.exprs[1]]
                self.str = None

            other = self.exprs[-1]
            if (isinstance(other, self.__class__) and not other.post_funcs and
               other.name is None and other.variable_name is None):
                self.exprs = self.exprs[:-1] + other.exprs[:]
                self.str = None

        self.str = "%s (%s)" % (self.__class__.__name__,
                                ", ".join([_ustr(e) for e in self.exprs]))
        return self

    def yield_productions(self):
        """
        Yield how this expression produces grammar productions.
        A :class:`GrammarExpression` class should implement its own.
        """
        raise NotImplementedError


class And(GrammarExpression):
    """
    An "+" expression that requires matching a sequence.
    """

    def __init__(self, exprs):
        super(And, self).__init__(exprs)

    def __iadd__(self, other):
        if isinstance(other, basestring):
            other = String(other)
        return self.append(other)

    def yield_productions(self):
        yield ExpressionProduction(self, self.exprs)


class Or(GrammarExpression):
    """
    An "|" expression that requires matching any one.
    """

    def __init__(self, exprs):
        super(Or, self).__init__(exprs)

    def __ior__(self, other):
        if isinstance(other, basestring):
            other = String(other)
        return self.append(other)  # Or( [ self, other ] )

    def yield_productions(self):
        # yield a production for *every* element in .exprs
        for e in self.exprs:
            yield ExpressionProduction(self, [e])


# ##### Unary Grammar Enhanced Elements ######


class GrammarElementEnhance(GrammarElement):
    """
    Enhanced grammar symbols for :class:`Optional`/:class:`OneOrMore` etc.
    """

    def __init__(self, expr):
        super(GrammarElementEnhance, self).__init__()
        if isinstance(expr, basestring):
            expr = String(expr)
        self.expr = expr
        self.str = _ustr(self.expr)
        self.is_terminal = False

    def default_name(self):
        return self.str

    def _parse(self, instring):
        return self.expr._parse(instring)

    def streamline(self):
        super(GrammarElementEnhance, self).streamline()
        self.expr.streamline()
        return self

    def yield_productions(self):
        """
        Yield how this expression produces grammar productions.
        A :class:`GrammarElementEnhance` class should implement its own.
        """
        raise NotImplementedError


class Optional(GrammarElementEnhance):
    """
    Optional matching (0 or 1 time).
    """
    def __init__(self, expr):
        super(Optional, self).__init__(expr)

    def yield_productions(self):
        """
        Yield how this expression produces grammar productions.
        If A = Optional(B), then this yields::

            A => NULL
            A => B
        """
        yield Production.factory(self, NULL)
        yield Production.factory(self, self.expr)


class OneOrMore(GrammarElementEnhance):
    """
    OneOrMore matching (1 or more times).
    """
    def __init__(self, expr):
        super(OneOrMore, self).__init__(expr)
        self.as_list = True

    def yield_productions(self):
        """
        Yield how this expression produces grammar productions.
        If A = OneOrMore(B), then this yields::

            A => B
            A => B A
        """
        yield Production.factory(self, self.expr)
        yield Production.factory(self, [self.expr, self])


class ZeroOrMore(GrammarElementEnhance):
    """
    ZeroOrMore matching (0 or more times).
    """
    def __init__(self, expr):
        super(ZeroOrMore, self).__init__(expr)
        self.as_list = True

    def yield_productions(self):
        """
        Yield how this expression produces grammar productions.
        If A = ZeroOrMore(B), then this yields::

            A => NULL
            A => B
            A => B A

        or (semantically equivalent)::

            A => NULL
            A => OneOrMore(B)

        """
        yield Production.factory(self, NULL)
        yield Production.factory(self, self.expr)
        yield Production.factory(self, [self.expr, self])


class Null(GrammarElement):
    """
    Null state, used internally
    """
    def __init__(self):
        super(Null, self).__init__()
        self.name = "Null"

    def _parse(self, instring):
        """
        Always returns False, no exceptions.

        :param str instring:  input string to be parsed
        :return: False
        """
        return False

    def default_name(self):
        return "Null"


# make a global NULL object shared by all productions
NULL = Null().set_name("NULL")


# ####################################
# ######### Developer  Space #########
# ####################################

# ##### Real Grammar Implementation ######

class GrammarImpl(object):
    """
    Actual grammar implementation that is returned by a :class:`Grammar`
    construction.
    """

    def __init__(self, name, dct):
        """
        This :func:`__init__` function should only be called from
        :class:`MetaGrammar` but never explicitly.

        :param str name: name of this grammar class
        :param dict dct: __class__.__dict__ field
        """
        self.name = name
        self._vid2name = self._extract_var_names(dct)
        self.goal = dct['GOAL']

        # call _set_element_name_recursively() first then
        # _build_grammar_recursively(), the latter decides whether to
        # streamline expressions based on element names
        self._set_element_name_recursively(self.goal)
        self.productions = self._build_grammar_recursively(self.goal, set())
        self._eliminate_null_and_expand()
        self.terminal2prod = {}
        self.nonterminal2prod = {}
        self.terminal2prod[NULL] = NullProduction
        self.productions.add(NullProduction)
        self.goal_productions = set()
        for prod in self.productions:
            if prod.is_terminal:
                self.terminal2prod[prod.lhs] = prod
            else:
                if prod.lhs not in self.nonterminal2prod:
                    # each nonterminal could map to multiple productions
                    self.nonterminal2prod[prod.lhs] = set()
                self.nonterminal2prod[prod.lhs].add(prod)
            if prod.lhs == self.goal:
                self.goal_productions.add(prod)
        self._lc_words = {}  # for terminal
        self._lc_cats = {}   # for non-terminal

        self.logger = logging.getLogger(__name__)
        if not self.logger.disabled:
            self.logger.debug("Grammar size: %d" % len(self))
            self.logger.debug("Grammar:\n" + str(self) + "\n")

    def _eliminate_null_and_expand(self):
        """
        Eliminate the Null elements in grammar by introducing more productions
        without Null elements. For each production *with* Null, add a new
        production *without*. For instance::

            S => Optional(A) B Optional(C)
            Optional(A) => NULL    --> remove
            Optional(A) => A
            Optional(C) => NULL
            Optional(C) => C       --> remove

        becomes::

            S => Optional(A) B Optional(C)
            Optional(A) => A
            Optional(C) => C
            S => B Optional(C)     --> added
            S => Optional(A) B     --> added
            S => B                 --> added

        The rational behind this is that NULL elements call for a lot of extra
        computation and are highly ambiguous. This function  increases the size
        of grammar but helps gain extra parsing speed. In reality comparison
        of a parsing task:

            - without eliminating: 1.6s, _fundamental_rule() was called
              38K times, taking 50% of all computing time.
              2c52b18d5fcfb901b55ff0506d75c3f41073871c
            - with eliminating: 0.6s, _fundamental_rule() was called 23K
              times, taking 36% of all computing time.
              33a1f3f541657ddf0204d02338d94a7e89473d86

        """
        null_productions = set()
        for prod in self.productions:
            if all(type(rhs) is Null for rhs in prod.rhs):
                null_productions.add(prod)

        # remove all NULL Productions
        self.productions.difference_update(null_productions)

        null_elements = set(p.lhs for p in null_productions)

        identity_productions = set()
        for prod in self.productions:
            if len(prod.rhs) == 1 and not prod.is_terminal \
                    and prod.rhs[0] == prod.lhs:
                identity_productions.add(prod)

        # remove all Identity Productions, which wastes CPU cycles
        self.productions.difference_update(identity_productions)

        def null_indices(rhs):
            return [i for i in range(len(rhs)) if rhs[i] in null_elements]

        def all_combinations(rhs):
            # could be, e.g.: [0,2]
            remove_indices = null_indices(rhs)
            # could be, e.g.: [0,1,2,3]
            full_indices = set(range(len(rhs)))
            if len(remove_indices) > 0:
                for i in range(1, len(remove_indices)+1):
                    for remove in itertools.combinations(remove_indices, i):
                        # remove values:
                        # In [0]: list(itertools.combinations([0,2], 1))
                        # Out[0]: [(0,), (2,)]
                        # In [1]: list(itertools.combinations([0,2], 2))
                        # Out[1]: [(0, 2)]
                        yield sorted(list(full_indices - set(remove)))
                        # returned values:
                        # [1,2,3], [0,1,3], [1,3]

        # for each production *with* null, add a new production *without*
        # e.g.,
        #   S => Optional(A) B Optional(C)
        #   Optional(A) => NULL    --> remove
        #   Optional(A) => A
        #   Optional(C) => NULL
        #   Optional(C) => C       --> remove
        # becomes:
        #   S => Optional(A) B Optional(C)
        #   Optional(A) => A
        #   Optional(C) => C
        #   S => B Optional(C)     --> added
        #   S => Optional(A) B     --> added
        #   S => B                 --> added
        new_prods = set()
        # redo = False
        for prod in self.productions:
            for indices in all_combinations(prod.rhs):
                new_rhs = [prod.rhs[i] for i in indices]
                if len(new_rhs) > 0:
                    new_prods.add(Production.factory(prod.lhs, new_rhs))
                else:
                    # RHS is all NULL, e.g., And(Optiona1 + Zero2) -> Null
                    new_prod = Production.factory(prod.lhs, [NULL])
                    if new_prod not in null_productions:
                        new_prods.add(new_prod)
                        # redo = True
        self.productions.update(new_prods)

        # Known bug: commenting out the following code will not parse
        # deeper NULL elements such as:
        # And(Optiona1 + Zero2 + Zero3) -> NULL
        #
        # But it will significantly increase parsing speed by reducing
        # grammar sizes. Developers are enouraged to write NULL elements
        # explicitly (utilizing Optional/ZeroOrMore etc).
        #
        # if redo:
        #     self._eliminate_null_and_expand()

    def _get_variable_name(self, variable):
        return self._vid2name.get(id(variable), None)

    def _extract_var_names(self, dct):
        """
        Given a dictionary, extract all variable names. For instance, given::

            light_general_name = Regex(r"(lights|light|lamp)")

        extract the mapping from ``id(light_general_name)`` to
        "light_general_name"

        :param dict dct: a grammar dictionary
        :return: a dictionary mapping from ``id(variable)`` to variable name.
        """
        vid2name = {}
        for k, v in dct.items():
            if isinstance(v, GrammarElement):
                vid2name[id(v)] = k
        return vid2name

    def _build_grammar_recursively(self, element, productions):
        """
        Build a grammar from  `element`. This mainly includes recursively
        extracting :class:`AND`/:class:`OR` :class:`GrammarExpression`'s
        from `element`.

        :param GrammarExpression element: a :class:`GrammarExpression`
        :param set productions: assign to `set()` when calling the first time
        :return: a set of :class:`Production`
        :rtype: set(:class:`Production`)
        """

        # streamline helps to flatten grammar hierarchies (thus parse trees).
        # e.g., Given a grammar: S -> S and S, the internal representation is
        # *actually*: S -> And(And(S, and), S), or put it another way:
        # the grammar is automatically binarized due to the nature of operator
        # overloading (__add__(self, other)).
        #
        # *If* we do CKY parsing, this (no streamline) actually saves us from
        # binarizing the grammar (though the parse tree will be binary too).
        # Now that we do chart parsing, streamlining un-binarize the grammar:
        # S -> [S, and, S] (a list). The output parse tree also looks more
        # compact  and intuitive.
        if not element.streamlined:
            element.streamline()

        if isinstance(element, GrammarExpression):
            # depth first traversal
            for e in element.exprs:
                self._build_grammar_recursively(e, productions)

            for p in element.yield_productions():
                productions.add(p)
        elif isinstance(element, GrammarElementEnhance):
            self._build_grammar_recursively(element.expr, productions)
            for p in element.yield_productions():
                productions.add(p)
        elif isinstance(element, GrammarElement):
            productions.add(element.production())

        return productions

    def _set_element_name_recursively(self, element):
        name_is_set = self._set_element_variable_name(element)
        if isinstance(element, GrammarExpression):
            for e in element.exprs:
                if not e.name_is_set:
                    self._set_element_name_recursively(e)
        elif isinstance(element, GrammarElementEnhance):
            self._set_element_name_recursively(element.expr)
        # call this function *after* recursively visiting children elements
        # so that parent element without a name can "borrow" one from its child
        if not name_is_set:
            self._set_element_canonical_name(element)

    def _set_element_variable_name(self, element):
        """
        Set the variable_name field of `element`

        :param GrammarElement element: a grammar element
        :return bool: True if found else False
        """
        ename = self._get_variable_name(element)
        if ename is not None:
            element.variable_name = ename
            element.name_is_set = True
            return True
        else:
            return False

    def _set_element_canonical_name(self, element):
        """
        Set the canonical name field of `element`, if not set yet

        :param GrammarElement element: a grammar element
        :return: None
        """
        # try our best to give a name by borrowing names from children
        if isinstance(element, GrammarElementEnhance):
            # if we have a production like Optional(quantifier)
            # we hope to give a name of "Optional(quantifier)"
            expr_name = str(element.expr)
        elif isinstance(element, GrammarExpression):
            expr_name = ", ".join([str(e) for e in element.exprs])
        elif isinstance(element, GrammarElement):
            expr_name = element.default_name()
        else:
            raise GrammarException("unrecognized element: " + str(element))

        element.canonical_name = element.__class__.__name__ + \
            "(" + expr_name + ")"
        element.name_is_set = True

    def build_leftcorner_table(self):
        """
        For each grammar production, build two mappings from the production
        to:

            1. its left corner RHS element (which is a pre-terminal);
            2. the terminal element that does the actual parsing job.
        """
        def add_to_leftcorner(prod, c_prod):
            rhs = c_prod.rhs[0]
            if prod not in self._lc_words:
                self._lc_words[prod] = set()
                self._lc_cats[prod] = {prod}

            if rhs.is_terminal:
                self._lc_words[prod].add(self.terminal2prod[rhs])
            else:
                for cc_prod in self.nonterminal2prod[rhs]:
                    self._lc_cats[prod].add(cc_prod)
                    add_to_leftcorner(prod, cc_prod)

        for prod in self.productions:
            add_to_leftcorner(prod, prod)

    def get_left_corner_terminals(self, prod):
        """
        Given a grammar production, return a set with its left-corner terminal
        productions, or an empty set if not found, .e.g.::

            S => A B
            A => C D
            A => e f
            B => b
            C => c

        passing `S` as `prod` will return the set of productions for `e` and
        `c`.

        :param Production prod: a grammar production
        :return: set(:class:`Production`)
        """
        return self._lc_words.get(prod, set())

    def get_left_corner_nonterminals(self, prod):
        """
        Given a grammar production, return a set with its left-corner
        non-terminal productions, or a set with `prod` itself if not found,
        .e.g.::

            S => A B
            A => C D
            A => e f
            B => b
            C => c

        passing `S` as `prod` will return the set of productions for `A` and
        `C`.


        :param Production prod: a grammar production
        :return: set(:class:`Production`)
        """
        return self._lc_cats.get(prod, {prod})

    def __str__(self):
        strings = []
        for p in self.productions:
            if p.is_terminal:
                strings.append("IsaTerminal  " + str(p))
            else:
                strings.append("NonTerminal  " + str(p))
        return "\n".join(sorted(strings))

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.productions)

    # @memoize --> needs to change code to return list intead of a generator
    def filter_terminals_for_scan(self, lexicon):
        """
        Yield all terminal productions that parses `lexicon`.

        :param str lexicon: a string to be parsed
        :return: a production generator
        :rtype: generator(:class:`Production`)
        """
        for prod in self.productions:
            if prod.is_terminal:
                try:
                    progress = prod.lhs.parse(lexicon)
                except ParseException:
                    pass
                else:
                    if progress:
                        yield prod

    # @memoize --> needs to change code to return list intead of a generator
    def filter_productions_for_prediction_by_rhs(self, rhs_starts_with):
        """
        Yield all productions whose RHS[0] is `rhs_starts_with`.

        :param GrammarElement rhs_starts_with: a grammar element
        :return: a production generator
        :rtype: generator(:class:`Production`)
        """
        for prod in self.productions:
            # replaced "==" here with "is" and got 2x speed up
            if prod.rhs[0] is rhs_starts_with:
                yield prod

    def filter_productions_for_prediction_by_lhs(self, lhs):
        """
        Yield all productions whose LHS is `lhs`.

        :param GrammarElement lhs: a grammar element
        :return: a production generator
        :rtype: generator(:class:`Production`)
        """
        for prod in self.productions:
            # replaced "==" here with "is" and got 2x speed up
            if prod.lhs is lhs:
                yield prod

    # def filter_nonterminals_for_prediction(self):
    #     """ Yield all nonterminal productions.
    #     :return: a production generator
    #     :rtype: generator(:class:`Production`)
    #     """
    #     for prod in self.productions:
    #         if not prod.is_terminal:
    #             yield prod


class Production(object):
    """
    Abstract class for a grammar production in the form:

        LHS --> RHS (RHS is a list)

    A grammar **production** is used by the parser while a grammar **element**
    by the user.

    :param lhs: a single LHS of :class:`GrammarElement`
    :param list rhs: a list of RHS element, each of which is of
                     :class:`GrammarElement`
    """

    def __init__(self, lhs, rhs):
        assert isinstance(lhs, GrammarElement)
        assert type(rhs) is list, "Error: RHS must be a list"
        self.lhs = lhs
        self.rhs = rhs
        self.rhs_len = len(self.rhs)
        self.is_terminal = lhs.is_terminal
        self._hash = hash((self.lhs,) + tuple(self.rhs))
        # recursive production like the following from
        # ZeroOrMore or OneOrMore:
        # yield Production.factory(self, [self.expr, self])
        self.is_recursive = any(lhs is r for r in rhs)
        self.as_list = lhs.as_list

    @staticmethod
    def factory(lhs, rhs=None):
        """
        a Production factory that constructs new productions according to the
        type of `lhs`. Users can either call this function, or directly call
        Production constructors.

        :param lhs: a single LHS of :class:`GrammarElement`
        :param rhs: RHS elements (single or a list), each of which is of
                         :class:`GrammarElement`
        :type rhs: list, :class:`GrammarElement`
        """
        if isinstance(lhs, GrammarExpression):
            if rhs:
                return ExpressionProduction(lhs, rhs)
            else:
                return ExpressionProduction(lhs, lhs.exprs)
        elif isinstance(lhs, GrammarElementEnhance):
            if rhs:
                return ElementEnhanceProduction(lhs, rhs)
            else:
                return ElementEnhanceProduction(lhs)
        else:  # GrammarElement
            return ElementProduction(lhs)

    def get_rhs(self, position):
        return self.rhs[position]

    def __str__(self):
        return "%s (%s) -> [%s]" % \
               (self.lhs.__class__.__name__, _ustr(self.lhs),
                ", ".join([_ustr(r) for r in self.rhs]))

    def __eq__(self, other):
        # return (self is other or
        #         (other is not None and self.lhs == other.lhs and
        #          self.rhs == other.rhs))
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self._hash


class ExpressionProduction(Production):
    """
    Wrapper of :class:`GrammarExpression`.
    """

    def __init__(self, lhs, rhs):
        Production.__init__(self, lhs, rhs)


class ElementProduction(Production):
    """
    Wrapper of :class:`GrammarElement`. An :class:`ElementProduction`
    has the following assertion true:

        LHS == RHS[0]
    """

    def __init__(self, element):
        Production.__init__(self, element, [element])


class ElementEnhanceProduction(ElementProduction):
    """
    Wrapper of :class:`GrammarElementEnhance`. An
    :class:`ElementEnhanceProduction` has the following assertion true:

        LHS == RHS[0]
    """

    def __init__(self, element, rhs=None):
        if rhs:
            if type(rhs) is list:
                Production.__init__(self, element, rhs)
            else:
                Production.__init__(self, element, [rhs])
        else:
            Production.__init__(self, element, [element.expr])
        assert isinstance(element, GrammarElementEnhance)


NullProduction = ElementProduction(NULL)


class TreeNode(object):
    """A tree structure to represent parser output.
    ``parent`` should be a chart :class:`Edge` while ``children``
    should be a :class:`TreeNode`.
    `lexicon` is the matched string if this node is a leaf node.

    :param Edge parent: an edge in Chart
    :param list children: a list of :class:`TreeNode`
    :param str lexicon: matched string when this node is a leaf node.
    """

    def __init__(self, parent, children, lexicon=None):
        self.parent = parent
        if type(children) is tuple:
            children = list(children)
        self.children = children
        self.lexicon = lexicon
        # flatten recursive production:
        # (OneOrMore(one_parse)
        #   (one_parse ...  )
        #   (OneOrMore(one_parse)
        #     (one_parse ... )
        #     (OneOrMore(one_parse)
        #       (one_parse ... )
        #     )
        #   )
        # )
        # becomes:
        # (OneOrMore(one_parse)
        #   (one_parse ... )
        #   (one_parse ... )
        #   (one_parse ... )
        # )
        if parent.prod.is_recursive:
            new_children = []
            for child in self.children:
                if child.parent.prod.lhs is parent.prod.lhs:
                    new_children.extend(child.children)
                else:
                    new_children.append(child)
            self.children = new_children

    def is_leaf(self):
        return len(self.children) == 0

    # def add_child(self, child):
    #     self.children.append(child)

    def __str__(self):
        return TreeNode.recursive_str(self)

    def size(self):
        """
        size is the total number of non-terminals and terminals in the tree

        :return: int
        :rtype: int
        """
        size = 1
        if not self.is_leaf():
            for child in self.children:
                size += child.size()
        return size

    def dict_for_js(self):
        """
        represents this tree in :class:`dict` so a json format can be
        extracted by::

            json.dumps(node.dict_for_js())

        :return: a :class:`dict`
        """
        name = str(self.parent.prod.lhs)
        if self.is_leaf():
            return {name: self.lexicon}
        else:
            children = [child.dict_for_js() for child in self.children]
            return {name: children}

    @staticmethod
    def recursive_str(node, indent=0):
        string = " " * indent + "(" + str(node.parent.prod.lhs)
        if not node.is_leaf():
            string += "\n"
            for child in node.children:
                string += node.recursive_str(child, indent + 2)
            string += " " * indent + ")\n"
        else:  # leaf
            # string += " " + str(node.parent.prod.rhs[0]) + ")\n"
            string += ' "' + node.lexicon + '")\n'
        return string

    @staticmethod
    def recursive_str_verbose(node, indent=0):
        string = " " * indent + "(" + str(node.parent.prod.lhs) + "<" + \
                 str(node.parent.prod.lhs) + ">"
        if not node.is_leaf():
            string += "\n"
            for child in node.children:
                string += node.recursive_str_verbose(child, indent + 2)
            string += " " * indent + ")\n"
        else:  # leaf
            string += " " + str(node.parent.prod.rhs[0]) + "<" + \
                      str(node.parent.prod.rhs[0]) + ">" + ")\n"
        return string

    def get_flat_dict(self, key="one_parse", only_leaf=True):
        return self.get_flat_dict_with_key([], key, only_leaf)

    def get_flat_dict_with_key(self, ret_list,
                               key="one_parse", only_leaf=True):
        name = str(self.parent.prod.lhs)
        if name == key:
            ret_list.append(self.get_flat_dict_all({}, only_leaf))
        else:
            for child in self.children:
                child.get_flat_dict_with_key(ret_list, key, only_leaf)
        return ret_list

    def get_flat_dict_all(self, flat_dict, only_leaf=True):
        name = str(self.parent.prod.lhs)
        if (self.lexicon != "" and
                ((only_leaf and self.is_leaf()) or not only_leaf)):
            if name not in flat_dict:
                flat_dict[name] = []
            flat_dict[name].append(self.lexicon)
        for child in self.children:
            child.get_flat_dict_all(flat_dict, only_leaf)
        return flat_dict

    def to_parse_result(self):
        """
        Convert this TreeNode to a ParseResult. The result is flattened
        as much as possible following:

        * if the parent node has ``as_list=True`` (ZeroOrMore and OneOrMore),
          then its children are not flattened;
        * children are flattened (meaning: they are elevated to the same level
          as their parents) in the following cases:

          - child is a leaf node
          - parent has ``as_list=False`` **and** all children have no name
            conflicts (e.g., in
            ``p -> {c1 -> {n -> "lexicon1"}, c2 -> {n -> "lexicon2"}}``,
            ``n`` will be elevated to the same levels of ``c1`` and ``c2``
            separately, but not to the same level of ``p``).

        :return: :class:`ParseResult`
        """
        lhs = self.parent.prod.lhs
        if lhs.ignore_in_result:
            return None
        name = str(lhs)
        parent_as_flat = not lhs.as_list
        if not self.lexicon:
            return None

        children, child_results = [], []
        for c in self.children:
            r = c.to_parse_result()
            if r is not None:
                children.append(c)
                child_results.append(r)

        result = ParseResult(name, self.lexicon, parent_as_flat)

        if len(children) != 0:
            name2count = Counter(name for c in child_results
                                 for name in c.names())
            as_flats = [parent_as_flat and
                        all(name2count[name] == 1 for name in c.names())
                        for c in child_results]

            for child, child_result, as_flat in \
                    zip(children, child_results, as_flats):
                result.add_result(child_result, child.is_leaf() or as_flat)

            # update the lexicon of parent to sync with lexicon of children
            new_lexicon = [child_result.get()
                           for child_result in child_results]
            if len(new_lexicon) == 1 and parent_as_flat:
                new_lexicon = new_lexicon[0]
            result.set(new_lexicon)

        lhs.run_post_funcs(result)
        return result


class Edge(object):
    """An edge in the chart with the following fields:

    :param int start: the starting position
    :param int end: the end position, so span = end - start
    :param Production production: the grammar production
    :param int dot: the dot position on the RHS. Any thing before the
                    `dot` has been consumed and after is waiting to complete
    """
    __slots__ = ["start", "end", "prod", "dot", "_hash"]

    def __init__(self, start, end, production, dot):
        assert start >= 0, "Error: start of edge is %d" % start
        assert end >= 0, "Error: end of edge is %d" % end
        self.start = start
        self.end = end
        self.prod = production
        self.dot = dot
        # warning: hash is computed only once, we need to make sure that Edge
        # is immutable, thus setting __slots__ above
        self._hash = hash((self.start, self.end, self.prod, self.dot))

    def __eq__(self, other):
        # eq = (self is other or
        #       other is not None and self.start == other.start and
        #       self.end == other.end and self.dot == other.dot and
        #       self.prod == other.prod)
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self._hash

    def span(self):
        """
        The span this edge covers, alias of ``end - start``. For instance,
        for edge::

            [1, 3] NP ->  * NNS

        it returns 2

        :return: an int
        :rtype: int
        """
        return self.end - self.start

    def get_rhs_after_dot(self):
        """
        Returns the RHS symbol after dot. For instance, for edge::

            [1, 1] NP ->  * NNS

        it returns NNS.

        If no symbol is after dot, then return None.

        :return: RHS after dot
        :rtype: :class:`GrammarElement`
        """
        if self.dot == self.prod.rhs_len:
            return None
        else:
            return self.prod.get_rhs(self.dot)

    def scan_after_dot(self, phrase):
        """
        Scan `phrase` with RHS after the dot. Returns a tuple of
        (lexical_progress, rhs_progress) in booleans.

        :return: a tuple
        :rtype: tuple(bool, bool)
        """

        if self.prod.rhs_len != self.dot:
            rhs = self.prod.rhs[self.dot]

            if rhs.is_terminal:
                try:
                    progress = rhs.parse(phrase)
                except ParseException:
                    return False, False
                else:
                    return progress, True
            else:
                return None, None
        else:
            return False, False

    def merge_and_forward_dot(self, edge):
        """
        Move the dot of self forward by one position and change the end
        position of self edge to end position of `edge`. Then return a new
        merged Edge. For instance::

            self: [1, 2] NNS ->  * NNS CC NNS
            edge: [2, 3] NNS -> men *

        Returns a new edge::

            [1, 3] NNS -> NNS * CC NNS

        Requires that ``edge.start == self.end``

        :return: a new edge
        :rtype: :class:`Edge`
        """
        assert edge.start == self.end, \
            "Can't merge and forward dot: \n%s\n%s" % (self, edge)

        assert self.dot < self.prod.rhs_len, \
            "Dot position (%d) way behind RHS (%s)" % (self.dot, self)
        return Edge(self.start, edge.end, self.prod, self.dot + 1)

    def is_complete(self):
        """Whether this edge is completed.

        :rtype: bool
        """
        return self.prod.rhs_len == self.dot

    def __str__(self):
        return "[%d, %d] %s (%s) -> %s * %s" % (
            self.start, self.end,
            self.prod.lhs.__class__.__name__, _ustr(self.prod.lhs),
            " ".join([_ustr(e) for e in self.prod.rhs[0:self.dot]]),
            " ".join([_ustr(e) for e in self.prod.rhs[self.dot:]]))

    def __repr__(self):
        return self.__str__()


class Agenda(object):
    """
    An agenda for ordering edges that will enter the chart.
    Current implementation is a wrapper around :class:`collections.deque`.

    :class:`collections.deque` supports both FILO
    (:func:`collections.deque.pop()`) and FIFO
    (:func:`collections.deque.popleft()`). FILO functions like a stack:
    edges get immediately popped out after they are pushed in. This has merit
    of finishing the parse *sooner*, esp. when new edges are just completed,
    then we can pop them for prediction.
    """
    def __init__(self, *args, **kwargs):
        self.agenda = deque(*args, **kwargs)
        self.total = 0

    def append(self, edge):
        """
        Add a single `edge` to agenda. `edge` can be either complete or not
        to be appended to agenda.

        :param Edge edge:
        """
        self.agenda.append(edge)
        self.total += 1

    def pop(self):
        """
        Pop an edge from agenda (stack).

        :return: an edge
        :rtype: :class:`Edge`
        """
        return self.agenda.pop()

    def __len__(self):
        return len(self.agenda)

    def extend(self, edges):
        """
        Add a sequence of `edges` to agenda.

        :param edges:
        :type: list(:class`Edge`)
        """
        self.agenda.extend(edges)
        self.total += len(edges)


class ParseResult(object):
    """
    Parse result converted from :class:`TreeNode` output, providing easy
    access by list or attribute style, for instance::

        result['color']
        result.color

    Results are flattened as much as possible, meaning: deep children are
    elevated to the top as much as possible as long as there are no
    name conflicts. For instance, given the following parse tree::

        (GOAL
          (And(action_verb, OneOrMore(one_parse))
            (action_verb "flash")
            (OneOrMore(one_parse)
              (one_parse
                (light_name
                  (Optional(light_quantifiers)
                    (light_quantifiers "both")
                  )
                  (ZeroOrMore(light_specific_name)
                    (light_specific_name "top")
                    (light_specific_name "bottom")
                  )
                  (Optional(light_general_name)
                    (light_general_name "light")
                  )
                )
                (ZeroOrMore(color)
                  (color "red")
                )
              )
              (one_parse
                (light_name
                  (ZeroOrMore(light_specific_name)
                    (light_specific_name "middle")
                  )
                  (Optional(light_general_name)
                    (light_general_name "light")
                  )
                )
                (ZeroOrMore(color)
                  (color "green")
                )
              )
              (one_parse
                (light_name
                  (ZeroOrMore(light_specific_name)
                    (light_specific_name "bottom")
                  )
                )
                (ZeroOrMore(color)
                  (color "purple")
                )
              )
            )
          )
        )

    The parse result looks like::

        {
          "action_verb": "flash",
          "one_parse": [
            {
              "one_parse": "both top bottom light red",
              "light_name": "both top bottom light",
              "light_quantifiers": "both",
              "ZeroOrMore(color)": "red",
              "color": "red",
              "ZeroOrMore(light_specific_name)": "top bottom",
              "Optional(light_general_name)": "light",
              "light_general_name": "light",
              "Optional(light_quantifiers)": "both",
              "light_specific_name": [
                "top",
                "bottom"
              ]
            },
            {
              "one_parse": "middle light green",
              "light_name": "middle light",
              "ZeroOrMore(color)": "green",
              "color": "green",
              "ZeroOrMore(light_specific_name)": "middle",
              "Optional(light_general_name)": "light",
              "light_general_name": "light",
              "light_specific_name": "middle"
            },
            {
              "one_parse": "bottom purple",
              "light_name": "bottom",
              "ZeroOrMore(color)": "purple",
              "color": "purple",
              "ZeroOrMore(light_specific_name)": "bottom",
              "light_specific_name": "bottom"
            }
          ],
          "And(action_verb, OneOrMore(one_parse))": "flash both top bottom
          light red middle light green bottom purple",
          "GOAL": "flash both top bottom light red middle light green bottom
          purple",
          "OneOrMore(one_parse)": "both top bottom light red middle light green
          bottom purple"
        }

    The following holds true given the above result::

        assert result.action_verb == "flash"
        assert result['action_verb'] == "flash"
        assert type(result.one_parse) is list
        assert result.one_parse[0].color == 'red'
        assert result.one_parse[0].light_specific_name == ['top', 'bottom']
        assert result.one_parse[1].light_specific_name == 'middle'

    Note how the parse result is flattened w.r.t. the tree. Basic principles
    of flattening are:

    - value of result access is either a string or another :class:`ParseResult`
      object
    - If a node has >= 1 children with the same name, make the name hold a list
    - Else make the name hold a string value.

    """
    def __init__(self, name, lexicon, as_flat=True):
        super(ParseResult, self).__setattr__("_name", name)
        super(ParseResult, self).__setattr__("_as_flat", as_flat)
        if as_flat:
            super(ParseResult, self).__setattr__("_results", {name: lexicon})
        else:
            super(ParseResult, self).__setattr__("_results", {name: [lexicon]})

    def set(self, value):
        """
        Set the value of ParseResult. ``value`` is not necessarily a string
        though: post functions from :func:`GrammarElement.set_result_action`
        can pass a different value to ``value``.
        """
        self[self._name] = value

    def add_item(self, k, v):
        """
        Add a ``k => v`` pair to result
        """
        if k not in self._results:
            if self._as_flat:
                self._results[k] = v
            else:
                self._results[k] = [v]
        elif type(self._results[k]) is not list:
            self._results[k] = [self._results[k], v]
        else:
            self._results[k].append(v)

    def add_result(self, result, as_flat):
        """
        Add another result to the current result.

        :parameter ParseResult result: another result
        :parameter bool as_flat: whether to flatten `result`.
        """
        if as_flat:
            for k, v in result.items():
                self.add_item(k, v)
        else:
            self.add_item(result.name(), result)

    def __contains__(self, item):
        return item in self._results

    def get(self, item=None, default=None):
        """
        Get the value of ``item``, if not found, return ``default``.
        If ``item`` is not set, then get the main value of ParseResult.
        The usual value is a lexicon string.
        But it can be different if the :func:`ParseResult.set` function is
        called.
        """
        if item:
            return self._results.get(item, default)
        else:
            return self[self._name]

    def name(self):
        """
        Return the result name

        :return: a string
        :rtype: str
        """
        return self._name

    def names(self):
        """
        Return the set of names in result
        """
        return self._results.keys()

    def __getitem__(self, item):
        return self._results.get(item, None)

    def __setitem__(self, key, value):
        self._results[key] = value

    def __delitem__(self, item):
        del self._results[item]

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        del self[item]

    def keys(self):
        """
        Return the set of names in result
        """
        return self._results.keys()

    def values(self):
        """
        Return the set of values in result
        """
        return self._results.values()

    def items(self):
        """
        Return the dictionary of items in result
        """
        return self._results.items()

    @staticmethod
    def _serialize(obj):
        return obj._results

    def __str__(self):
        return json.dumps(self._results,
                          default=ParseResult._serialize,
                          indent=2)

    def __repr__(self):
        return self.__str__()


class Chart(object):
    """
    A 2D chart (list) to store graph edges. Edges can be accessed via:
    Chart.edges[start][end] and return value is a set of edges.

    :param int size: chart size, normally ``len(tokens) + 1``.
    """

    def __init__(self, size):
        self._init_pointers()
        self.size = size
        self.edges = [[set() for _ in xrange(self.size)]
                      for _ in xrange(self.size)]
        # current parsing progress; when chart_i = m, it means we are
        # considering the token between m-1 and m.
        self.chart_i = 0

    def _init_pointers(self):
        # edge2backpointers hold only tuples of children edges
        # (could be {1,2,...}) instead of 2-tuple of (previous, child) edges
        # (version 1). # This has the benefit of handling non-binary
        # productions (e.g., NP -> NP CC NP while verion 1 has to be sth like:
        # NP -> (NP CC) NP
        self.edge2backpointers = {}

    def add_edge(self, edge, prev_edge, child_edge, lexicon=''):
        """
        Add `edge` to the chart with backpointers being
        `previous edge` and `child edge`

        :param Edge edge: newly formed edge
        :param Edge prev_edge: the left (previous) edge where edge is
                               coming from
        :param Edge child_edge: the right (child) edge that the completion
                                of which moved the dot ot prev_edge
        :return bool: Whether this edge is newly inserted
                      (not already exists)
        """
        if edge in self.edges[edge.start][edge.end]:
            ret = False
        else:
            ret = True
            self.edges[edge.start][edge.end].add(edge)

        if child_edge and edge != child_edge:
            # not child_edge: prevent recursion
            if edge not in self.edge2backpointers:
                self.edge2backpointers[edge] = set()

            if prev_edge in self.edge2backpointers:
                for prev_child_edges in self.edge2backpointers[prev_edge]:
                    # lists are unhashable, thus using tuples
                    new_child_edges = prev_child_edges + (child_edge,)
                    self.edge2backpointers[edge].add(new_child_edges)
            else:
                # pay attention to , to make sure it's a tuple instead of
                # a parenthesis
                new_child_edges = (child_edge,)
                self.edge2backpointers[edge].add(new_child_edges)
                # sanity check, should all pass
                # if len(new_child_edges) != edge.dot:
                #   print("missing children")

        return ret

    def filter_edges_for_prediction(self, end):
        """
        Return a list of edges ending at ``end``.

        :param int end: end position
        :return: list(:class:`Edge`)
        """
        edges = []
        for i in xrange(min(self.size, end + 1)):
            for edge in self.edges[i][end]:
                edges.append(edge)
        return edges

    def filter_edges_for_completion(self, end, rhs_after_dot):
        """
        Find all edges with matching ``end`` position and RHS nonterminal
        directly after the dot as ``rhs_after_dot``. For instance, both edges::

            [1, 1] NNS ->  * NNS CC NNS
            [1, 1] NP ->  * NNS

        match `end=1` and `rhs_after_dot=NNS`
        """
        # Note: fix can't use yield
        # the reason is that after returning, we immediately add to chart.edges
        # which causes the size of edges to change. One solution is to
        # first put it on agenda, then add to chart (instead of first adding
        # to chart, then to agenda)
        edges = []
        # if end is not None and rhs_after_dot is not None:
        # # edges = [edge
        # # for i in xrange(min(self.size, end+1))
        # #           for edge in self.edges[i][end]
        # #             if edge.get_rhs_after_dot() is rhs_after_dot
        # #         ]
        for i in xrange(min(self.size, end + 1)):
            for edge in self.edges[i][end]:
                # replaced "==" here with "is" and got 2x speed up
                # if edge.get_rhs_after_dot() is rhs_after_dot:
                # avoiding the function call get_rhs_after_dot()
                # is 15% faster
                if edge.prod.rhs_len != edge.dot and \
                   edge.prod.rhs[edge.dot] is rhs_after_dot:
                    # can't yield here because Zero/Optional elements
                    # might be # re-added to edges[i][end], then list
                    # size changed exception yield edge
                    edges.append(edge)
        # elif end is None and rhs_after_dot:
        #     for i in xrange(self.size):
        #         for j in xrange(self.size):
        #             for edge in self.edges[i][j]:
        #                 # replaced "==" here with "is" and got 2x speed up
        #                 # if edge.get_rhs_after_dot() is rhs_after_dot:
        #                 if edge.prod.rhs_len != edge.dot and \
        #                    edge.prod.rhs[edge.dot] is rhs_after_dot:
        #                     # yield edge
        #                     edges.append(edge)
        return edges

    def filter_completed_edges(self, start, lhs):
        """
        Find all edges with matching `start` position and LHS with `lhs`.
        directly after the dot as `rhs_after_dot`. For instance, both edges::

            [1, 1] NP ->  * NNS CC NNS
            [1, 3] NP ->  * NNS

        match ``start=1`` and ``lhs=NP``.

        :return: a list of edges
        :rtype: list(:class:`Edge`)
        """
        edges = []
        for j in xrange(self.size):
            for edge in self.edges[start][j]:
                if edge.is_complete() and edge.prod.lhs is lhs:
                    edges.append(edge)
        return edges

    def __str__(self):
        str_list = []
        for i in xrange(self.size):
            for j in xrange(self.size):
                if len(self.edges[i][j]) > 0:
                    str_list += [str(e) for e in self.edges[i][j]]
        return "\n".join(sorted(str_list))

    def print_backpointers(self):
        """
        Return a string representing the current state of all backpointers.
        """
        str_list = []
        for edge, children in self.edge2backpointers.items():
            str_list.append(str(edge) + " :-> " + str(children))
        return "\n".join(sorted(str_list))

    def trees(self, tokens=None, all_trees=False, goal=None):
        """
        Yield all possible trees this chart covers. If `all_trees` is False,
        then only the most compact trees for each `goal` are yielded. Otherwise
        yield all trees (**warning: can be thousands**).

        :param list tokens: a list of lexicon tokens
        :param bool all_trees: if False, then only print the smallest tree.
        :param goal: the root of this tree (usually Grammar.GOAL)
        :type: GrammarElement, None
        :return: a tuple of (tree index, TreeNode)
        :rtype: tuple(int, :class:`TreeNode`)
        """
        i = 0
        if self.size <= 1:
            raise ParseException("No parse tree found")
        else:
            for root in self.edges[0][self.size - 1]:
                if root.is_complete():
                    if goal is not None and root.prod.lhs != goal:
                        continue
                    i += 1
                    # print("root", i)
                    if all_trees:
                        for tree in self._trees(root, tokens):
                            yield (i, tree)
                    else:
                        for tree in self._most_compact_trees(root, tokens):
                            yield (i, tree)
                            # print("number of complete root nodes:", i)

    def best_tree_with_parse_result(self, trees):
        """
        Return a tuple of the smallest tree among `trees` and its parse result.

        :param list trees: a list of :class:`TreeNode`
        :return: a tuple of (best tree, its parse result)
        :rtype: tuple(:class:`TreeNode`, :class:`ParseResult`)
        """
        if len(trees) == 0:
            raise ParseException("No parse tree found")
        else:
            best_tree = sorted([(t.size(), t) for i, t in trees])[0][1]
            parse_result = best_tree.to_parse_result()
            return best_tree, parse_result

    def _trees(self, parent_edge, tokens=None):
        trees = []
        lexicon = ""
        if tokens is not None:
            lexicon = " ".join(tokens[parent_edge.start: parent_edge.end])
        if parent_edge in self.edge2backpointers:
            for children_edges in self.edge2backpointers.get(parent_edge):
                child_trees = [self._trees(child_edge, tokens) for
                               child_edge in children_edges]
                for t in itertools.product(*child_trees):
                    trees.append(TreeNode(parent_edge, t, lexicon))
        else:
            # leaf child edge doesn't have backpointers
            # previous edges do, but we are only retrieving child edges
            trees = [TreeNode(parent_edge, [], lexicon=lexicon)]

        return trees

    def _most_compact_trees(self, parent_edge, tokens=None):
        """
        Try to eliminate spurious ambiguities by getting the most
        compact/flat tree. This mainly deals with removing Optional/ZeroOrMore
        nodes
        """
        trees = []
        lexicon = ""
        if tokens is not None:
            lexicon = " ".join(tokens[parent_edge.start: parent_edge.end])
        if parent_edge in self.edge2backpointers:
            # to improve efficiency, we can use a priority queue
            # for self.edge2backpointers
            ss = sorted(
                [(len(children_edges), children_edges) for children_edges
                 in self.edge2backpointers[parent_edge]])
            min_child_num = ss[0][0]
            # there could be multiple backpointers of the same size
            min_children_edges = [c for l, c in ss if l == min_child_num]

            child_trees_list = []
            for children_edges in min_children_edges:
                child_trees = [self._most_compact_trees(child_edge, tokens)
                               for child_edge in children_edges]
                child_trees_list.append(child_trees)
            # we select from whoever's children are the smallest
            cc = sorted([(sum([t[0].size() for t in c_trees]),
                          c_trees) for c_trees in child_trees_list])
            child_trees = cc[0][1]
            for t in itertools.product(*child_trees):
                trees.append(TreeNode(parent_edge, t, lexicon))
        else:
            # leaf child edge doesn't have backpointers
            # previous edges do, but we are only retrieving child edges
            trees = [TreeNode(parent_edge, [], lexicon=lexicon)]

        return trees


class IncrementalChart(Chart):
    """
    A 2D chart (list of list) that expands its size as having more
    edges added.

    :param int size: current size of chart
    :param int max_size: total capacity of chart, if exceeded, then
      need to increase by ``inc_size``.
    :param int inc_size: size to increase when max_size is filled
    """

    def __init__(self, init_size=10, inc_size=10):
        """
        :param init_size: the initial size
        :param inc_size: extra size to span when the chart is filled up
        """
        super(IncrementalChart, self).__init__(init_size)
        # actual size that has been used
        self.size = 0
        # total capacity
        self.max_size = init_size
        self.inc_size = inc_size

    def increase_capacity(self):
        """
        Increase the capacity of the current chart by `self.inc_size`
        """

        # padding horizontally -->>
        for i in xrange(self.max_size):
            self.edges[i] += [set() for _ in xrange(self.inc_size)]

        # padding vertically --vv
        self.edges += [[set() for _ in xrange(self.max_size + self.inc_size)]
                       for _ in xrange(self.inc_size)]
        self.max_size += self.inc_size

    def add_edge(self, edge, prev_edge, child_edge, lexicon=''):
        if edge.end >= self.size:
            self.size = edge.end + 1
        if self.size >= self.max_size:
            self.increase_capacity()
        return Chart.add_edge(self, edge, prev_edge, child_edge, lexicon)


# ############## Parsing Rules ##############
# Optimization tricks with closure:
# http://tech.magnetic.com/2015/05/optimize-python-with-closures.html
# or (simpler:) directly use pypy (with warm up)

class ChartRule(object):
    """
    Rules applied in parsing, such as scan/predict/fundamental. New rules
    need to implement the :func:`apply` method.
    """
    def apply(self, *args):
        raise NotImplementedError


class TopDownInitRule(ChartRule):
    """
    Initialize the chart when we get started by inserting the goal.
    """
    NUM_EDGES = 0

    def apply(self, chart, grammar, agenda, phrase):
        if chart.size == 0:
            for prod in grammar.goal_productions:
                edge = Edge(0, 0, prod, 0)
                if chart.add_edge(edge, None, None):
                    agenda.append(edge)
            if len(agenda) == 0:  # corner case: no nonterminals
                for prod in grammar.productions:
                    edge = Edge(0, 0, prod, 0)
                    if chart.add_edge(edge, None, None):
                        agenda.append(edge)
        # agenda is always empty whenever this function is called,
        # we have to fill it with chart edges and do the prediction again
        # if *not* incremental parsing, then we can save a bit here
        if len(agenda) == 0:
            agenda.extend(chart.filter_edges_for_prediction(chart.chart_i-1))
        return False


class BottomUpScanRule(ChartRule):
    """
    Rules used in bottom up scanning.
    """
    NUM_EDGES = 0

    def apply(self, chart, grammar, agenda, phrase):
        current_lexicon_progressed_by_grammar = False
        for prod in grammar.filter_terminals_for_scan(phrase):
            edge = Edge(chart.chart_i-1, chart.chart_i, prod, prod.rhs_len)
            current_lexicon_progressed_by_grammar = True
            if chart.add_edge(edge, None, None, lexicon=phrase):
                agenda.append(edge)
        return current_lexicon_progressed_by_grammar


class TopDownPredictRule(ChartRule):
    """
    Predict edge if it's not complete and add it to chart
    """
    NUM_EDGES = 1

    def apply(self, chart, grammar, agenda, edge, phrase):
        if edge.is_complete():
            return False
        if edge.end + 1 != chart.chart_i:
            return False
        rhs = edge.get_rhs_after_dot()
        if rhs.is_terminal:  # critical: saves 20% computing time
            return False
        for prod in grammar.filter_productions_for_prediction_by_lhs(rhs):
            # no lookahead, just add everything
            predicted_edge = Edge(edge.end, edge.end, prod, 0)
            if chart.add_edge(predicted_edge, None, None):
                agenda.append(predicted_edge)
        return False


class LeftCornerPredictScanRule(ChartRule):
    """
    Left corner rules: only add productions whose left corner non-terminal
    can parse the lexicon.
    """
    NUM_EDGES = 1

    def apply(self, chart, grammar, agenda, edge, phrase):
        if edge.is_complete():
            return False
        rhs = edge.get_rhs_after_dot()
        productions = set()
        if rhs.is_terminal:
            productions.add(grammar.terminal2prod[rhs])
        else:
            productions.update(grammar.nonterminal2prod[rhs])
        current_lexicon_progressed_by_grammar = False

        for prod in productions:
            for term in grammar.get_left_corner_terminals(prod):
                progress = False
                try:
                    progress = term.lhs.parse(phrase)
                except ParseException:
                    pass

                if progress:
                    current_lexicon_progressed_by_grammar = True
                    edge = Edge(chart.chart_i-1, chart.chart_i, term,
                                term.rhs_len)
                    if chart.add_edge(edge, None, None, lexicon=phrase):
                        agenda.append(edge)

                    # Prediction
                    if prod.is_terminal:  # don't predict terminal
                        continue
                    for nonterm in grammar.get_left_corner_nonterminals(prod):
                        if term in grammar.get_left_corner_terminals(nonterm):
                            # just add, then let CompleteRule finish the edge
                            predicted_edge = Edge(chart.chart_i-1,
                                                  chart.chart_i-1, nonterm, 0)
                            if chart.add_edge(predicted_edge, None, None):
                                agenda.append(predicted_edge)
        return current_lexicon_progressed_by_grammar


class BottomUpPredictRule(ChartRule):
    """
    In bottom up parsing, predict edge if it's not complete and add it to chart
    """
    NUM_EDGES = 1

    def apply(self, chart, grammar, agenda, edge, phrase):
        if not edge.is_complete():
            return False
        # Predict with completed
        for production in grammar.\
                filter_productions_for_prediction_by_rhs(edge.prod.lhs):
            # no lookahead, just add everything
            predicted_edge = Edge(edge.start, edge.start, production, 0)
            if chart.add_edge(predicted_edge, None, None):
                agenda.append(predicted_edge)
        return False


class TopDownScanRule(ChartRule):
    """
    Scan lexicon from top down
    """
    NUM_EDGES = 1

    def apply(self, chart, grammar, agenda, edge, phrase):
        if edge.is_complete():
            return False
        if edge.end + 1 != chart.chart_i:
            return False
        lex_progress, rhs_progress = edge.scan_after_dot(phrase)
        if lex_progress:
            prod = grammar.terminal2prod[edge.prod.rhs[edge.dot]]

            scanned_edge = Edge(chart.chart_i-1, chart.chart_i,
                                prod, prod.rhs_len)
            if chart.add_edge(scanned_edge, None, None, phrase):
                agenda.append(scanned_edge)
            return True
        else:
            return False


class CompleteRule(ChartRule):
    """
    Complete an incomplete edge form the agenda by merging with a matching
    completed edge from the chart, or complete an incomplete edge from the
    chart by merging with a matching completed edge from the agenda.
    """
    NUM_EDGES = 1

    def apply_complete(self, edge, chart, agenda):
        for filtered_edge in chart.filter_edges_for_completion(
                end=edge.start, rhs_after_dot=edge.prod.lhs):

            # print("filtered edge", str(filtered_edge))
            moved_edge = filtered_edge.merge_and_forward_dot(edge)
            # print("moved edge", str(moved_edge))
            if edge != moved_edge:
                if chart.add_edge(moved_edge, filtered_edge, edge):
                    agenda.append(moved_edge)

    def apply_incomplete(self, edge, chart, agenda):
        for filtered_edge in chart.filter_completed_edges(
                start=edge.end, lhs=edge.prod.rhs[edge.dot]):

            moved_edge = edge.merge_and_forward_dot(filtered_edge)
            if edge != moved_edge:
                added = chart.add_edge(moved_edge, edge, filtered_edge)
                if added:
                    agenda.append(moved_edge)

    def apply(self, chart, grammar, agenda, edge, phrase):
        if edge.is_complete():
            self.apply_complete(edge, chart, agenda)
        else:
            self.apply_incomplete(edge, chart, agenda)
        return False


# ############## Parsing Strategies ##############

class ParsingStrategy(object):
    """
    Parsing strategy used in TopDown, BottomUp, LeftCorner parsing. Each
    strategy consists of a list of various :class:`ChartRules`'s.
    """
    def __init__(self, rule_list):
        self.init_rules = []
        self.edge_rules = []
        for rule in rule_list:
            if rule.NUM_EDGES == 0:
                self.init_rules.append(rule)
            elif rule.NUM_EDGES == 1:
                self.edge_rules.append(rule)
            else:
                raise ValueError("Rules with NUM_EDGES > 1 not supported" +
                                 str(rule))

    def is_leftcorder(self):
        return any(type(r) is LeftCornerPredictScanRule
                   for r in self.edge_rules)


TopDownStrategy = ParsingStrategy([
    TopDownInitRule(),
    TopDownScanRule(),
    TopDownPredictRule(),
    CompleteRule()
])
"""Top-down parsing strategy"""


BottomUpStrategy = ParsingStrategy([
    # we can consider adding EmptyPredictRule for Null element
    # but need to consider whether it's doable for Top Down
    BottomUpScanRule(),
    BottomUpPredictRule(),
    CompleteRule()
])
"""Bottom-up parsing strategy"""


LeftCornerStrategy = ParsingStrategy([
    TopDownInitRule(),
    LeftCornerPredictScanRule(),
    CompleteRule()
])
"""Top-down left corner parsing strategy to speed up top-down strategy"""


class RobustParser(object):
    """
    A robust, incremental chart parser.

    :param grammar: user defined grammar, a :class:`GrammarImpl` type.
    :param ParsingStrategy strategy: top-down or bottom-up parsing
    """
    def __init__(self, grammar, strategy=LeftCornerStrategy):
        self.logger = logging.getLogger(__name__)
        self.goal = grammar.goal
        self.grammar = grammar

        # for incremental parsing:
        self.to_be_parsed = []
        self.accepted_tokens = []
        self.chart = None
        self.strategy = strategy
        if strategy.is_leftcorder():
            self.grammar.build_leftcorner_table()

    def clear_cache(self):
        """
        Clear all history when the parser is to parse another sentence. Mainly
        used in server mode for incremental parsing
        """
        self.to_be_parsed = []
        self.accepted_tokens = []
        self.chart = None

    def parse_to_chart(self, string):
        """
        Parse a whole sentence into a chart and parsed tokens.
        This gives a raw chart where all trees or the single best tree can
        be drawn from.

        :param str string: input sentence that's already tokenized.
        :return: parsing chart and newly parsed tokens
        :rtype: tuple(:class:`Chart`, list(str))
        """
        return self.parse_multi_token_skip_reuse_chart(string)

    def incremental_parse_to_chart(self, single_token, chart):
        """
        Incremental parsing one token each time. Returns
        (chart, is_token_accepted).

        :param str single_token: a single word
        :param RobustChart chart: the previous returned chart. On first call,
                      set it to None.
        :return: a tuple of (chart, parsed_tokens)
        """
        if chart is None:
            self.to_be_parsed = []
        self.to_be_parsed.append(single_token)
        num = len(self.to_be_parsed)

        # "please turn off"
        # please -> no parse, save ["please"]
        # please turn ->
        # -> "please turn" no parse
        #   -> "turn" no parse
        #   -> save ["please turn"]
        # please turn off ->
        #   -> "please turn off" no parse, save it
        #   -> "turn off" parse, return, save []
        progress = 0
        is_parsed = False
        parsed_tokens = []
        while progress < num and not is_parsed:
            single_list = [" ".join(self.to_be_parsed[progress:])]
            (chart, parsed_tokens) = self._parse_multi_token(
                single_list, chart)
            is_parsed = len(parsed_tokens) > 0
            if is_parsed:
                self.to_be_parsed = []
            progress += 1

        return chart, parsed_tokens

    def incremental_parse(self, single_token, is_final, only_goal=True):
        """
        Incremental parsing one token each time. Returns the best parsing tree
        and parse result.

        :param str single_token: a single word
        :param bool is_final: whether the current `single_token` is the last
            one in sentence.
        :param bool only_goal: only output trees with GOAL as root node
        :return: (best parse tree, parse result)
        :rtype: tuple(:class:`TreeNode`, :class:`ParseResult`) or (None, None)
        """
        try:
            self.chart, parsed_tokens = self.incremental_parse_to_chart(
                single_token, self.chart)
            if len(parsed_tokens) > 0:
                self.accepted_tokens.extend(parsed_tokens)
            goal = self.goal if only_goal else None
            trees = list(self.chart.trees(self.accepted_tokens,
                                          all_trees=False, goal=goal))
            tree, result = self.chart.best_tree_with_parse_result(trees)
            if is_final:
                self.accepted_tokens = []
                self.chart = None
            return tree, result
        except ParseException:
            if is_final:
                self.accepted_tokens = []
                self.chart = None
            return None, None

    def print_incremental_parse(self, sent):
        string = strip_string(sent)
        tokens = string.split()
        chart = None
        accepted_tokens = []
        num = len(tokens)
        for i in xrange(num):
            token = tokens[i]
            (chart, parsed_tokens) = self.incremental_parse_to_chart(
                token, chart)
            if len(parsed_tokens) > 0:
                accepted_tokens.extend(parsed_tokens)
            print("tokens so far:", " ".join(tokens[0:i + 1]))
            print("parsed tokens:", " ".join(accepted_tokens))
            print("parse tree so far:")
            try:
                trees = list(chart.trees(accepted_tokens,
                                         all_trees=False, goal=None))
                best_tree, best_parse = chart.best_tree_with_parse_result(
                    trees)
                print(best_tree)
            except ParseException:
                pass
            print()

    def parse_multi_token_skip_reuse_chart(self, sent):
        """
        Parse sentence with capabilities to:

            - *multi_token*: recognize multiple tokens as one phrase
                (e.g., "turn off")
            - *skip*: throw away tokens not licensed by grammar (e.g.,
                speech fillers "um...")
            - *reuse_chart*: doesn't waste computation by reusing the chart
                from last time. This makes the function call up to 25% faster
                than without reusing the chart.

        :param str sent: a sentence in string
        :return: the chart and the newly parsed tokens
        :rtype: tuple(:class:`Chart`, list(str))
        """
        string = strip_string(sent)
        if len(string) == 0:
            raise ParseException("input string is empty")
        tokens = string.split()
        to_be_parsed = tokens[:]
        all_parsed_tokens = []

        chart, parsed_tokens = None, None

        # "I want to turn off the lights please"
        while True and len(to_be_parsed) > 0:
            (chart, parsed_tokens) = self._parse_multi_token(
                to_be_parsed, chart)

            # items in parsed_tokens could be multi-token: ["turn off"]
            ret_len_in_single_tokens = sum([len(t.split())
                                            for t in parsed_tokens])

            if ret_len_in_single_tokens == 0:
                # can't parse, skip the first token
                to_be_parsed.pop(0)
            elif ret_len_in_single_tokens == len(to_be_parsed):
                all_parsed_tokens += parsed_tokens
                break  # have a parse
            else:  # partial parse
                # pop out the token where the chart stopped at
                # and try once again
                all_parsed_tokens += parsed_tokens
                to_be_parsed = to_be_parsed[ret_len_in_single_tokens + 1:]

        if not self.logger.disabled and chart:
            self.logger.debug("Chart:")
            self.logger.debug(chart)
            self.logger.debug("\nBackpointers:")
            self.logger.debug(chart.print_backpointers())
            self.logger.debug("\n")
        return chart, all_parsed_tokens

    # ####### Main Parsing Routin ########

    def _parse_single_token(self, agenda, chart, phrase):
        progressed = False
        for rule in self.strategy.init_rules:
            progressed |= rule.apply(chart, self.grammar, agenda, phrase)

        while len(agenda) > 0:
            edge = agenda.pop()
            for rule in self.strategy.edge_rules:
                progressed |= rule.apply(chart, self.grammar, agenda, edge,
                                         phrase)
        return progressed

    def _parse_multi_token(self, sent_or_tokens, chart=None):
        """
        Parse sentences while being able to tokenize multiple tokens,
        for instance:

            kill lights -> "kill" "lights"
            turn off lights -> "turn off" "lights"

        Each quotes-enclosed (multi-)token is recognized as a phrase.

        This function doesn't parse unrecognizable tokens.
        """

        if isinstance(sent_or_tokens, basestring):
            string = strip_string(sent_or_tokens)
            tokens = string.split()
        elif type(sent_or_tokens) is list:
            tokens = sent_or_tokens
        else:
            raise TypeError("input should either be a string or list: " +
                            str(sent_or_tokens))
        length = len(tokens)
        if length == 0:
            raise ValueError("input string is empty!")

        agenda = Agenda()

        if chart is None:
            chart = IncrementalChart()
        if chart.size == 0:
            chart.chart_i = 0

        else:  # continue from where we were left behind
            chart.chart_i = chart.size - 1

        new_tokens = []

        # whether this word is covered in grammar
        progressed = False
        phrase_start = 0
        phrase_end = 0
        while phrase_end < length:

            if progressed or phrase_end == 0:
                chart.chart_i += 1
                phrase_start = phrase_end
                phrase_end += 1
            else:
                # try a longer phrase by fixing phrase_start and increasing
                # phrase_end
                phrase_end += 1

            phrase = " ".join(tokens[phrase_start: phrase_end])

            progressed = self._parse_single_token(agenda, chart, phrase)

            if progressed:
                new_tokens.append(phrase)

        if not self.logger.disabled:
            self.logger.debug("Agenda total: %d" % agenda.total)
        return chart, new_tokens

    def parse_string(self, string):
        """
        alias of :func:`parse`.
        """
        chart, tokens = self.parse_to_chart(string)
        try:
            trees = list(chart.trees(tokens, all_trees=False, goal=self.goal))
            best_tree, best_parse = chart.best_tree_with_parse_result(trees)
            return best_tree, best_parse
        except ParseException:
            print("can't parse:", string, file=sys.stderr)
            return None, None

    def parse(self, string):
        """
        Parse an input sentence in ``string`` and return the best
        (tree, result).

        :param string: tokenized input
        :return: (best tree, best parse)
        :rtype: tuple(:class:`TreeNode`, :class:`ParseResult`)
        """
        return self.parse_string(string)

    def print_parse(self, string, all_trees=False, only_goal=True,
                    best_parse=True, print_json=False,
                    strict_match=False):
        """
        Print the parse tree given input ``string``.

        :param str string: input string
        :param bool all_trees: whether to print all trees (warning: massive
            output)
        :param bool only_goal: only print the tree licensed by final goal
        :param bool best_parse: print the best one tree ranked by the smallest
            size
        :param bool strict_match: strictly matching input with parse output
            (for test purposes)
        :return: True if there is a parse else False
        """
        print(string)
        try:
            chart, tokens = self.parse_to_chart(string)
            trees = list(chart.trees(tokens, all_trees,
                                     goal=self.goal if only_goal else None))
            if len(trees) == 0:
                raise ParseException("No parse trees found")
        except ParseException:
            print("can't parse:", string, file=sys.stderr)
            return False

        if not best_parse:
            for i, tree in trees:
                print(i)
                if print_json:
                    print(json.dumps(tree.dict_for_js(), indent=2))
                else:
                    print(tree)
                print("size:", tree.size())
                print()
            print("total trees:", len(trees))
        else:
            best_tree, best_parse = chart.best_tree_with_parse_result(trees)
            print("best tree:")
            if print_json:
                print(json.dumps(best_tree.dict_for_js(), indent=2))
            else:
                print(best_tree)
                print(best_parse)
            print("total trees:", len(trees))
        print()

        if strict_match:
            if string == " ".join(tokens):
                return True
            else:
                return False
        else:
            return True


def strip_string(string):
    """
    Merge spaces into single space
    """
    return re.sub('[\t\s]+', ' ', string).strip()


def find_word_boundaries(string):
    """
    Given a string, such as "my lights are off", return a tuple::

        0: a list containing all word boundaries in tuples
        (start(inclusive), end(exclusive)):
        [(0, 2), (3, 9), (10, 13), (14, 17)]
        1: a set of all start positions: set[(0, 3, 10, 14)]
        2: a set of all end positions: set[(2, 9, 13, 17)]

    """
    start, end, last_end = 0, 0, -1
    boundaries = []
    while end != -1:
        end = string.find(" ", start)
        if end != -1:
            boundaries.append((start, end))
            last_end = end
        start = last_end + 1
    start, end = start, len(string)
    if end > start:
        boundaries.append((start, end))
    if len(boundaries) > 0:
        starts, ends = zip(*boundaries)
        starts, ends = set(starts), set(ends)
    else:
        starts, ends = set(), set()
    return boundaries, starts, ends
