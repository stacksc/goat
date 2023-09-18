#!/usr/bin/env bash
#### INFO: this needs work
#### INFO: meant to help prepare our docker image, but needs some attention

GREEN="\\033[1;32m"
WHITE="\\033[1;97m"
RED="\\033[1;31m"
YELLOW="\\033[1;33m"
MAGENTA="\\033[1;34m"
CYAN="\\033[1;36m"
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
ENV=$(find ${HOME} -maxdepth 1 -name ".env" -print 2>/dev/null)
qcnt=0

pushd $MYDIR >/dev/null
printf "${COLOR_OFF}"

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

function chk_os() {
  case "$(uname -s)" in
        Darwin) # darwin
                OS="MAC"
                ;;
         Linux) # linux
                OS="LINUX"
                ;;
         CYGWIN*|MINGW32*|MSYS*|MINGW*) # windows
                OS="WINDOWS"
                ;;
             *) # other
                OS="OTHER"
                ;;
  esac
}

function trap_exit() {

  printf "\n\n${RED}**********************************************************************\n"
  printf "*                                                                    *\n"
  printf "* INTERRUPT: program received an interrupt...EXITING                 *\n"
  printf "*                                                                    *\n"
  printf "**********************************************************************${COLOR_OFF}\n"
  printf "\n"

  stty echo
  # these files get removed during an interrupt; this function puts Humpty Dumpty back together again
  exit 0
}

chk_os;

trap 'trap_exit; \
      exit 1' 1 2 3 15

printf "${COLOR_OFF}"

printf "INFO: preparing to build our docker container\n"
printf "      using multiple tools, scripts and utilities to make the magic happen. Enjoy!\n"
echo

[[ -z ${USER} ]] && USER="$(whoami)"; export USER
[[ -z ${GITDIR} ]] && GITDIR="/home/${USER}/git"; export GITDIR

SSH_PUB_KEY="$(cat ${HOME}/.ssh/id_rsa.pub)"
SSH_PRV_KEY="$(cat ${HOME}/.ssh/id_rsa)"

cat << EOF > $MYDIR/.env
GITDIR="${GITDIR}"
USER="${USER}"
SSH_PUB_KEY="${SSH_PUB_KEY}"
SSH_PRV_KEY="${SSH_PRV_KEY}"
LOGNAME="${USER}"
EOF

printf "INFO: starting the docker build process, which will stop any running GOAT containers, & prune prior to starting\n"
echo
docker stop $(docker ps | grep goat | awk '{print $1}') >/dev/null 2>&1 && yes | docker system prune
echo
docker build . -t goat --build-arg MYUSER=${USER} --secret id=my_env,src=.env 
ret=$?
echo
[[ $ret -eq 0 ]] && docker run -d -it --memory="4g" --cpus="3.0" goat
ret=$?
echo
[[ $ret -eq 0 ]] && docker ps -a
echo
echo "INFO: login to goat now with: docker exec -it \$(docker ps -a| grep goat | awk '{print \$1}') bash -l"
echo "INFO: copying .env to ${HOME} and out of the main repository"
cp -f ${MYDIR}/.env ${HOME}/.env 2>/dev/null
[[ -f ${MYDIR}/.env ]] && rm -f ${MYDIR}/.env >/dev/null 2>&1
echo "INFO: goat docker build is complete!"
echo
popd >/dev/null
