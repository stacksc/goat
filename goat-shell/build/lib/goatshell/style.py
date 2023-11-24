from __future__ import print_function, absolute_import, unicode_literals

from pygments.token import Token
from pygments.util import ClassNotFound
from pygments.styles import get_style_by_name
from prompt_toolkit.styles import Style

styles = {
    'token.app.title': 'bg:#005577 #ffffff',
    'completion-menu.completions.current': 'bg:#afb3b5 #666d6f',
    'completion-menu.completion': 'bg:#666d6f #afb3b5',
    'completion-menu.meta.current': 'bg:#afb3b5 #000000',
    'completion-menu.meta': 'bg:#afb3b5 #7f7f7f',
    'bottom-toolbar.off': 'bg:#222222 #696969',
    'bottom-toolbar.on': 'bg:#000000 #ffffff',
    'bottom-toolbar.search': 'noinherit bold',
    'bottom-toolbar.search.text': 'noinherit bold',
    'bottom-toolbar.system': 'noinherit bold',
    'bottom-toolbar.arg': 'noinherit bold',
    'bottom-toolbar': 'bg:#ffffff #000000',
    'bottom-toolbar-red': 'bg:#ff0000 #000000',
    'success-text': 'bold',
    'failure-text': 'bg:#ff0000 #000000 bold'   # black background with red text
}
