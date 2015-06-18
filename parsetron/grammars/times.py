from parsetron import Grammar, Or, Set, RobustParser
from parsetron.grammars.numbers import replaced_string, NumbersGrammar

__author__ = 'Xuchen Yao'


class TimesGrammar(Grammar):

    special_maps = [
        ('once', 1),
        ('twice', 2),
        ('thrice', 3),
    ]

    special = Or([replaced_string(s, v) for s, v in special_maps])

    numbers = NumbersGrammar.GOAL

    GOAL = special | \
        (numbers + Set('times time').ignore())

    sents = [
        ('zero time', 0),
        ('once', 1),
        ('1 time', 1),
        ('5 times', 5),
        ('five times', 5),
        ('sixty seven times', 67),
        ('five hundred ten times', 510),
        ('a million times', int(1e6)),
    ]

    @staticmethod
    def test():
        g = TimesGrammar()
        parser = RobustParser(g)
        for sent, expect in TimesGrammar.sents:
            _, r = parser.parse(sent)
            print(r)
            assert r.get() == expect, "%s <- %s" % (str(r.get()), sent)


def test():
    """
    Simple test method to be called by pytest
    """
    TimesGrammar.test()

if __name__ == '__main__':
    test()
