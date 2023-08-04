# misc functions
import sys, os, shutil, getpass, importlib_resources, glob, gnupg, json, gnureadline, re
from toolbox.logger import Log
from toolbox.menumaker import Menu
from pathlib import Path
from idptools.idpclient import idp_setup

MOVE = '\033[40G'
MOVE2 = '\033[75G'
HOME = os.getenv("HOME")
RESET = '\033[0m'
GREEN = '\033[0;32m'
RED = '\033[1;31m'
UNDERLINE = '\033[4m'
MYBLUE = '\033[0;2;60m'
pushstack = list()

def convert(list):
    # convert list to tuple
    return tuple(list)

def convertTuple(tup):
    # initialize an empty string
    str = ''
    for item in tup:
        str = str + item
    return str

def set_terminal_width():
    return max(80, shutil.get_terminal_size().columns - 2)

def get_aliases():
    COMPLETION = HOME + '/pyps_completion.sh'
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
            "# Added by pyps #\n"
            f'alias cscm="pyps jira project search CSCM -a {OSNAME} -t"\n'
            f'alias cssd="pyps jira project search CSSD -a {OSNAME} -t"\n'
            f'alias pubsec="pyps jira project search PUBSECSRE -a {OSNAME} -t"\n'
            'alias toggle="pyps aws iam authenticate"\n'
        )

def detect_environment():
    try:
        DOMAIN = os.getenv('USER').split('@')[1]
        ENVS = {
            "admins.vmwarefed.com": 'gc-prod',
            "vmwarefedstg.com": 'gc-stg',
            "svc.vmwarefed.com": 'gc-prod',
            "vmware.smil.mil": 'ohio-sim'
        }
        RESULT = ENVS[DOMAIN]
    except:
        Log.debug('Unable to get user domain; assuming non-gc environment (ie VMware issued macbook)')
        return 'non-gc'
    return RESULT

