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

version = '1.0.0'
text = "Purpose: Cloud Wrapper\nVersion: %s" %(version)
title = HTML("""<b>GOAT INTERFACE</b>""")
func_title = HTML("""<b>Hotkeys</b>""")
misc_title = HTML("""<b>Misc</b>""")
input = """\

[F8]  Display Help & Layout
[F10] Toggle Cloud Profiles
[F12] Exit
[TAB] Fuzzy auto-completion

"""
misc_input = """\
 e|exit    : exit shell
 c|clear   : clear screen
 h|help    : display usage
 !<cmd>    : run OS command
"""

def getLayout():

    os.system('clear')
    print_container(
    HSplit([
        Frame(
            Window(FormattedTextControl(text), height=2, align=WindowAlign.CENTER), title=(title)),
        VSplit([
            HSplit([
                Frame(body=Label(text=input.strip()), width=60, title=(func_title)),
            ], padding=1, padding_char=' ', align=HorizontalAlign.LEFT),
            HSplit([
                Frame(body=Label(text=misc_input.rstrip()), width=60, title=(misc_title)),
            ], padding=1, padding_char=' ', align=HorizontalAlign.CENTER)
        ])
    ]))
    print()

if __name__ == '__main__':
    getLayout()
