import os, sys
import logging, logging.config

# reduce a json, aka keep only specified key:value pairs and discard others
# definitino dict shall be a collection of keys with either a none or a list value
# each key should hold a value None unless you intend to re-map a key from a source json
# for example, lets assume we have a json: { name: test, data: { config: { created: today } } }
# to produce a "reduced" json like so: { name: test, data: today } you'd need to pass a definition dict as follows:
# { name: None, data: ( data,config,created ) }
# lastly, json_dict can be set to True to reduce a "json of jsons"; ie { John: { age: 15, ht: 180 }, Sam: { age: 20, ht: 200 } }
def reduce_json(source_data, definition_dict, json_dict=False):
    if type(source_data) is list:
        RESULT = []
        for DATA in source_data:
            REDUCED_DATA = _reduce_json(DATA, definition_dict)
            RESULT.append(REDUCED_DATA)
    elif json_dict:
        RESULT = {}
        for KEY in source_data:
            REDUCED_DATA = _reduce_json(source_data[KEY], definition_dict)
            RESULT[KEY] = REDUCED_DATA
    else:
        RESULT = _reduce_json(source_data, definition_dict)
    return RESULT

# worker function for reduce_json
def _reduce_json(source_json, definition_dict):
    REDUCED_DATA = {}
    for KEY in definition_dict:
        VALUE = definition_dict[KEY]
        if VALUE is None:
            if KEY in source_json:
                REDUCED_DATA[KEY] = source_json[KEY]
            else:
                REDUCED_DATA[KEY] = ""
        elif type(VALUE) == dict:
            SUB_DATA = source_json[KEY]
            REDUCED_SUB_DATA = _reduce_json(SUB_DATA, VALUE)
            REDUCED_DATA[KEY] = REDUCED_SUB_DATA
        elif type(VALUE) is list:
            SUB_DATA = source_json
            for ENTRY in VALUE:
                try:
                    if ENTRY in SUB_DATA:
                        SUB_DATA = SUB_DATA[ENTRY]
                    else:
                        REDUCED_DATA[KEY] = None
                        break
                except TypeError:
                    REDUCED_DATA[KEY] = ""
            REDUCED_DATA[KEY] = SUB_DATA
        else:
            critical('error parsing json - toolbox.jsontools.filter_json')
    return REDUCED_DATA

def filter(source_data, filter, json_dict=False):
    if type(source_data) is list:
        RESULT = []
        for DATA in source_data:
            REDUCED_DATA = filter_json(DATA, filter)
            if REDUCED_DATA is not None:
                RESULT.append(REDUCED_DATA)
    elif json_dict:
        RESULT = {}
        for KEY in source_data:
            REDUCED_DATA = filter_json(source_data[KEY], filter)
            if REDUCED_DATA is not None:
                RESULT[KEY] = REDUCED_DATA
    else:
        RESULT = filter_json(source_data, filter)
    return RESULT

def filter_json(data, filter):
    FILTER_RESULTS = []
    if ',' in filter:
        FILTER = filter.split(',')
    else:
        FILTER = [ filter ] 
    for ITEM in FILTER:
        if ':' not in ITEM:
            warn(f'detected incorrect filter item {ITEM}; ignoring it')
            warn('to filter the json for key-value pairs, use "key:pair" format')
            warn('to look just for a key, or just for a value use: "key:" or ":value"' )
            break
        KEY,VALUE = ITEM.split(':',1)
        if ':' in VALUE:
            warn(f'detected incorrect filter item {ITEM}; ignoring it')
            warn('it is not allowed to use ":" character more than once')
            break
        FILTER_RESULTS.append(_filter_json(data, KEY, VALUE))
    for RESULT in FILTER_RESULTS:
        if RESULT == False:
            return None
    return data
        
def _filter_json(data, filter_key, filter_value):
    if filter_key != "" and filter_value != "":
        FOUND_KEY = False
        FOUND_VALUE = False
        for KEY in data:
            if KEY == filter_key:
                FOUND_KEY = True
            VALUE = data[KEY]
            if VALUE == filter_value:
                FOUND_VALUE = True
            elif type(VALUE) is dict:
                _filter_json(VALUE, filter_key, filter_value)
            else:
                FOUND_KEY = False
                FOUND_VALUE = False
            if FOUND_KEY and FOUND_VALUE:
                return True
        return False
    elif filter_key == "" and filter_value != "":
        FOUND_VALUE = False
        for KEY in data:
            VALUE = data[KEY]
            if VALUE == filter_value:
                FOUND_VALUE = True
            elif type(VALUE) is dict:
                _filter_json(VALUE, filter_key, filter_value)
            else:
                FOUND_VALUE = False
            if FOUND_VALUE:
                return True
        return False
    elif filter_key != "" and filter_value == "":
        FOUND_KEY = False
        for KEY in data:
            VALUE = data[KEY]
            if KEY == filter_key:
                FOUND_KEY = True
            elif type(VALUE) is dict:
                _filter_json(VALUE, filter_key, filter_value)
            else:
                FOUND_KEY = False
            if FOUND_KEY:
                return True
        return False
    else:
        return False

#### logging

LOGNAME = 'jsonfilter.log'
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
logging.config.dictConfig(DICTCONFIG)

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