def easy_setup(reset=False):
    # hack to easily setup the tools
    if reset is True and 'prod' in detect_environment():
        name = 'jiratools'
        Log.info(f'setting up {name} now for JIRA servicedesk authentication')
        JIRAURL = 'https://servicedesk.vmwarefed.com'
        os.system('rm -f ~/.jiratools.*')
        command = f'jiratools -p default auth -u {JIRAURL} -m pass'
        os.system(command)
        name = 'nexustools'
        Log.info(f'setting up {name} now for Nexus')
        command = 'nexustools -p default auth setup'
        os.system(command)
        name = 'jenkinstools'
        Log.info(f'setting up {name} now for delta')
        command = 'jenkinstools -p delta auth setup'
        os.system(command)
        Log.info(f'setting up {name} now for atlas')
        command = 'jenkinstools -p atlas auth setup'
        os.system(command)
        name = 'awstools'
        Log.info(f'setting up {name} now for AWS authentication')
        command = 'awstools -p default iam reset-password'
        os.system(command)
        command = 'awstools -p default iam authenticate'
        os.system(command)
        name = 'confluence'
        Log.info(f'setting up {name} now for confluence authentication')
        command = 'contools -p default auth setup'
        os.system(command)
    elif 'prod' in detect_environment():
        name = 'csptools'
        ANS = input(f"INFO: would you like to setup client {name} for operator org? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'csptools -p operator auth setup -i 62f106e6-ad48-11e8-b5e4-0650ddb62ab0 -n "VMC Gov Cloud Operator Org PRD"'
            os.system(command)
        ANS = input(f"INFO: would you like to setup client {name} for platform org? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'csptools -p platform auth setup -i 82ec843d-8c67-46c4-aef3-ea814b61d1f9 -n "Platform org"'
            os.system(command)
        name = 'jiratools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            JIRAURL = 'https://servicedesk.vmwarefed.com'
            command = f'jiratools -p default auth -u {JIRAURL} -m pass'
            os.system(command)
        name = 'nexustools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'nexustools -p default auth setup'
            os.system(command)
        name = 'jenkinstools'
        ANS = input(f"INFO: would you like to setup client {name} for Delta? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'jenkinstools -p delta auth setup'
            os.system(command)
        ANS = input(f"INFO: would you like to setup client {name} for Atlas? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'jenkinstools -p atlas auth setup'
            os.system(command)
        name = 'awstools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'awstools -p default iam reset-password'
            os.system(command)
            command = 'awstools -p default iam authenticate'
            os.system(command)
        name = 'confluence'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'contools -p default auth setup'
            os.system(command)
        name = 'idptools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            NAMES = get_client_credentials()
            for NAME in NAMES:
                Log.info(f"setting up tenant: {NAME}")
                TENANT = NAME.replace("vidm_","")
                INFO = NAMES[NAME]
                URL = INFO['idp']
                CLIENT = INFO['client_id']
                SECRET = INFO['client_secret']
                idp_setup(URL, CLIENT, SECRET, user_profile=TENANT)
    else:
        name = 'jiratools'
        JIRAURL = 'https://servicedesk.eng.vmware.com'
        ANS = input(f"INFO: would you like to setup client {name} using {JIRAURL}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = f'jiratools -p default auth -u {JIRAURL} -m pass'
            os.system(command)
        JIRAURL = 'https://jira.eng.vmware.com'
        ANS = input(f"INFO: would you like to setup client {name} using {JIRAURL}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = f'jiratools -p jd auth -u {JIRAURL} -m pass'
            os.system(command)
        name = 'jfrogtools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'jfrogtools -p default auth setup'
            os.system(command)
        name = 'jenkinstools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'jenkinstools -p default auth setup'
            os.system(command)
        name = 'awstools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'awstools -p default iam authenticate -r us-gov-west-1 -o json'
            os.system(command)
        name = 'confluence'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'contools -p default auth setup'
            os.system(command)
        name = 'flytools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'flytools -p default auth setup'
            os.system(command)
        name = 'gitools'
        ANS = input(f"INFO: would you like to setup client {name}? [Y/n]: ")
        if ANS == 'Y' or ANS == 'y' or not ANS:
            command = 'gitools -p default auth setup'
            os.system(command)
    return True

def get_client_credentials():

    NAMES = {}
    HOME = str(Path.home())
    for KEY in glob.glob(HOME + "/.vidm_*.gpg"):
        if os.path.isfile(KEY):
            try:
                KEY = str(Path(KEY).stem.replace(".",""))
                BASE = os.path.basename(KEY)
                tenant_file = '~/.' + BASE + '.gpg'
                if not os.path.exists(os.path.expanduser(tenant_file)):
                    Log.critical(f"failed to load {tenant_file} file, please create the client file prior to running this command")
                gpg = gnupg.GPG()
                with open(os.path.expanduser(tenant_file), 'rb') as f:
                    d = str(gpg.decrypt(f.read()))
                    r = json.loads(d)
                    NAMES[BASE] = { 'idp': r["idp"], 'client_id': r["client_id"], 'client_secret': r["client_secret"] }
            except:
                pass
    return NAMES

def search_man_pages(manuals):

    NAMES = []
    PATTERNS = []
    MINE = []
    SAVE = []

    MY_RESOURCES = importlib_resources.files("pyps")
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
        Log.critical(f'unable to find any user manuals loaded matching pattern {manuals}')
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
    TITLE = f'PYPS: {INPUT}'
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

def SddcMenuResults(ctx):

    from csptools.cspclient import CSPclient
    CSP = CSPclient()
    DATA = []
    OUTPUT = CSP.list_orgs_with_sddc(ctx.obj['operator'], 'operator')
    if OUTPUT == []:
        Log.critical('unable to find any orgs')
    else:
        for i in OUTPUT:
            ID = i['id']
            STATE = i['project_state']
            if not i['properties']:
                continue
            PROPERTIES = i['properties']['values']
            if STATE == 'CREATED' and PROPERTIES:
                X = re.search('sddc', str(PROPERTIES), re.IGNORECASE)
                if X:
                    DISPLAY_NAME = i['display_name'].ljust(50)
                    STR = DISPLAY_NAME + "\t" + ID
                    DATA.append(STR)
        DATA.sort()
        INPUT = 'SDDC ORG Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            target_org = CHOICE.split('\t')[1]
            DISPLAY_NAME = CHOICE.split('\t')[0].strip()
            if DISPLAY_NAME:
                Log.info(f"displaying {DISPLAY_NAME} details now, please wait...")
            else:
                Log.critical("please select an Org to continue...")
        except:
            Log.critical("please select an Org to continue...")
    return target_org, DISPLAY_NAME

def DeletedMenuResults(ctx):

    from csptools.cspclient import CSPclient
    CSP = CSPclient()
    DATA = []
    OUTPUT = CSP.list_orgs(ctx.obj['operator'], 'operator')
    if OUTPUT == []:
        Log.critical('unable to find any orgs')
    else:
        for i in OUTPUT:
            if i['project_state'] != 'DELETED':
                continue
            ID = i['id']
            DISPLAY_NAME = i['display_name'].ljust(50)
            STR = DISPLAY_NAME + "\t" + ID
            DATA.append(STR)
        DATA.sort()
        INPUT = 'ORG Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            target_org = CHOICE.split('\t')[1]
            DISPLAY_NAME = CHOICE.split('\t')[0].strip()
            if DISPLAY_NAME:
                Log.info(f"gathering {DISPLAY_NAME} details now, please wait...")
            else:
                Log.critical("please select an Org to continue...")
        except:
            Log.critical("please select an Org to continue...")
    return target_org, DISPLAY_NAME

def MenuResults(ctx):

    from csptools.cspclient import CSPclient
    CSP = CSPclient()
    DATA = []
    OUTPUT = CSP.list_orgs(ctx.obj['operator'], 'operator')
    if OUTPUT == []:
        Log.critical('unable to find any orgs')
    else:
        for i in OUTPUT:
            if i['project_state'] == 'DELETED' or i['project_state'] == 'DISABLED':
                continue
            ID = i['id']
            DISPLAY_NAME = i['display_name'].ljust(50)
            STR = DISPLAY_NAME + "\t" + ID
            DATA.append(STR)
        DATA.sort()
        INPUT = 'ORG Manager'
        CHOICE = runMenu(DATA, INPUT)
        try:
            CHOICE = ''.join(CHOICE)
            target_org = CHOICE.split('\t')[1]
            DISPLAY_NAME = CHOICE.split('\t')[0].strip()
            if DISPLAY_NAME:
                Log.info(f"gathering {DISPLAY_NAME} details now, please wait...")
            else:
                Log.critical("please select an Org to continue...")
        except:
            Log.critical("please select an Org to continue...")
    return target_org, DISPLAY_NAME

def pushd(dirname):
    global pushstack
    pushstack.append(os.getcwd())
    os.chdir(dirname)

def popd():
    global pushstack
    os.chdir(pushstack.pop())
