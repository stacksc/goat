import sys, os
try:
    import importlib_resources
except:
    from importlib import resources

def convert_slack_names(target_names):

    TARGET_CHANNELS = []
    MY_RESOURCES = importlib_resources.files("toolbox")
    DATA = (MY_RESOURCES / "slack_channels.lst")

    with open(DATA) as f:
        CONTENTS = f.read()
    for name in target_names:
        for line in CONTENTS.split('\n'):
            if line:
                item = line.split(",")[0]
                value = line.split(",")[1]
                if name == item:
                    TARGET_CHANNELS.append(line.split(",")[1])
    if TARGET_CHANNELS:
        return TARGET_CHANNELS
    else:
        return target_names

