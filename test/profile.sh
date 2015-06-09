#! /bin/sh
P=$@
if [ -z "$P" ]
then
    P=profile.slow
fi
python -m cProfile -o $@ $(which py.test)
runsnake $@ &
