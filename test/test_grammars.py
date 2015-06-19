import os


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)


def test_grammars():
    for fname in os.listdir("parsetron/grammars"):
        if fname.endswith('.py') and not fname.startswith("__"):
            module = fname[0:-3]  # numbers.py -> numbers
            # pull out the test() function in each module
            test = import_from("parsetron.grammars." + module, "test")
            test()
