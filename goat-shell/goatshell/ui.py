from __future__ import print_function, unicode_literals
import sys, os

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.styles import Style

from prompt_toolkit.layout.containers import (
    HorizontalAlign,
    HSplit,
    VerticalAlign,
    VSplit,
    Window,
    WindowAlign,
)

from prompt_toolkit.widgets import (
    Frame,
    Label,
    TextArea,
)

buffer1 = Buffer()

def is_non_zero_file(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0

tip = 'TIP: resource completion coming soon!'
version = '1.0.0'
text = f"Purpose: Cloud Wrapper\n{tip}"
title = HTML("""<b>GOAT INTERFACE</b>""")
func_title = HTML("""<b>Hotkeys</b>""")
misc_title = HTML("""<b>Commands</b>""")
advanced_title = HTML("""<b>Advanced</b>""")
input = """\
[F9]  Toggle VI mode
[F10] Toggle Profile
[TAB] Fuzzy Complete
"""

misc_input = """\
e|exit    : exit shell
c|clear   : clear screen
h|help    : display usage
"""

advanced_input = """\
history   : shell history
!<cmd>    : run OS command
cloud     : view cloud details
"""

def getLayout():

    os.system('clear')
    print_container(
    HSplit([
        Frame(
            Window(FormattedTextControl(text), height=2, align=WindowAlign.CENTER), title=(title)),
        VSplit([
            Frame(body=Label(text=input.strip()), width=30, title=(func_title)),
            Frame(body=HSplit([Label(text=advanced_input.strip())], padding=1, padding_char=' '), width=40, title=(advanced_title)),
            Frame(body=Label(text=misc_input.rstrip()), width=30, title=(misc_title))
        ])
    ]))

if __name__ == '__main__':
    getLayout()
