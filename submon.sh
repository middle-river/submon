#!/bin/sh

export TERM=xterm
export LANG=ja_JP.UTF-8
export LC_CTYPE=C.UTF-8
export LC_ALL=C.UTF-8

while : ; do
xterm -fa 'Monospace' -fs 32 -fullscreen -e $(dirname $0)/submon.py
done
