import os, sys, logging, logging.config
from cryptography.fernet import Fernet

LOGNAME = 'fernet.log'
DICTCONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file_handler': {
            'level': 'INFO',
            'mode': 'a',
            'filename': f"{os.getenv('HOME')}/goat/.{LOGNAME}",
            'class': 'logging.FileHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['file_handler'],
            'level': 'INFO',
            'propagate': True
        },
    }
}

HOME = os.getenv('HOME')
os.makedirs(f'{HOME}/goat', exist_ok=True)
logging.config.dictConfig(DICTCONFIG)

def setup(KEYNAME):
    KEYFILE = f"{os.getenv('HOME')}/goat/.{KEYNAME}.key" 
    if not os.path.exists(KEYFILE):
        warn("Encryption key not detected. Generating a new one")
        KEY = Fernet.generate_key()
        with open(KEYFILE, 'wb') as KEYFILE:
            try:
                KEYFILE.write(KEY)
            except:
                critical(f"Failed to generate encryption key")
    else:
        with open(KEYFILE, 'rb') as KEYFILE:
            try:
                KEY = KEYFILE.read()
            except:
                critical(f"Failed to read encryption key")
    try:
        CIPHER = Fernet(KEY)
    except:
        critical(f"Failed to start encryption system")
    return CIPHER

def encrypt_string(KEYNAME, INPUTSTR, FILEPATH=None):
    CIPHER = setup(KEYNAME)
    ENCRYPTED_STR = CIPHER.encrypt(bytes(INPUTSTR, 'utf-8'))
    if FILEPATH is None:
        return ENCRYPTED_STR.decode('utf-8')
    with open(FILEPATH, 'wb') as DESTINATION:
        DESTINATION.write(ENCRYPTED_STR)

def encrypt_file(INPUTPATH, OUTPUTPATH=None):
    with open(INPUTPATH, 'r+') as INPUTFILE:
        DECRYPTED_STR = INPUTFILE.read()
        ENCRYPTED_STR = encrypt_string(DECRYPTED_STR)
        if OUTPUTPATH is not None:
            with open(OUTPUTPATH, 'wb') as DESTINATION:
                DESTINATION.write(ENCRYPTED_STR)
        else:
            INPUTFILE.truncate(0)
            INPUTFILE.seek(0)
            INPUTFILE.write(ENCRYPTED_STR)

def decrypt_string(KEYNAME, INPUTSTR):
    CIPHER = setup(KEYNAME)
    DECRYPTED_STR = CIPHER.decrypt(INPUTSTR.encode('utf-8'))
    return DECRYPTED_STR.decode()

def decrypt_file(INPUTPATH):
    with open(INPUTPATH, 'rb') as INPUTFILE:
        ENCRYPTED_STR = INPUTFILE.read()
    DECRYPTED_STR = decrypt_string(ENCRYPTED_STR)
    return DECRYPTED_STR

def error(msg):
    logging.error(msg)
    if logging.root.level == logging.INFO:
        print(f"ERROR: {msg}")

def info(msg, output=False):
    logging.info(msg)
    if logging.root.level == logging.INFO or output:
        print(f"INFO: {msg}")

def warn(msg):
    logging.warn(msg)
    if logging.root.level == logging.INFO:
        print(f"WARN: {msg}")

def debug(msg):
    logging.debug(msg)
    if logging.root.level == logging.DEBUG:
        print(f"DEBUG: {msg}")
    
def critical(msg):
    logging.critical(msg)
    logging.debug('exception: ', exc_info=True)
    print(f"CRITICAL: {msg}")
    sys.exit()
