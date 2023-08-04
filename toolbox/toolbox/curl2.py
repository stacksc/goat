import os, logging, requests, sys
from socket import gaierror
from json import dumps
from requests.auth import HTTPBasicAuth
    
def post(url=None, headers=None, data=None, json=None, auth=None, expected_codes=[200, 202]):
    return _call("POST", url, headers, data, json, auth, expected_codes)

def patch(url=None, headers=None, data=None, json=None, auth=None, expected_codes=[200]):
    return _call("PATCH", url, headers, data, json, auth, expected_codes)

def get(url=None, headers=None, data=None, json=None, auth=None, expected_codes=[200]):
    return _call("GET", url, headers, data, json, auth, expected_codes)

def put(url=None, headers=None, data=None, json=None, auth=None, expected_codes=[200]):
    return _call("PUT", url, headers, data, json, auth, expected_codes)

def delete(url=None, headers=None, data=None, json=None, auth=None, expected_codes=[200]):
    return _call("DELETE", url, headers, data, json, auth, expected_codes)

def _call(req_type, req_url=None, req_headers=None, req_data=None, req_json=None, req_auth=None, expected_codes=[200]):
    if req_url is None:
        critical('curl2: no URL provided')
        return None
    try:
        if type(req_auth) is dict:
            debug('curl2: adding HTTPBasicAuth to the request')
            RESPONSE = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json, auth=HTTPBasicAuth(req_auth['user'], req_auth['pass']))
        else:
            RESPONSE = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json) 
    except gaierror:
        critical(f"curl2: failed to resolve API endpoint - {req_url}")
    if _process_result(RESPONSE, expected_codes):
        return curl_repsonse(RESPONSE)
    else:
        critical(f'unexpected response from the API: {RESPONSE.status_code} \nendpoint: {req_url} \nresponse details:\n {RESPONSE.text}')

def _process_result(result, expected_codes):
    for code in expected_codes:
        if result.status_code == code:
            return True
    return False
    
def _check_arguments(req_url, req_headers, req_data, req_json, req_auth, expected_codes):
    if type(expected_codes) != list and type(req_url) != str and (type(req_headers) == dict or type(req_headers) == None) and (type(req_json) == dict or type(req_json) == None) and (type(req_data) == dict or type(req_data) == None) and (type(req_auth) == dict or type(req_auth) == None):
        return True
    return False

class curl_repsonse():
    def __init__(self, object):
        try:
            self.json=object.json()
        except requests.exceptions.JSONDecodeError:
            self.json=None
        self.status_code=object.status_code
        self.text=object.text
        self.response=object

#### logging

LOGNAME = 'curl2.log'
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
            'filename': f"{os.getenv('HOME')}/.{LOGNAME}",
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
    sys.exit(100)
