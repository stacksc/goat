import sys, os, tty, signal, readline
from prompt_toolkit import prompt
from prompt_toolkit.filters import Condition
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings

def getIDPCredentials():
    try:
        IDP_USER = os.environ['LOGNAME'].replace('admins.','')
        IDP_PASS = os.environ['IDP_PASS']
    except:
        IDP_USER = ''
        IDP_PASS = ''
    return IDP_USER, IDP_PASS

def getJiraCredentials():

    try:
        JIRA_USER = os.environ['LOGNAME']
        JIRA_PASS = os.environ['JIRA_API_TOKEN']
    except:
        JIRA_USER = ''
        JIRA_PASS = ''
    return JIRA_USER, JIRA_PASS

def getCreds():

    JIRA_USER, JIRA_PASS = getJiraCredentials()
    if JIRA_USER and JIRA_PASS:
        return JIRA_USER, JIRA_PASS
    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    old = tty.tcgetattr(stdin)

    JIRA_USER = input('Enter username ' + "[" + os.environ['LOGNAME'].split('@')[0] + "] : ").strip()
    if not JIRA_USER:
        JIRA_USER = os.environ['LOGNAME'].split('@')[0]

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    JIRA_PASS = prompt(
        "Enter password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return JIRA_USER, JIRA_PASS

# generic version of the two functions above
def get_secure_string_from_environ(var_name):
    try:
        SECURE_STRING = os.environ[var_name]
    except:
        SECURE_STRING = None
    return SECURE_STRING

def get_secure_string(var_name, prompt_msg="Enter password: "):
    SECURE_STRING = get_secure_string_from_environ(var_name)
    if SECURE_STRING:
        return SECURE_STRING
    HIDDEN = [True]
    BINDINGS = KeyBindings()
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    STDIN = sys.__stdin__.fileno()
    STREAM = sys.__stderr__.fileno()
    OLD = tty.tcgetattr(STDIN)
    @BINDINGS.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        HIDDEN[0] = not HIDDEN[0]
    SECURE_STRING = prompt(
        prompt_msg, is_password=Condition(lambda: HIDDEN[0]), key_bindings=BINDINGS
    )
    tty.tcsetattr(STDIN, tty.TCSAFLUSH, OLD)
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)
    return SECURE_STRING

def password_prompt():

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    PASSWORD = prompt(
        "Enter password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return PASSWORD

def getOtherCreds(title='default'):

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    old = tty.tcgetattr(stdin)

    USER = input('Enter ' + title + ' username ' + "[" + os.environ['LOGNAME'].split('@')[0] + "] : ").strip()
    if not USER:
        USER = os.environ['LOGNAME'].split('@')[0]

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    PASS = prompt(
        "Enter " + title + " password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return USER, PASS

def getFullUrl(title='default'):

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    URL = prompt(
        "Paste " + title + " full URL here: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )

    # restore terminal settings
    tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return URL
    return remove_lead_and_trail_slash(URL)

def remove_lead_and_trail_slash(s):
    if s.startswith('/'):
        s = s[1:]
    if s.endswith('/'):
        s = s[:-1]
    return s

def getOtherToken(title='default'):

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    TOKEN = prompt(
        "Paste " + title + " token here: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return TOKEN

def getIDPCreds():

    IDP_USER, IDP_PASS = getIDPCredentials()
    if IDP_USER and IDP_PASS:
        return IDP_USER, IDP_PASS
    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    old = tty.tcgetattr(stdin)

    IDP_USER = input('Enter username ' + "[" + os.environ['LOGNAME'].replace('admins.','') + "] : ").strip()
    if not IDP_USER:
        IDP_USER = os.environ['LOGNAME'].replace('admins.','')

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    IDP_PASS = prompt(
        "Enter password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return IDP_USER, IDP_PASS
