#!/usr/bin/env bash

terminal=$(tty)
GREEN="\\033[1;32m"
WHITE="\\033[1;97m"
RED="\\033[1;31m"
YELLOW="\\033[1;33m"
MAGENTA="\\033[1;34m"
CYAN="\\033[1;36m"
BLUE="\\033[38;5;69m"
ORANGE="\\033[38;5;172m"
COLOR_OFF="\\033[0m"
BOOTUP=color
RES_COL=110
MOVE_TO_COL="echo -en \\033[${RES_COL}G"
SETCOLOR_SUCCESS="echo -en \\033[1;32m"
SETCOLOR_FAILURE="echo -en \\033[1;31m"
SETCOLOR_WARNING="echo -en \\033[1;33m"
SETCOLOR_NORMAL="echo -en \\033[0;39m"
SCRIPT=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)/`basename "${BASH_SOURCE[0]}"`
MYDIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
BASE=$(dirname ${MYDIR})
ERROR=0
DATE=$(date +'%s')
SLIDE="\\033[25G"
HOST=$(hostname)
PY=$(which python)
[[ -z $PY ]] && PY=$(which python3)

########################################################################
# success message in GREEN                                             #
########################################################################

function echo_success() {
  $SETCOLOR_SUCCESS
  [ "$BOOTUP" = "color" ] && $MOVE_TO_COL
  echo -n "["
  [ "$BOOTUP" = "color" ] && $SETCOLOR_SUCCESS
  echo -n $"  OK  "
  [ "$BOOTUP" = "color" ] && $SETCOLOR_SUCCESS
  echo -n "]"
  $SETCOLOR_NORMAL
  printf $COLOR_OFF
  echo
  return 0
}

########################################################################
# failure message in RED                                               #
########################################################################

function echo_failure() {
  $SETCOLOR_FAILURE
  [ "$BOOTUP" = "color" ] && $MOVE_TO_COL
  echo -n "["
  [ "$BOOTUP" = "color" ] && $SETCOLOR_FAILURE
  echo -n $" FAIL "
  [ "$BOOTUP" = "color" ] && $SETCOLOR_FAILURE
  echo -n "]"
  $SETCOLOR_NORMAL
  printf $COLOR_OFF
  echo
  return 1
}

########################################################################
# warning message in YELLOW                                            #
########################################################################

function echo_warning() {
  $SETCOLOR_WARNING
  [ "$BOOTUP" = "color" ] && $MOVE_TO_COL
  echo -n "["
  [ "$BOOTUP" = "color" ] && $SETCOLOR_WARNING
  echo -n $"  WARNING  "
  [ "$BOOTUP" = "color" ] && $SETCOLOR_WARNING
  echo -n "]"
  $SETCOLOR_NORMAL
  printf $COLOR_OFF
  echo
  return 0
}

####################################################################
# function to disable stdout and stderr                            #
####################################################################

function disable_output() {
  exec 3>&1 4>&2
  exec 1>/dev/null 2>&1
}

####################################################################
# function to enable stdout and stderr                             #
####################################################################

function enable_output() {
  # Restore descriptors
  exec 1>&3 2>&4
  # Close the descriptors
  exec 3>&- 4>&-
}

function trap_exit() {

  printf "\n\n${RED}**********************************************************************\n"
  printf "*                                                                    *\n"
  printf "* INTERRUPT: program received an interrupt...EXITING                 *\n"
  printf "                                                                    *\n"
  printf "**********************************************************************${COLOR_OFF}\n"
  printf "\n"

  stty echo
  exit 0
}

trap 'trap_exit; \
      exit 1' 1 2 3 15

function usage() {
  printf "\n${BLUE}Help Documentation${COLOR_OFF}: ${SCRIPT}\n"
  printf "\n${ORANGE}INFO${COLOR_OFF}: perform bulk operations to rebuild wheels for specific modules and run unit tests\n\n"
  printf "${BLUE}--action${COLOR_OFF}${SLIDE} supply one of the following actions: [rebuild/install/sync]$(tput sgr0)\n"
  printf "${BLUE}--target${COLOR_OFF}${SLIDE} supply the specific module to action, or supply keyword \"all\" for all modules$(tput sgr0)\n"
  printf "${BLUE}--help${COLOR_OFF}${SLIDE} show this help message$(tput sgr0)\n\n"
  exit 0
}

function chk_os() {
  case "$(uname -s)" in
        Darwin) # darwin
                MYOS="MAC"
                ;;
         Linux) # linux
                MYOS="LINUX"
                ;;
         CYGWIN*|MINGW32*|MSYS*|MINGW*) # windows
                MYOS="WINDOWS"
                ;;
             *) # other
                MYOS="OTHER"
                ;;
  esac
}

