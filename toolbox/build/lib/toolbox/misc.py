# misc functions
import sys, os, shutil, getpass, glob, gnupg, json, gnureadline, re, operator, base64
from toolbox.logger import Log
from toolbox.menumaker import Menu
from pathlib import Path
try:
    import importlib_resources as resources
except:
    from importlib import resources

MOVE = '\033[35G'
MOVE2 = '\033[75G'
HOME = os.getenv("HOME")
RESET = '\033[0m'
GREEN = '\033[0;32m'
RED = '\033[1;31m'
UNDERLINE = '\033[4m'
MYBLUE = '\033[0;2;60m'
debug = 1
pushstack = list()
SCREEN_WIDTH=80
centered = operator.methodcaller('center', SCREEN_WIDTH)

def draw_title():
    b = centered('''
        (_(
        /_/'_____/)
        "  |      |
           |""""""|
    ''')
    return(''.join(b))

def convert(list):
    # convert list to tuple
    return tuple(list)

def convertTuple(tup):
    # initialize an empty string
    str = ''
    for item in tup:
        str = str + item
    return str

def decode_string(string):
    string_bytes = string.encode('ascii')
    return base64.b64decode(string_bytes).decode('ascii')

def set_terminal_width():
    return max(90, shutil.get_terminal_size().columns - 2)

def get_aliases():
    COMPLETION = HOME + '/goat_completion.sh'
    if os.path.isfile(COMPLETION):
        with open(COMPLETION) as F:
            LINES = [LINE.rstrip() for LINE in F]
        ALIASES = []
        TOTAL = 0
        for L in LINES:
            if 'alias' in L:
                TOTAL = TOTAL + 1
                NAME = L.split('=')[0].replace('alias','').strip()
                VALUE = L.split('=')[1].replace('"','').replace('"','')
                ALIAS_DICT = {}
                ALIAS_DICT['alias'] = NAME
                ALIAS_DICT['command'] = VALUE
                ALIASES.append(ALIAS_DICT)
        if ALIASES:
            return ALIASES
        else:
            Log.info("there are no aliases defined; configuring them now")
            define(COMPLETION)
    else:
        Log.info("there are no aliases defined; configuring them now")
        define(COMPLETION)

def define(completion):
    OSNAME = getpass.getuser().split('@')[0]
    with open(completion, "at") as source:
        source.write(
            "\n"
            "# Added by goat #\n"
        )

def detect_environment():
    return 'non-gc'

def search_man_pages(manuals):

    NAMES = []
    PATTERNS = []
    MINE = []
    SAVE = []

    MY_RESOURCES = resources.files("goat")
    DATA = (MY_RESOURCES / "manuals")

    # compile a list of patterns
    for SEARCH in manuals:
        PATTERNS.append(SEARCH)

    PATTERNS.sort()

    # compile a list of man pages
    for MAN in os.listdir(DATA):
        MINE.append(MAN)

    RUN = {}
    for MAN in MINE:
        for PATTERN in PATTERNS:
            if MAN not in RUN and PATTERN in MAN:
                RUN[MAN] = {
                    "%s" %(PATTERN)
                }
            elif MAN in RUN and PATTERN in MAN:
                RUN[MAN].update({ "%s" %(PATTERN) })

    for MAN in RUN:
        p = RUN[MAN]
        p = [(v) for v in p]
        p.sort()
        if p == PATTERNS:
            SAVE.append(MAN)

    SAVE.sort()
    NAMES = SAVE

    if NAMES == []:
        Log.critical(f'WARN: unable to find any user manuals loaded matching pattern {manuals}')
    else:
        INPUT = 'viewer'
        CHOICE = runMenu(NAMES, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            name = CHOICE.split('\t')[0]
            if name:
                Log.info(f"gathering manual {name} now, please wait...")
            else:
                Log.critical("please select a user manual to continue...")
        except:
            Log.critical("please select a user manual to continue...")
    return (MY_RESOURCES / "manuals" / name)

def runMenu(DATA, INPUT):
    COUNT = 0
    FINAL = []
    TITLE = f'GOAT: {INPUT}'
    for data in DATA:
        COUNT = COUNT + 1
        RESULTS = []
        RESULTS.append(data)
        FINAL.append(RESULTS)
    SUBTITLE = f'showing {COUNT} available object(s)'
    JOINER = '\t\t'
    FINAL_MENU = Menu(FINAL, TITLE, JOINER, SUBTITLE)
    CHOICE = FINAL_MENU.display()
    return CHOICE

def remove_html_tags(text):
    import re
    text = re.sub('<.*?>', '', text)
    clean = re.sub('{panel.*?}', '', text)
    return clean.strip()

def pushd(dirname):
    global pushstack
    pushstack.append(os.getcwd())
    os.chdir(dirname)

def popd():
    global pushstack
    os.chdir(pushstack.pop())
