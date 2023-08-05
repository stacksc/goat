#!/bin/bash

_post_install {
    # your post isntall customization script goes here
    echo "no post install steps available"
}

_auto_complete {
    # adds autocomplete
    echo "no autocompletion available"
}

# standard wheel installation script; modify if needed
_wheel_install {
    if [[ ! -f ./dist ]]
    then
        echo "FAIL - missing directories"
        echo "It looks like we're missing files. Please make sure to clone the entire source for the module."
        echo "You can install with just the wheel file etc. manually. The script way requires all repo files locally"
    fi
    _WHL_PATH_=$(find ./dist -type f -name "*.whl")
    pip install $_WHL_PATH_
}

