# misc functions
import sys, os, shutil, getpass, glob, gnupg, json, re, operator, base64, subprocess
from toolbox.logger import Log
from pathlib import Path
from configstore.configstore import Config
from azdevops.misc import generic_menu

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
        CHOICE = generic_menu(NAMES)
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

def get_save_path(filename="aws.json"):
    user_home = Path.home()
    goat_shell_data_path = user_home / "goat" / "shell" / "data"
    goat_shell_data_path.mkdir(parents=True, exist_ok=True) # create directory if doesn't exist
    return goat_shell_data_path / filename

def attempt_load_custom_json(provider):
    """
    Attempt to load user's custom JSON from home directory.

    Args:
    - provider (str): The cloud provider's name.

    Returns:
    - bool: True if successful, False otherwise.
    """
    # Get the user's custom JSON path
    user_home = Path.home()
    user_json_path = user_home / "goat" / "shell" / "data" / f"{provider}.json"

    # If user's custom JSON does not exist, return False
    if not user_json_path.exists():
        return False

    # Try to load the JSON
    try:
        with user_json_path.open() as json_file:
            data = json.load(json_file)
        # Successfully loaded JSON
        return True
    except Exception as ex:
        logger.warning(f"Exception while attempting to load user's custom JSON for {provider}: {ex}")
        # Failed to load JSON
        return False

def is_valid_json(file_path):
    try:
        with open(file_path, 'r') as json_file:
            json.load(json_file)
        return True
    except:
        return False

def get_corrupt_provider_files():
    user_home = Path.home()
    data_directory = user_home / "goat" / "shell" / "data"
    corrupt_files_dict = {}

    for json_file in data_directory.glob('*.json'):
        if not is_valid_json(json_file):
            # Extracting the provider name from the file name
            provider_name = json_file.stem
            corrupt_files_dict[provider_name] = str(json_file)

    return corrupt_files_dict

def get_latest_profile(config_store):
    CONFIGSTORE = Config(config_store)
    # Retrieve the 'latest' profile
    LATEST = CONFIGSTORE.get_profile('latest')

    if LATEST is None:
        # Fallback to default if no 'latest' profile
        MY_PROFILE = 'default'
        URL = 'DEFAULT'
    else:
        # Extract the role from the 'latest' profile's config
        role_name = LATEST['config'].get('role')
        # Use the role_name to fetch the corresponding profile
        role_profile = CONFIGSTORE.get_profile(role_name)

        if role_profile:
            MY_PROFILE = role_name
            # Assuming the 'url' is directly under the 'config' of the role profile
            URL = role_profile.get('config', {}).get('url', 'DEFAULT')  # Set 'DEFAULT' if 'url' is not found
            if URL == 'DEFAULT':
                # try to get it from metadata
                URL = role_profile.get('metadata', {}).get('url', 'DEFAULT')  # Set 'DEFAULT' if 'url' is not found
        else:
            # Fallback if the role profile doesn't exist
            MY_PROFILE = 'default'  # Ensure consistency in fallback profile naming
            URL = 'DEFAULT'
    
    # Ensure URL is not None; if it is, set to 'DEFAULT'
    if URL is None:
        URL = 'DEFAULT'
        
    return MY_PROFILE, URL.upper()

def clear_screen():
    # Clear the screen
    subprocess.call('clear' if os.name == 'posix' else 'cls')

def get_terminal_size():
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)

def draw_title():
    b = centered('''
        (_(
        /_/'_____/)
        "  |      |
           |""""""|
    ''')
    return(''.join(b))
