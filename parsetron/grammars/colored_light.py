from parsetron import Set, Grammar, Optional, ZeroOrMore, OneOrMore, \
    RobustParser
from parsetron.grammars.times import TimesGrammar
from parsetron.grammars.colors import ColorsGrammar

__author__ = 'Xuchen Yao'


class ColoredLightGrammar(Grammar):

    # On or off
    on = Set(['turn on', 'on', 'hit'])
    off = Set(['turn off', 'off', 'kill'])
    on_off = on | off

    # light names
    general_name = Set(["lights", "light", "lamp", "bulb", "lightbulb"])
    specific_name = Set(["top", "bottom", "middle", "kitchen", "living room",
                         "bedroom", "bedside"])
    light_quantifiers = Set(["both", "all"])
    light_name = Optional(light_quantifiers) + \
        ZeroOrMore(specific_name) + \
        Optional(general_name)

    # actions
    action_blink = Optional(Set(["blink", "flash"]))

    # brightness
    brightness_more = Set(["bright", "brighter", "strong", "stronger",
                           "too dark"])
    brightness_less = Set(["less bright", "soft", "softer", "dim", "dimmer",
                           "too bright"])
    brightness = brightness_more | brightness_less

    # saturation
    saturation_more = Set(["deeper", "darker", "warmer", "too cold"])
    saturation_less = Set(["lighter", "shallower", "colder", "too warm"])
    saturation = saturation_less | saturation_more

    color = ColorsGrammar.GOAL

    times = TimesGrammar.GOAL

    theme = Set(["christmas", "xmas", "halloween", "romantic", "valentine",
                 "valentine's", "reading", "beach", "sunrise", "sunset"])

    one_parse = (
        on_off |
        light_name + on_off |
        on_off + light_name |
        light_name + Optional(color) + Optional(times) |
        light_name + Optional(times) + Optional(color) |
        light_name + color |
        light_name + brightness |
        brightness + light_name |
        light_name + saturation |
        saturation + light_name |
        theme
    )

    GOAL = (
        OneOrMore(one_parse) |
        action_blink + OneOrMore(one_parse)
    )

    sents = [
        (True, "blink top lights"),
        (True, "flash both top and bottom light with red color and "
               "middle light with green and bottom with purple"),
        (True, "flash both top and bottom light with red color and "
               "middle light with green"),
        (True, "flash both "),
        (True, "blink top lights twice"),
        (True, "I want to blink top lights"),
        (True, "on top"),
        (True, "have top red"),
        (True, "change top to red and bottom to yellow"),
        (True, "lights please on"),
        (True, "flash middle and top light "),
        (True, "change my top light to red and middle to yellow then "
               "bottom blue"),
        (True, "turn on lights please"),
        (True, "I want to turn off the top light please"),
        (True, "I want to turn off the lights please"),
        (True, "change top lights to red"),
        (True, "kill top lights for me"),
        (True, "turn lights on"),
        (True, "blink top"),
        (True, "blink top lights twice"),
        (True, "flash middle light twice with red and top once"),
        (True, "flash middle light twice red top once"),
        (True, "give me something romantic"),
        (True, "my top light is too dark"),
        (True, "my top and bottom lights can be warmer"),
        (False, "I want to turn ")
    ]

    @staticmethod
    def test():
        import time
        parser = RobustParser(ColoredLightGrammar())
        sents = ColoredLightGrammar.sents
        s = time.time()
        for expect, sent in sents:
            s1 = time.time()
            assert expect == parser.print_parse(sent), sent
            s2 = time.time()
            print("parse time: %.2f ms" % ((s2-s1)*1000))
            print()
        e = time.time()
        elapsed = e - s
        print("total time: %.2f s" % (elapsed))
        print("per parse: %.2f ms" % (elapsed*1000/len(sents)))


def test():
    """
    Simple test method to be called by pytest
    """
    ColoredLightGrammar.test()
