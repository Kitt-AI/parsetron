#! /bin/sh

echo "CPython"
python time_parsetron.py > /dev/null

echo "\n\nPypy"
pypy time_parsetron.py warmup > /dev/null
