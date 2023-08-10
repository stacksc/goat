#!/usr/bin/env python
# ==============================================================================
# Copyright (c) 2020, Oracle and/or its affiliates. All rights reserved.
# ==============================================================================

import sys, os
c = '/opt/native/gen2cli/.override_colors'

RESET = '\033[0m'
CYAN = '\033[0;36m'
RED = '\033[31m'
boldRED = '\033[0;31m'
YELLOW = '\033[0;33m'
GREEN = '\033[0;32m'
MAGENTA = '\033[0;35m'
MYBLUE = '\033[0;2;60m'
BLUE = '\033[38;5;69m'
GREY = '\033[0;49;39m'
LIGHTGREY = '\033[0;37m'
ORANGE = '\033[38;5;172m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'
SCREEN_WIDTH = 95
MOVE1 = '\033[70G'
MOVE2 = '\033[100G'
WHITE = '\033[1;37m'

if os.path.isfile(c):
    COLOR = (([line.split('=')[1].strip('\n').strip('"') for line in open(c) if 'USAGE_COLOR' in line]))
    COLOR = ''.join(map(str, COLOR))
    if 'GREEN' in COLOR:
        USAGE_COLOR = GREEN
    elif 'CYAN' in COLOR:
        USAGE_COLOR = CYAN
    elif 'MYBLUE' in COLOR:
        USAGE_COLOR = MYBLUE
    elif 'RED' in COLOR:
        USAGE_COLOR = RED
    elif 'MAGENTA' in COLOR:
        USAGE_COLOR = MAGENTA
    elif 'YELLOW' in COLOR:
        USAGE_COLOR = YELLOW
    elif 'ORANGE' in COLOR:
        USAGE_COLOR = ORANGE
    elif 'BLUE' in COLOR:
        USAGE_COLOR = BLUE
    elif 'LIGHTGREY' in COLOR:
        USAGE_COLOR = LIGHTGREY
    elif 'GREY' in COLOR:
        USAGE_COLOR = GREY
    else:
        USAGE_COLOR = MYBLUE
else:
    USAGE_COLOR = MYBLUE

def get_username():
    from os import environ, getcwd
    user = (lambda: environ["USERNAME"] if "C:" in getcwd() else environ["USER"])()
    return user
