import os
import sys
import platform
import logging, logging.config
import json

class Log:
    def __init__(self, logname, level='1'):
        self.NAME = logname
        MODES = {
            '0': 'WARN',
            '1': 'INFO',
            '2': 'DEBUG'
        }
        self.MODE = MODES[str(level)]

    # V2 
    def setup(name,level=1):
        MODES = {
            0: 'WARN',
            1: 'INFO',
            2: 'DEBUG'
        }
        MODE = MODES[level]
        try:
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
                        'level': MODE,
                        'mode': 'a',
                        'filename': f"{os.getenv('HOME')}/goat/.{name}.log",
                        'class': 'logging.FileHandler',
                        'formatter': 'standard'
                    }
                },
                'loggers': {
                    '': {
                        'handlers': ['file_handler'],
                        'level': MODE,
                        'propagate': True
                    },
                }
            }
            logging.config.dictConfig(DICTCONFIG)
        except FileExistsError:
            sys.exit("ERROR: Unable to setup a logfile. Exiting")

    def startlog(self):    
        try:
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
                        'level': self.MODE,
                        'mode': 'a',
                        'filename': f"{os.getenv('HOME')}/goat/.{self.NAME}.log",
                        'class': 'logging.FileHandler',
                        'formatter': 'standard'
                    }
                },
                'loggers': {
                    '': {
                        'handlers': ['file_handler'],
                        'level': self.MODE,
                        'propagate': True
                    },
                }
            }
            logging.config.dictConfig(DICTCONFIG)
        except FileExistsError:
            sys.exit("ERROR: Unable to setup a logfile. Exiting")

    def error(msg):
        logging.error(msg)
        if logging.root.level == logging.INFO:
            print(f"ERROR: {msg}")

    def json(msg, output=False):
        logging.info(msg)
        if logging.root.level == logging.INFO or output:
            print(f"{msg}")

    def info(msg, output=False):
        logging.info(msg)
        if logging.root.level == logging.INFO or output:
            print(f"INFO: {msg}")

    def warn(msg):
        logging.warn(msg)
        if logging.root.level == logging.INFO:
            print(f"WARN: {msg}")

    def debug(*args):
        for arg in args:
            logging.debug(arg)
            if logging.root.level == logging.DEBUG:
                print(f"DEBUG: {arg}")
        
    def notify(msg, title, subtitle, link, cmd):
        # for mac raise notification for critical issues
        RES = platform.system()
        if 'Darwin' in RES:
            from pync import Notifier
            if link:
                try:
                    Notifier.notify(msg, title=title, subtitle=subtitle, open=link)
                except:
                    pass
            elif cmd:
                try:
                    Notifier.notify(msg, title=title, subtitle=subtitle, execute=cmd)
                except:
                    pass
            else:
                try:
                    Notifier.notify(msg, title=title, subtitle=subtitle)
                except:
                    pass

    def critical(msg):
        logging.critical(msg)
        logging.debug('exception: ', exc_info=True)
        print(f"CRITICAL: {msg}")
        sys.exit()
        
