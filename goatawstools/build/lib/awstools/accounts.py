import sys, os
from toolbox.misc import detect_environment
try:
    import importlib_resources as resources
except:
    from importlib import resources

def get_accounts(target_names):

    TARGETS = []
    RESULT = detect_environment()
    MY_RESOURCES = resources.files("toolbox")
    if 'prod' in RESULT:
        DATA = (MY_RESOURCES / "prod_accounts.lst")
    else:
        DATA = (MY_RESOURCES / "stage_accounts.lst")

    target_names = ''.join(target_names)
    with open(DATA) as f:
        CONTENTS = f.read()
    for line in CONTENTS.split('\n'):
        if line:
            item = line.split(",")[0]
            value = line.split(",")[1]
            if item == target_names:
                TARGETS.append(line.split(",")[1])
    if TARGETS:
        return TARGETS
    else:
        return target_names

