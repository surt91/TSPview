#!/bin/bash
AUTH=$(echo $X11AUTH | head -n1 | cut -d ' ' -f 3)
echo "token: $AUTH"
touch ~/.Xauthority
xauth add $HOSTNAME/unix:0 . $AUTH

/usr/bin/python3 main.py
