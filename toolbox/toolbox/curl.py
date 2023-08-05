import os, json, logging, requests
from socket import gaierror
from requests.auth import HTTPBasicAuth
    
def post(url, headers=None, data=None, rjson=None, raw=False, auth=None, v2=False):
    if rjson is not None:
        json.dumps(rjson)
    return call("POST", url, headers, data, rjson, raw, auth)

def patch(url, headers=None, data=None, rjson=None, raw=False, auth=None, v2=False):
    if rjson is not None:
        json.dumps(rjson)
    return call("PATCH", url, headers, data, rjson, raw, auth)

def get(url, headers=None, data=None, rjson=None, raw=False, auth=None, v2=False):
    if rjson is not None:
        json.dumps(rjson)
    return call("GET", url, headers, data, rjson, raw, auth)

def put(url, headers, data=None, rjson=None, raw=False, auth=None, v2=False):
    if rjson is not None:
        json.dumps(rjson)
    return call("PUT", url, headers, data, rjson, raw, auth)

def delete(url, headers, data=None, rjson=None, raw=False, auth=None, v2=False):
    if rjson is not None:
        json.dumps(rjson)
    return call("DELETE", url, headers, data, rjson, raw, auth)

def call(req_type, req_url, req_headers=None, req_data=None, req_json=None, raw=False, req_auth=None, v2=False):
    if not v2:
        if raw:
            try: 
                if type(req_auth) is dict:
                    response = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json, auth=HTTPBasicAuth(req_auth['user'], req_auth['pass'])) 
                else:
                    response = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json) 
                info(f"\n{response.json}")
                return response.json
            except:
                critical(f"Failure running API call - code: {response}")
                return None
        try:
            if type(req_auth) is dict:
                response = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json, auth=HTTPBasicAuth(req_auth['user'], req_auth['pass'])) 
            else:
                response = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json) 
        except gaierror:
            critical(f"Unable to resolve API endpoint - {req_url} - possible issue with DNS")
            return None
        except:
            critical(f"Failure running API call - code: {response}")
            return None
        try:
            return response.json()
        except:
            return response
    else:
        try:
            if type(req_auth) is dict:
                response = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json, auth=HTTPBasicAuth(req_auth['user'], req_auth['pass']))
            else:
                response = requests.request(method=req_type, url=req_url, headers=req_headers, data=req_data, json=req_json) 
            return response
        except gaierror:
            critical(f"Unable to resolve API endpoint - {req_url} - possible issue with DNS")
        except:
            critical(f"Failure running API call - code: {response}")     
            
#### logging

LOGNAME = 'curl.log'
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
