from parsetron import *
import pytest

__author__ = 'Xuchen Yao'


# @pytest.mark.skipif(True, reason="")
class TestMul(object):
    def test_mul(self):
        s = String("t")('t')
        # valid grammar:
        class G(Grammar): GOAL = s * 1
        s_1 = RobustParser(G())
        assert s_1.print_parse("t", strict_match=True)
        assert False is s_1.print_parse("t t", strict_match=True)

        class G(Grammar): GOAL = s * (1, 2)
        s_1_2 = RobustParser(G())
        assert s_1_2.print_parse("t", strict_match=True)
        assert s_1_2.print_parse("t t", strict_match=True)
        assert False is s_1_2.print_parse("t t t", strict_match=True)

        class G(Grammar): GOAL = s * [1,]
        s_1_none = RobustParser(G())
        assert s_1_none.print_parse("t", strict_match=True)
        assert s_1_none.print_parse("t t", strict_match=True)
        assert s_1_none.print_parse("t t t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [1, None]
        s_1_none_a = RobustParser(G())
        assert s_1_none_a.print_parse("t", strict_match=True)
        assert s_1_none_a.print_parse("t t", strict_match=True)
        assert s_1_none_a.print_parse("t t t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [3,]
        s_3_none = RobustParser(G())
        assert False is s_3_none.print_parse("t", strict_match=True)
        assert False is s_3_none.print_parse("t t", strict_match=True)
        assert s_3_none.print_parse("t t t", strict_match=True)
        assert s_3_none.print_parse("t t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [3, None]
        s_3_none_a = RobustParser(G())
        assert False is s_3_none_a.print_parse("t", strict_match=True)
        assert False is s_3_none_a.print_parse("t t", strict_match=True)
        assert s_3_none_a.print_parse("t t t", strict_match=True)
        assert s_3_none_a.print_parse("t t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [None, 1]
        s_none_1 = RobustParser(G())
        assert s_none_1.print_parse("t", strict_match=True)

        class G(Grammar): GOAL = s * [None, 3]
        s_none_3 = RobustParser(G())
        assert s_none_3.print_parse("t", strict_match=True)
        assert s_none_3.print_parse("t t", strict_match=True)
        assert s_none_3.print_parse("t t t", strict_match=True)
        assert False is s_none_3.print_parse("t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [0, 1]
        s_0_1 = RobustParser(G())
        assert s_0_1.print_parse("t", strict_match=True)
        assert False is s_0_1.print_parse("a", strict_match=True)

        class G(Grammar): GOAL = s * [0, 1] + "b"
        s_0_1 = RobustParser(G())
        assert s_0_1.print_parse("t b", strict_match=True)
        assert s_0_1.print_parse("b")

        class G(Grammar): GOAL = s * [0, 3]
        s_0_3 = RobustParser(G())
        assert s_0_3.print_parse("t", strict_match=True)
        assert s_0_3.print_parse("t t", strict_match=True)
        assert s_0_3.print_parse("t t t", strict_match=True)
        assert False is s_0_3.print_parse("t t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [3, 5]
        s_3_5 = RobustParser(G())
        assert False is s_3_5.print_parse("t t", strict_match=True)
        assert s_3_5.print_parse("t t t", strict_match=True)
        assert s_3_5.print_parse("t t t t", strict_match=True)
        assert s_3_5.print_parse("t t t t t", strict_match=True)
        assert False is s_3_5.print_parse("t t t t t t", strict_match=True)

        class G(Grammar): GOAL = s * [3, 3]
        s_3_3 = RobustParser(G())
        assert False is s_3_3.print_parse("t t", strict_match=True)
        assert s_3_3.print_parse("t t t", strict_match=True)
        assert False is s_3_3.print_parse("t t t t", strict_match=True)

        # invalid grammar:
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * [3, 2]
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * (3, 2)
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * 3.0
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * (3, 4.5)
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * None
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * 0
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * -1
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * [-1, 3]
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * [-1, None]
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * [1, -1]
        with pytest.raises(ValueError):
            class G(Grammar): GOAL = s * [None, -1]


# @pytest.mark.skipif(True, reason="")
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


# @pytest.mark.skipif(True, reason="")
class TestRegex(object):
    def test_empty_init(self):
        with pytest.raises(ValueError):
            String("")

    def test_parse(self):
        r = Regex(r"(ab|bc)")
        assert r.parse("ab")
        assert r.parse("bc")
        with pytest.raises(ParseException):
            assert r.parse("cd")


# @pytest.mark.skipif(True, reason="")
class TestAnd(object):
    def test_plus(self):
        a = String("1") + Optional(String("1"))
        assert len(a.exprs) == 2
        a += Regex("3")
        assert len(a.exprs) == 3


# @pytest.mark.skipif(True, reason="")
class TestOr(object):
    def test_or(self):
        a = String("1") | Optional(String("1"))
        assert len(a.exprs) == 2
        a |= Regex("3")
        assert len(a.exprs) == 3
        a |= String("4") + Optional(String("4"))
        assert len(a.exprs) == 4


# @pytest.mark.skipif(True, reason="")
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


# @pytest.mark.skipif(True, reason="")
class TestGrammar(object):
    def test_grammar_str(self):
        class LightGrammar(Grammar):
            light_general = String("light")
            action = Regex(r"(turn on|turn off|off|blink)")
            times = Regex(r"(once|twice|three times)")
            optional_times = Optional(times)
            one_more_light = OneOrMore(light_general)
            zero_more_action = ZeroOrMore(action)
            GOAL = zero_more_action + optional_times + one_more_light + optional_times + \
                   OneOrMore(String("quickly")('quick'))
        light = LightGrammar()
        assert light.name == "LightGrammar"
        print light
        parser = RobustParser(light)
        parser_bu = RobustParser(light, BottomUpStrategy)
        assert True == parser.print_parse("blink light light light quickly")
        assert True == parser_bu.print_parse("blink light light light quickly")
        assert True == parser.print_parse("light quickly")
        assert True == parser_bu.print_parse("light quickly")


# @pytest.mark.skipif(True, reason="")
class TestParser(object):
    def test_parser(self):
        class LightGrammar(Grammar):
            light_general = String("light")
            action = Regex(r"(turn on|turn off|off|blink)")
            times = Regex(r"(once|twice|three times)")
            GOAL = action + light_general + Optional(times) + \
                   String("quickly")('quick')
        light = LightGrammar()
        parser = RobustParser(light)
        assert True == parser.print_parse("blink light quickly")


# @pytest.mark.skipif(True, reason="")
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
        # known bug
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
        # assert True == parser.print_parse("set my top light to red")
        # assert True == parser.print_parse("set my top light to red and change "
        #                                   "middle light to yellow")
        # assert True == parser.print_parse("set my top light to red and change "
        #     "middle light to yellow and flash bottom light twice in blue")

        sents = ["set my top light to red",
            "set my top light to red and change middle light to yellow",
            "set my top light to red and change middle light to yellow and flash bottom light twice in blue"]
        for sent in sents:
            tree, result = parser.parse_string(sent)
            print '"%s"' % sent
            print "parse tree:"
            print tree
            print "parse result:"
            print result
            assert type(result.one_parse) is list
            print