pushd $MYDIR >/dev/null
printf "${COLOR_OFF}"

while test $# -gt 0;
do
  case "$1" in
   --target) # this will be our target
	     shift
	     TARGET=$1
	     shift
	     ;;
   --action) # action
	     shift
	     ACTION=$1
	     shift
	     ;;
          *) # help
             usage;
             exit 1
             ;;
  esac
done

if [[ -z ${TARGET} ]];
then
  printf "INFO: target cannot be empty, i.e:\n     ./bulk.sh --target all --action rebuild"
  exit
fi

if [[ "${ACTION}" == "sync" ]];
then
  printf "would you like to sync from repository to local disk? (y/n): "
  read ANS
  if [ $TARGET == "all" ]; then
    for folder in $(pwd)/*;
    do
      chk=$(find ${folder} -name "pyproject.toml")
      [[ -z ${chk} ]] && continue
      if [[ -d "${folder}" ]] && [[ ! "${folder}" =~ "template" ]] && [[ ! "${folder}" =~ "builds" ]];
      then
        cd ${folder}
	BASE=$(basename $(pwd))
	FULL=$(pwd)
	if [[ ${ANS} == "Y" ]] || [[ ${ANS} == "y" ]];
	then
          sudo rsync -av ./${BASE}/* /opt/homebrew/lib/python3.11/site-packages/${BASE}/
	  sudo chown -R root:root /opt/homebrew/lib/python3.11/site-packages/${BASE}
        else
          sudo rsync -av /opt/homebrew/lib/python3.11/site-packages/${BASE}/* ./${BASE}/
	fi
      fi
    done
  else
    chk=$(find ${TARGET} -name "pyproject.toml")
    [[ ! -z ${chk} ]] && cd $TARGET
    BASE=$(basename $(pwd))
    FULL=$(pwd)
    if [[ ${ANS} == "Y" ]] || [[ ${ANS} == "y" ]];
    then
        sudo rsync -av ./${BASE}/* /opt/homebrew/lib/python3.11/site-packages/${BASE}/
        sudo chown -R root:root /opt/homebrew/lib/python3.11/site-packages/${BASE}
    else
        sudo rsync -av /opt/homebrew/lib/python3.11/site-packages/${BASE}/* ./${BASE}/
    fi
  fi
  sudo chown -R ${LOGNAME}:staff ~/git/goat
  exit 0
fi

printf "INFO: checking for the build module"
if [[ $(pip3 show build 2>&1) == "WARNING: Package(s) not found: build" ]]; then
  echo_warning
  pip3 install build
else
  echo_success
fi

if [ $TARGET == "all" ]; then
  for folder in $(pwd)/*;
  do
    if [[ -d "${folder}" ]] && [[ ! "${folder}" =~ "template" ]] && [[ ! "${folder}" =~ "builds" ]];
    then
      chk=$(find ${folder} -name "pyproject.toml")
      [[ -z ${chk} ]] && continue
      cd $folder
      if [[ ${ACTION} != "test" ]]; then
        if [[ ${ACTION} != "install" ]]; then
          [[ -d ./build ]] && rm -rf ./build >/dev/null 2>&1
          $PY -m build --wheel --sdist
        fi
        name=$(basename $folder)
        pip3 uninstall -y $name
        pip3 install $(find ./dist -type f -name "*.whl" | sort -nr | head -n 1) --no-cache-dir
      else
        chk=$(find ${folder} -name "tests.py")
        [[ -z ${chk} ]] && continue
        printf "INFO: running $ACTION on $(basename $folder)"
        $PY -m unittest tests > /tmp/test_${name} 2>&1
        test=$(cat /tmp/test_${name} | grep OK)
        [[ -z ${test} ]] && echo_failure || echo_success
      fi
    fi
  done
else
  chk=$(find ${TARGET} -name "pyproject.toml")
  [[ -z ${chk} ]] && continue
  cd $TARGET
  if [[ ${ACTION} != "test" ]]; then
    if [[ ${ACTION} != "install" ]]; then
      [[ -d ./build ]] && rm -rf ./build >/dev/null 2>&1
      $PY -m build --wheel --sdist
    fi
    pip3 uninstall -y ${TARGET}
    pip3 install $(find ./dist -type f -name "*.whl" | sort -nr | head -n 1) --no-cache-dir
  else
    chk=$(find ${folder} -name "tests.py")
    [[ -z ${chk} ]] && continue
    printf "INFO: running $ACTION on $(basename $folder)"
    $PY -m unittest tests > /tmp/test_${name} 2>&1
    test=$(cat /tmp/test_${name} | grep OK)
    [[ -z ${test} ]] && echo_failure  || echo_success
  fi
fi

chk_os;

TYPE=$(echo $SHELL | grep "zsh" >/dev/null 2>&1; echo $?)
# do the following on a mac for zsh everytime for sanity purposes
if [[ $MYOS == "MAC" ]] && [[ $TYPE -eq 0 ]];
then
  # if the OS is mac create a completion file
  cat << 'EOF' > ~/goat_completion.sh
fpath=(~/func $fpath)
autoload -U compinit
compinit
EOF
  [[ -f ${MYDIR}/aliases ]] && cat ${MYDIR}/aliases >> ${HOME}/goat_completion.sh
  # if the shell really is ZSH then setup zshrc file
  chk=$(cat ${HOME}/.zshrc | grep "source ~/goat_completion.sh" >/dev/null 2>&1; echo $?)
  if [[ $chk -ne 0 ]];
  then
    cat << 'EOF' >> ~/.zshrc
source ~/goat_completion.sh
EOF
  fi
  cp -rfp ${MYDIR}/func ${HOME}/ >/dev/null 2>&1
  echo
  echo "INFO: please source your profile for shell changes to take effect."
  echo "INFO: run the following command to source zshrc: source ${HOME}/.zshrc"
  echo
fi

if [[ $(which click-man >/dev/null 2>&1; echo $?) -eq 0 ]]
then
  if [ -d /opt/homebrew/share/man/man1 ];
  then
    click-man goat -t /opt/homebrew/share/man/man1
    echo
    echo "INFO: make sure the following line exists in /etc/man.conf:"
    echo "MANPATH_MAP     /opt/homebrew/bin       /usr/local/share/man"
  fi
fi

TYPE=$(echo $SHELL | grep "bash" >/dev/null 2>&1; echo $?)
if [ $TYPE -eq 0 ];
then
  echo
  echo "INFO: please source your profile for shell changes to take effect."
  echo "INFO: run the following command to source bashrc: source ${HOME}/.bashrc"
  echo
  cat << 'EOF' > ~/goat_completion.sh
# custom .bashrc for goat

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]
then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# vars
export GREEN="\\033[1;32m"
export WHITE="\\033[1;97m"
export RED="\\033[1;31m"
export YELLOW="\\033[1;33m"
export MAGENTA="\\033[1;35m"
export COLOR_OFF="\\033[0m"
export ENHANCD_COMMAND=ecd
export HISTFILE=~/.zsh_history
export HISTFILESIZE=50000000
export HISTSIZE=$HISTFILESIZE
export SAVEHIST=$HISTSIZE
export HISTIGNORE='l:ls:la:ll:w'
export HISTCONTROL=ignoredups:ignorespace
export HISTTIMEFORMAT='%F %T '
export HIST_STAMPS="mm/dd/yyyy"
export CLICOLOR=1
export PAGER='less'
export LESS='CMifSR --tabs=4'
export LESSCHARSET='utf-8'
export GIT_PAGER=$PAGER
export MLR_CSV_DEFAULT_RS='lf'

# Creates an archive (*.tar.gz) from given directory.
function maketar() {
  tar cvzpf "${1%%/}.tar.gz" "${1%%/}/"
  chmod 777 "${1%%/}.tar.gz"
}

# Create a ZIP archive of a file or folder.
function makezip() { zip -r "${1%%/}.zip" "$1" ; }

# get absolute path of argument
abspath () { case "$1" in /*)printf "%s\n" "$1";; *)printf "%s\n" "$PWD/$1";; esac; }

# load settings only if we are interactive
if [ -t 1 ]; then
  bind 'TAB:menu-complete'
  bind 'set show-all-if-ambiguous on'
  bind 'set completion-ignore-case on'
  bind 'set menu-complete-display-prefix on'
  bind '"\e[Z":menu-complete-backward'
fi

[[ -f ${HOME}/load_prompt.sh ]] && source ${HOME}/load_prompt.sh >/dev/null 2>&1
EOF
  chk=$(cat ${HOME}/.bashrc | grep "source ~/goat_completion.sh" >/dev/null 2>&1; echo $?)
  if [[ $chk -ne 0 ]];
  then
    cat << 'EOF' >> ~/.bashrc
source ~/goat_completion.sh
EOF
  fi
fi

popd >/dev/null
