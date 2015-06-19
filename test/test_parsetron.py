from parsetron import *  # NOQA
import re
import pytest

__author__ = 'Xuchen Yao'


class TestMul(object):

    def test_mul(self):
        s = String("t")('t')

        # valid grammar:
        class G(Grammar):
            GOAL = s * 1
        s_1 = RobustParser(G())
        assert s_1.print_parse("t", strict_match=True)
        assert False is s_1.print_parse("t t", strict_match=True)

        class G(Grammar):
            GOAL = s * (1, 2)
        s_1_2 = RobustParser(G())
        assert s_1_2.print_parse("t", strict_match=True)
        assert s_1_2.print_parse("t t", strict_match=True)
        assert False is s_1_2.print_parse("t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [1, ]
        s_1_none = RobustParser(G())
        assert s_1_none.print_parse("t", strict_match=True)
        assert s_1_none.print_parse("t t", strict_match=True)
        assert s_1_none.print_parse("t t t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [1, None]
        s_1_none_a = RobustParser(G())
        assert s_1_none_a.print_parse("t", strict_match=True)
        assert s_1_none_a.print_parse("t t", strict_match=True)
        assert s_1_none_a.print_parse("t t t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [3, ]
        s_3_none = RobustParser(G())
        assert False is s_3_none.print_parse("t", strict_match=True)
        assert False is s_3_none.print_parse("t t", strict_match=True)
        assert s_3_none.print_parse("t t t", strict_match=True)
        assert s_3_none.print_parse("t t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [3, None]
        s_3_none_a = RobustParser(G())
        assert False is s_3_none_a.print_parse("t", strict_match=True)
        assert False is s_3_none_a.print_parse("t t", strict_match=True)
        assert s_3_none_a.print_parse("t t t", strict_match=True)
        assert s_3_none_a.print_parse("t t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [None, 1]
        s_none_1 = RobustParser(G())
        assert s_none_1.print_parse("t", strict_match=True)

        class G(Grammar):
            GOAL = s * [None, 3]
        s_none_3 = RobustParser(G())
        assert s_none_3.print_parse("t", strict_match=True)
        assert s_none_3.print_parse("t t", strict_match=True)
        assert s_none_3.print_parse("t t t", strict_match=True)
        assert False is s_none_3.print_parse("t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [0, 1]
        s_0_1 = RobustParser(G())
        assert s_0_1.print_parse("t", strict_match=True)
        assert False is s_0_1.print_parse("a", strict_match=True)

        class G(Grammar):
            GOAL = s * [0, None]
        s_0_1 = RobustParser(G())
        assert s_0_1.print_parse("t", strict_match=True)
        assert False is s_0_1.print_parse("a", strict_match=True)

        class G(Grammar):
            GOAL = s * [0, 1] + "b"
        s_0_1 = RobustParser(G())
        assert s_0_1.print_parse("t b", strict_match=True)
        assert s_0_1.print_parse("b")

        class G(Grammar):
            GOAL = s * [0, 3]
        s_0_3 = RobustParser(G())
        assert s_0_3.print_parse("t", strict_match=True)
        assert s_0_3.print_parse("t t", strict_match=True)
        assert s_0_3.print_parse("t t t", strict_match=True)
        assert False is s_0_3.print_parse("t t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [3, 5]
        s_3_5 = RobustParser(G())
        assert False is s_3_5.print_parse("t t", strict_match=True)
        assert s_3_5.print_parse("t t t", strict_match=True)
        assert s_3_5.print_parse("t t t t", strict_match=True)
        assert s_3_5.print_parse("t t t t t", strict_match=True)
        assert False is s_3_5.print_parse("t t t t t t", strict_match=True)

        class G(Grammar):
            GOAL = s * [3, 3]
        s_3_3 = RobustParser(G())
        assert False is s_3_3.print_parse("t t", strict_match=True)
        assert s_3_3.print_parse("t t t", strict_match=True)
        assert False is s_3_3.print_parse("t t t t", strict_match=True)

        # invalid grammar:
        with pytest.raises(ValueError):
            s * [3, 2]
        with pytest.raises(ValueError):
            s * (3, 2)
        with pytest.raises(ValueError):
            s * 3.0
        with pytest.raises(ValueError):
            s * [3.0, 4]
        with pytest.raises(ValueError):
            s * (3, 4.5)
        with pytest.raises(ValueError):
            s * None
        with pytest.raises(ValueError):
            s * 0
        with pytest.raises(ValueError):
            s * -1
        with pytest.raises(ValueError):
            s * [-1, 3]
        with pytest.raises(ValueError):
            s * [-1, None]
        with pytest.raises(ValueError):
            s * [1, -1]
        with pytest.raises(ValueError):
            s * [None, -1]
        with pytest.raises(ValueError):
            s * [1, 2, 3]


class TestString(object):
    def test_empty_init(self):
        with pytest.raises(ValueError):
            String("")

    def test_parse(self):
        s = StringCs("hello")
        assert s.parse("hello")
        with pytest.raises(ParseException):
            s.parse("Hello")
        with pytest.raises(ParseException):
            s.parse("")
        with pytest.raises(ParseException):
            s.parse("helloo")
        with pytest.raises(ParseException):
            s.parse("hell")


class TestRegex(object):
    def test_empty_init(self):
        with pytest.raises(ValueError):
            Regex("")

    def test_equal(self):
        assert Regex("ab") == "ab"
        assert Regex("ab") == "AB"
        assert Regex("ab") != "ac"
        assert Regex("ab") != 1

    def test_parse(self):
        r = Regex(r"(ab|bc)")
        repr(r)
        assert r.parse("ab")
        assert r.parse("bc")
        with pytest.raises(ParseException):
            assert r.parse("cd")
        with pytest.raises(ParseException):
            assert r.parse("abc")
        r1 = Regex("ab", match_whole=True)
        with pytest.raises(ParseException):
            assert r1.parse("abc")
        r2 = Regex(re.compile("ab"))
        r2.parse("ab")
        with pytest.raises(ValueError):
            Regex(12)
        r3 = Regex("ab", match_whole=False)
        r3.parse("abc")


class TestSet(object):
    def test_parse(self):
        with pytest.raises(ValueError):
            Set(123)
        s1 = Set("a b c")
        s2 = Set(["a", "b", "c"])
        s3 = Set({"a", "b", "c"})
        s4 = Set("abc")
        for s in [s1, s2, s3, s4]:
            s.parse("A")
            s.parse("B")
            s.parse("C")
            with pytest.raises(ParseException):
                s.parse("d")

    def test_parse_casesensitive(self):
        s1 = SetCs("a b c")
        s2 = SetCs(["a", "b", "c"])
        s3 = SetCs({"a", "b", "c"})
        s4 = SetCs("abc")
        for s in [s1, s2, s3, s4]:
            s.parse("a")
            s.parse("b")
            s.parse("c")
            with pytest.raises(ParseException):
                s.parse("A")


class TestAnd(object):
    def test_plus(self):
        a = String("1") + Optional(String("1"))
        assert len(a.exprs) == 2
        a += Regex("3")
        assert len(a.exprs) == 3
        b = "1" + a
        assert len(b.exprs) == 2
        b += "3"
        assert len(b.exprs) == 3
        assert b[0].str == "1"

    def test_streamline(self):
        a = String("1") + Optional(String("1"))
        b = String("1") + Optional(String("1"))
        c = a + b
        with pytest.raises(GrammarException):
            c.parse("1 1")


class TestOr(object):
    def test_or(self):
        a = String("1") | Optional(String("1"))
        assert len(a.exprs) == 2
        a |= Regex("3")
        assert len(a.exprs) == 3
        a |= String("4") + Optional(String("4"))
        assert len(a.exprs) == 4
        a |= "3"
        assert len(a.exprs) == 5

        with pytest.raises(GrammarException):
            print(a | 3.3)


class TestStr(object):
    def test_str(self):
        s = String("a string")
        assert str(s) == "String(a string)"
        o = Optional("a string")
        assert str(o) == "Optional(String(a string))"
        r = Regex(r"abc")('regex')
        assert str(r) == 'regex'
        r1 = r.set_name('xeger')
        assert str(r1) == 'xeger'


class TestGrammar(object):
    class LightGrammar(Grammar):
        light_general = String("light")
        action = Regex(r"(turn on|turn off|off|blink)")
        times = Regex(r"(once|twice|three times)")
        optional_times = Optional(times)
        one_more_light = OneOrMore(light_general)
        zero_more_action = ZeroOrMore(action)
        GOAL = zero_more_action + optional_times + one_more_light + \
            optional_times + OneOrMore(String("quickly")('quick'))

    def test_constructor(self):
        assert 2 == len(GrammarExpression(["1", "2"]).exprs)
        assert 1 == len(GrammarExpression("2").exprs)
        with pytest.raises(GrammarException):
            GrammarExpression(1)

    def test_grammar_str(self):
        light = TestGrammar.LightGrammar()
        repr(light)
        assert light.name == "LightGrammar"
        print(light)
        parser = RobustParser(light)
        parser_bu = RobustParser(light, BottomUpStrategy)
        # TODO: this semantics is NOT tesing "grammar"
        assert True == parser.print_parse("blink light light light quickly")
        assert True == parser_bu.print_parse("blink light light light quickly")
        assert True == parser.print_parse("light quickly")
        assert True == parser_bu.print_parse("light quickly")

    def test_reserved(self):
        with pytest.raises(GrammarException):
            class ReservedGrammar(Grammar):
                _grammar_ = "reserved"
                GOAL = _grammar_
            ReservedGrammar()

    def test_goal(self):
        with pytest.raises(GrammarException):
            class NoGoalGrammar(Grammar):
                random = 'random'
            NoGoalGrammar()

    def test_test(self):
        with pytest.raises(NotImplementedError):
            TestGrammar.LightGrammar.test()


class TestZeroOrMore(object):
    def test_or(self):
        class OrGrammar(Grammar):
            GOAL = "1" | ZeroOrMore("1")
        p = RobustParser(OrGrammar())
        p.parse("1 1")


class TestParser(object):
    class LightGrammar(Grammar):
        def times2int(r):
            if r.get() == "once":
                r.set(1)
            elif r.get() == "twice":
                r.set(2)
            elif r.get() == "three times":
                r.set(3)

        light = String("light").ignore()
        color = String("red").replace_result_with((255, 0, 0))
        action = Regex(r"(turn on|turn off|off|blink)")
        times = Regex(r"(once|twice|three times)").set_result_action(times2int)
        GOAL = action + Optional(color) + light + Optional(times) + \
            String("quickly")('quick')
    light = LightGrammar()
    parser = RobustParser(light)
    test_str = "blink red light once quickly ignore"

    def test_parse(self):
        parser = TestParser.parser
        test_str = TestParser.test_str
        assert True == parser.print_parse(test_str, print_json=True)
        assert True == parser.print_parse(test_str, best_parse=False)
        assert True == parser.print_parse(
            test_str, best_parse=False, print_json=True)
        assert (None, None) == parser.parse("can't parse")
        assert (None, None) == parser.parse_string("can't parse")

        t, r = parser.parse(test_str)
        # test result
        assert r.times == 1
        assert r.color == (255, 0, 0)
        print(repr(r))  # test __repr__()
        assert 'quickly' in r.values()
        assert 'quick' in r.keys()
        del r['quick']
        assert 'quick' not in r.keys()
        r.quick = 'quickly'
        assert 'quickly' in r.values()
        del r.quick
        assert 'quick' not in r
        r['quick'] = 'quickly'
        assert 'quickly' == r.get('quick')
        assert 'light' not in r

        # test tree
        d = t.get_flat_dict(key='GOAL', only_leaf=True)
        assert 'action' in d[0]
        d = t.get_flat_dict(key='GOAL', only_leaf=False)
        assert 'action' in d[0]
        d = t.get_flat_dict(key='action', only_leaf=False)
        assert 'action' in d[0]
        TreeNode.recursive_str_verbose(t)

        with pytest.raises(ParseException):
            parser.parse("")
        with pytest.raises(ValueError):
            parser._parse_multi_token("")
        _, tokens = parser._parse_multi_token("can't parse")
        assert len(tokens) == 0
        with pytest.raises(TypeError):
            parser._parse_multi_token(1)

    def test_incremental_parse(self):
        parser = TestParser.parser
        test_str = TestParser.test_str
        parser.print_incremental_parse(test_str)

        assert (None, None) == parser.incremental_parse('blink', False)
        assert (None, None) == parser.incremental_parse('light', False)
        t, r = parser.incremental_parse('quickly', is_final=True)
        assert t is not None
        assert (None, None) == parser.incremental_parse('light', is_final=True)
        parser.clear_cache()

    def test_num_edges(self):
        class BadRule(ChartRule):
            NUM_EDGES = 2

        with pytest.raises(ValueError):
            ParsingStrategy([BadRule])
        with pytest.raises(NotImplementedError):
            BadRule().apply()

#     def test_full_trees(self):
#         class CatalanGrammar(Grammar):
#             a = String("a")
#             A = NULL | a
#             A |= A + A
#             GOAL = A
#         p = RobustParser(CatalanGrammar(), TopDownStrategy)
#         chart, tokens = p.parse_to_chart("a a a a")
#         trees = list(chart.trees(tokens,
#                                  all_trees=True,
#                                  goal=CatalanGrammar.GOAL))
#         assert len(trees) == 5

    def test_full_trees(self):
        class FullGrammar(Grammar):
            a = String("a")
            b = String("a")
            GOAL = a + b | b + a | a + a | b + b
        p = RobustParser(FullGrammar(), TopDownStrategy)
        chart, tokens = p.parse_to_chart("a a")
        trees = list(chart.trees(tokens,
                                 all_trees=True,
                                 goal=FullGrammar.GOAL))
        print(chart)  # test chart __str__()
        assert len(trees) == 4


def test_topdown_init_rule():
    class CornerGrammar(Grammar):
        GOAL = String("a") + String("b")
    p = RobustParser(CornerGrammar(), TopDownStrategy)
    assert (None, None) == p.parse("b")
    t, _ = p.parse("a b")
    assert t is not None
    assert (None, None) == p.parse("b a")


class TestOptional(object):
    def test_o2(self):
        class OptionalGrammar(Grammar):
            s = String("t")('t')
            o1 = Optional(s)
            o2 = Optional(o1)
            GOAL = s + o2
        parser = RobustParser(OptionalGrammar(), strategy=TopDownStrategy)
        assert True == parser.print_parse("t t")
        assert True == parser.print_parse("t")
        OptionalGrammar.o2.parse("t")

    def test_o3(self):
        class OptionalGrammar(Grammar):
            s = String("t")('t')
            o3 = Optional(Optional(s))
            GOAL = s + o3
        parser = RobustParser(OptionalGrammar(), strategy=BottomUpStrategy)
        assert True == parser.print_parse("t t")
        assert True == parser.print_parse("t")


class TestNullAnd(object):
    def test_o2(self):
        class OptionalGrammar(Grammar):
            s = String("t")('t')
            o1 = Optional(s)
            o2 = ZeroOrMore(s)
            o3 = o1 + o2
            GOAL = s + o3
        parser = RobustParser(OptionalGrammar(), strategy=TopDownStrategy)
        assert True == parser.print_parse("t t")
        # known bug, FIXME
        assert False == parser.print_parse("t")


class TestDocGrammar(object):
    def test_o2(self):
        class LightGrammar(Grammar):
            action = Set(['change', 'flash', 'set', 'blink'])
            light = Set(['top', 'middle', 'bottom'])
            color = Regex(r'(red|yellow|blue|orange|purple|...)')
            times = Set(['once', 'twice', 'three times']) | Regex(r'\d+ times')
            one_parse = action + light + Optional(times) + color
            GOAL = OneOrMore(one_parse)
        parser = RobustParser(LightGrammar(), strategy=TopDownStrategy)
        # assert parser.print_parse("set my top light to red")
        # assert parser.print_parse("set my top light to red and change "
        #                                   "middle light to yellow")
        # assert parser.print_parse("set my top light to red and change "
        #     "middle light to yellow and flash bottom light twice in blue")

        sents = [
            "set my top light to red",
            "set my top light to red and change middle light to yellow",
            "set my top light to red and change middle light to yellow and "
            "flash bottom light twice in blue"
        ]
        for sent in sents:
            tree, result = parser.parse_string(sent)
            print('"%s"' % sent)
            print("parse tree:")
            print(tree)
            print("parse result:")
            print(result)
            assert type(result.one_parse) is list
            print()


def test_find_word_boundaries():
    boundaries, starts, ends = find_word_boundaries(strip_string(
        "my lights are off"))
    assert boundaries == [(0, 2), (3, 9), (10, 13), (14, 17)]
    assert [0, 3, 10, 14] == sorted(list(starts))
    assert [2, 9, 13, 17] == sorted(list(ends))
    boundaries, starts, ends = find_word_boundaries(strip_string(""))
    assert len(boundaries) == 0
    assert len(starts) == 0
    assert len(ends) == 0
