from parsetron import *
import time
import sys

sents = [
         # (True, "go hopkins jays quick"),
         (True, "lights please on"),
         (True, "flash both top and bottom light with red color and middle light with green"),
         (True, "flash middle light twice with red and top once"),
         (True, "flash middle light twice red top once"),
         (True, "on top"),
         (True, "flash middle and top light "),
         (True, "change my top light to red and middle to yellow then bottom blue"),
         (True, "turn on lights please"),
         (True, "I want to turn off the top light please"),
         (True, "I want to turn off the lights please"),
         (True, "I want to blink top lights"),
         (True, "change top lights to red"),
         (True, "change top to red and bottom to yellow"),
         (True, "kill top lights for me"),
         (True, "blink top lights twice"),
         (True, "turn lights on"),
         (True, "blink top"),
         # (False, "I want to turn ")
         ]

time_grammar_s = time.time()
from parsetron.grammars import colored_light
light = colored_light.ColoredLightGrammar()
parser_td = RobustParser(light, TopDownStrategy)
parser_bu = RobustParser(light, BottomUpStrategy)
parser_lc = RobustParser(light, LeftCornerStrategy)
time_grammar_e = time.time()

print >> sys.stderr, \
    "grammar init time: %.2f seconds" % (time_grammar_e-time_grammar_s)

def test_code(parser):
    global sents
    for (expect, sent) in sents:
        assert expect == parser.print_parse(sent), sent

# warm up 
try:
    if sys.argv[1] == 'warmup':
        for i in range(20):
            test_code(parser_td)
            test_code(parser_bu)
            test_code(parser_lc)
except:
    pass

def parse_time(strategy):
    iterations = 5
    if strategy == 0:
        parser = parser_td
        pstr = "Top Down"
    elif strategy == 1:
        parser = parser_bu
        pstr = "Bottom Up"
    elif strategy == 2:
        parser = parser_lc
        pstr = "Left Corner"

    time_parser_s = time.time()
    for i in range(iterations):
        test_code(parser)
    time_parser_e = time.time()

    elapsed = time_parser_e-time_parser_s
    print >> sys.stderr, \
        "%s parsing time: %.2f seconds" % (pstr, elapsed)

    per_parse = elapsed*1000/iterations/len(sents)
    print >> sys.stderr, \
        "%s time per parse: %.2f ms" % (pstr, per_parse)
    return elapsed, per_parse

td_elapsed, td_per = parse_time(0)
bu_elapsed, bu_per = parse_time(1)
lc_elapsed, lc_per = parse_time(2)

print >> sys.stderr, "\naverage time per parse: %.2f ms" % ((td_per+bu_per+lc_per)/3)
