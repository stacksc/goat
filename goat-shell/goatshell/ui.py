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

instructions = """
    1. To trigger auto-completion, start with TAB or type the beginning of a command or option and press Tab.
    2. Use the arrow keys or Tab to navigate through the suggestions.
    3. Press Enter to accept a suggestion or Esc to cancel.
    4. If an option requires a value, use --option=value instead of --option value.
    5. Special key '%%' will change scopes. Use it with TAB completion to change depth levels.
        %% ..        go back a depth level
        %% {scope}   change context to selected scope in TAB completion
        %%           unscope to root of the tree
"""

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
[F7]  Xtract CLI Tree
[F8]  Toggle Provider
[F9]  Toggle Profile
[F10] Toggle VIM
[F12] Toggle Safety Mode
"""

misc_input = """\
e|exit    : exit shell
c|clear   : clear screen
h|help    : display usage
##        : key to run OS command
%%        : key to change scopes
"""

def getLayout(with_help=None):
    os.system('clear')

    if with_help:
        # Create a TextArea for the instructions
        instructions_area = TextArea(
            text=instructions,  # Your instructions text
            read_only=True,     # Makes the TextArea read-only
            scrollbar=True      # Enables scrollbar if the content is too long
        )
    else:
        instructions_area = TextArea(
            text = "INFO: general instructions will be displayed here with the 'help' command",
            read_only=True,     # Makes the TextArea read-only
            scrollbar=False     # Enables scrollbar if the content is too long
        )

    instructions_frame = Frame(
        instructions_area,
        title=HTML("<b>Instructions</b>")
    )

    print_container(
        HSplit([
            Frame(
                Window(FormattedTextControl(text), height=2, align=WindowAlign.CENTER), title=(title)
            ),
            VSplit([
                Frame(body=Label(text=input.strip()), width=60, title=(func_title)),
                Frame(body=Label(text=misc_input.rstrip()), width=60, title=(misc_title))
            ]),
            instructions_frame # Add the instructions frame here
        ])
    )

if __name__ == '__main__':
    getLayout()
