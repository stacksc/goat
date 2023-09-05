from __future__ import print_function, absolute_import, unicode_literals

from pygments.token import Token
from pygments.util import ClassNotFound
from pygments.styles import get_style_by_name
from prompt_toolkit.styles import Style

styles_dict = {
        "": "ansicyan",
        "oci": "#C74634",
        "bottom-toolbar": "noreverse",
        "bottom-toolbar.text": "#888888 bg:default noreverse noitalic nounderline noblink",
        "bottom-toolbar.error": "fg:ansired",
        "required-parameter": "fg:ansired"
}
