from parsetron import String, Grammar, Regex, Or, Optional, ZeroOrMore, \
    OneOrMore, RobustParser

__author__ = 'Xuchen Yao'


def replaced_string(s, v):
    return String(s).replace_result_with(v)


def result_sum(r):
    # result could either be a list or a single item
    try:
        r.set(sum(r.get()))
    except TypeError:  # not a list
        r.set(r.get())


def result_mul(r):
    try:
        m = 1
        for i in r.get():
            if type(i) is list:
                i = i[0]
            m *= i
    except TypeError:  # not a list
        m = r.get()
    r.set(m)


class NumbersGrammar(Grammar):

    single_maps = [
        ('zero', 0), ('o', 0), ('oh', 0), ('nada', 0), ('one', 1),
        ('a', 1), ('two', 2), ('three', 3), ('four', 4), ('five', 5),
        ('six', 6), ('seven', 7), ('eight', 8), ('nine', 9), ('ten', 10),
        ('eleven', 11), ('twelve', 12), ('thirteen', 13), ('fourteen', 14),
        ('forteen', 14), ('fifteen', 15), ('sixteen', 16), ('seventeen', 17),
        ('eighteen', 18), ('nineteen', 19)]

    ten_maps = [
        ('ten', 10), ('twenty', 20), ('thirty', 30), ('forty', 40),
        ('fourty', 40), ('fifty', 50), ('sixty', 60), ('seventy', 70),
        ('eighty', 80), ('ninety', 90)]

    digits = Regex(r"\d+").set_result_action(lambda r: r.set(int(r.get())))

    single = Or([replaced_string(s, v) for s, v in single_maps])
    ten = Or([replaced_string(s, v) for s, v in ten_maps])

    double = (Optional(ten) + Optional(single)).set_result_action(result_sum) \
        | digits

    a_hundred = replaced_string('hundred', 100)
    zero_maps = [
        ('hundred', 100), ('thousand', 1000), ('million', int(1e6)),
        ('billion', int(1e9)), ('trillion', int(1e12))]
    zero = Or([replaced_string(s, v) for s, v in zero_maps])
    zeros = ZeroOrMore(zero).set_result_action(result_mul)

    hundred = ((double + a_hundred).set_result_action(result_mul) +
               Optional(double)).set_result_action(result_sum)

    unit = ((double | hundred) + zeros).set_result_action(result_mul)

    GOAL = OneOrMore(unit).set_result_action(result_sum)

    sents = [
        ('zero', 0),
        ('twelve', 12),
        ('twenty', 20),
        ('twenty three', 23),
        ('23', 23),
        ('eight hundred fifty eight', 858),
        ('one hundred twenty five', 125),
        ('seventy three', 73),
        ('twelve hundred thirty five', 1235),
        ('twenty two hundred thirty five', 2235),
        ('two thousand', 2000),
        ('two thousand two hundred thirty five', 2235),
        ('seventy eight thousand nine hundred twenty one', 78921),
        ('seven hundred eighty nine thousand twenty one', 789021),
        ('one million sixty one', 1000061),
        ('1 million sixty one', 1000061),
        ('1 million 61', 1000061),
        ('twenty three million seven hundred eighty nine thousand', 23789000),
        ('one hundred thousand sixty one', 100061),
        ('one hundred thousand five hundred sixty one', 100561),
        ('1 hundred thousand 5 hundred 61', 100561),
    ]

    @staticmethod
    def test():
        parser = RobustParser(NumbersGrammar())
        for sent, expect in NumbersGrammar.sents:
            t, r = parser.parse(sent)
            # print(t)
            # print(r)
            assert r.get() == expect, "%s <- %s" % (str(r.get()), sent)


def test():
    """
    Simple test method to be called by pytest
    """
    NumbersGrammar.test()


if __name__ == "__main__":
    test()
