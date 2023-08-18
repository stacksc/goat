import sys, os
try:
    import importlib_resources as resources
except:
    from importlib import resources

def get_accounts():

    TARGETS = []
    MY_RESOURCES = resources.files("toolbox")
    DATA = (MY_RESOURCES / "stage_accounts.csv")

    with open(DATA) as f:
        CONTENTS = f.read()
    for line in CONTENTS.split('\n'):
        if line:
            item = line.split(",")[0]
            value = line.split(",")[1]
            if name == item:
                TARGETS.append(line.split(",")[1])
    if TARGETS:
        return TARGETS
