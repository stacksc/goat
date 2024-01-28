import sys, os, signal, readline

if os.name != 'nt':
    import tty

from prompt_toolkit import prompt
from prompt_toolkit.filters import Condition
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings

user_env_var = "USERNAME" if os.name == 'nt' else "LOGNAME"
default_assignee = os.environ.get(user_env_var, None)

def getJiraCredentials():
    try:
        JIRA_USER = default_assignee
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

    if os.name != 'nt':
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    JIRA_USER = input('Enter username ' + "[" + str(default_assignee).split('@')[0] + "] : ").strip()
    if not JIRA_USER:
        JIRA_USER = str(default_assignee).split('@')[0]

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    JIRA_PASS = prompt(
        "Enter password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    if os.name != 'nt':
        tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
    # enable (^Z) SIGTSTP
    if os.name != 'nt':
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
    if os.name != 'nt':
        OLD = tty.tcgetattr(STDIN)
    @BINDINGS.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        HIDDEN[0] = not HIDDEN[0]
    SECURE_STRING = prompt(
        prompt_msg, is_password=Condition(lambda: HIDDEN[0]), key_bindings=BINDINGS
    )
    if os.name != 'nt':
        tty.tcsetattr(STDIN, tty.TCSAFLUSH, OLD)
    signal.signal(signal.SIGTSTP, signal.SIG_DFL)
    return SECURE_STRING

def password_prompt():

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    PASSWORD = prompt(
        "Enter password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    # restore terminal settings
    if os.name != 'nt':
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

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    USER = input('Enter ' + title + ' username ' + "[" + str(default_assignee).split('@')[0] + "] : ").strip()
    if not USER:
        USER = str(default_assignee).split('@')[0]

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    PASS = prompt(
        "Enter " + title + " password: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    if os.name != 'nt':
        # restore terminal settings
        tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
        # enable (^Z) SIGTSTP
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return USER, PASS

def get_azure_org(title='default'):

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    U = 'baxtercu'
    ORG = input('Paste ' + title + ' default org here: ' + "[" + str(U) + "] : ").strip()

    if not ORG:
        ORG = str(U).strip()

    if os.name != 'nt':
        # restore terminal settings
        tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
        # enable (^Z) SIGTSTP
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return ORG
    return remove_lead_and_trail_slash(ORG)

def get_azure_url(title='default'):

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    U = 'https://dev.azure.com'
    URL = input('Paste ' + title + ' full URL here: ' + "[" + str(U) + "] : ").strip()

    if not URL:
        URL = str(U).strip()

    if os.name != 'nt':
        # restore terminal settings
        tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
        # enable (^Z) SIGTSTP
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return URL
    return remove_lead_and_trail_slash(URL)

def getFullUrl(title='default'):

    hidden = [True]  # Nonlocal
    bindings = KeyBindings()

    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    stdin = sys.__stdin__.fileno()
    stream = sys.__stderr__.fileno()

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    URL = prompt(
        "Paste " + title + " full URL here: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )

    if os.name != 'nt':
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

    if os.name != 'nt':
        old = tty.tcgetattr(stdin)

    @bindings.add("c-t")
    def _(event):
        "When ControlT has been pressed, toggle visibility."
        hidden[0] = not hidden[0]

    TOKEN = prompt(
        "Paste " + title + " token here: ", is_password=Condition(lambda: hidden[0]), key_bindings=bindings
    )
    if os.name != 'nt':
        # restore terminal settings
        tty.tcsetattr(stdin, tty.TCSAFLUSH, old)
        # enable (^Z) SIGTSTP
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)

    # return credentials
    return TOKEN
