#!/usr/bin/env bash

_post_install() {
    # your post isntall customization script goes here
    echo "INFO: running post-install scripts now, please wait"
}

_general() {
  GENERAL=${HOME}/.generalrc
  [[ -f ${GENERAL} ]] && rm -f ${GENERAL} >/dev/null 2>&1
  TYPE=$(echo $SHELL | grep "bash" >/dev/null 2>&1; echo $?)
  if [ $TYPE -ne 0 ];
  then
    TYPE=$(echo $SHELL | grep "zsh" >/dev/null 2>&1; echo $?)
    if [ $TYPE -eq 0 ];
    then
      # we are zsh
      echo "autoload -U bashcompinit; bashcompinit" >> ${GENERAL}
      echo 'source ${HOME}/.govopsrc' >> ${GENERAL}
      chk=$(cat ${HOME}/.zshrc | grep "source \${HOME}/.generalrc" >/dev/null 2>&1; echo $?)
      if [ $chk -ne 0 ];
      then
        echo 'source ${HOME}/.generalrc' >> ${HOME}/.zshrc
      fi
    fi
  else
    # we are bash
    echo "bind 'TAB:menu-complete'" >> ${GENERAL}
    echo "bind 'set show-all-if-ambiguous on'" >> ${GENERAL}
    echo "bind 'set completion-ignore-case on'" >> ${GENERAL}
    echo 'source ${HOME}/.govopsrc' >> ${GENERAL}
    CHK=$(cat ${HOME}/.bashrc | grep "source \${HOME}/.generalrc" >/dev/null 2>&1; echo $?)
    if [ $CHK -ne 0 ];
    then
      echo 'source ${HOME}/.generalrc' >> ${HOME}/.bashrc
    fi
  fi
}

_auto_complete() {
    # adds autocomplete
    echo "INFO: setting up auto-completion now"
    type=$(echo $SHELL | grep "bash" >/dev/null 2>&1; echo $?)
    if [ $type -ne 0 ];
    then
      type=$(echo $SHELL | grep "zsh" >/dev/null 2>&1; echo $?)
      # check shell if zsh
      if [ $type -eq 0 ];
      then
        # the type check here is redundant
        # we are zsh
        if [ -f ${HOME}/.govopsrc ];
        then
          chk=$(cat ${HOME}/.govopsrc | grep "slackclient" >/dev/null 2>&1; echo $?)
          if [ $chk -ne 0 ];
          then
            echo 'eval "$(register-python-argcomplete slackclient)"' >> ${HOME}/.govopsrc
          fi
        else
          echo 'eval "$(register-python-argcomplete slackclient)"' >> ${HOME}/.govopsrc
        fi
      fi
    else
      # we are bash
      if [ -f ${HOME}/.govopsrc ];
      then
        chk=$(cat ${HOME}/.govopsrc | grep "slackclient" >/dev/null 2>&1; echo $?)
        if [ $chk -ne 0 ];
        then
          echo 'eval "$(register-python-argcomplete slackclient)"' >> ${HOME}/.govopsrc
        fi
      else
        echo 'eval "$(register-python-argcomplete slackclient)"' >> ${HOME}/.govopsrc
      fi
    fi
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
_general;
_auto_complete;
