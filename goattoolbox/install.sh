#!/usr/bin/env bash

_post_install() {
    # your post isntall customization script goes here
    echo "INFO: running post-install scripts now, please wait"
}

# standard wheel installation script; modify if needed
_wheel_install() {
    if [[ ! -d ./dist ]]
    then
        echo "FAIL - missing directories"
        echo "It looks like we're missing files. Please make sure to clone the entire source for the module."
        echo "You can install with just the wheel file etc. manually. The script way requires all repo files locally"
    fi
    _WHL_PATH_=$(find ./dist -type f -name "*.whl")
    pip install $_WHL_PATH_
}

_post_install;
_wheel_install;
