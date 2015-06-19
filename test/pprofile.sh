#! /bin/sh
# https://github.com/vpelletier/pprofile
# pip install pprofile
# brew install qcachegrind


# cmd line:
# pprofile $(which py.test) > pprofile.log

# gui:
pprofile --format callgrind --out cachegrind.out.threads $(which py.test)

qcachegrind &
