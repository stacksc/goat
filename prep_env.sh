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
printf "INFO: AWS ACCESS KEY ID & SECRET KEY can be retrieved from: https://console.aws.amazon.com => Security Credentials"
printf "INFO: generate new keys if they are inactive, lost, etc...\n"
echo

function ask() {
  qcnt=$(expr $qcnt + 1)
  [[ -z ${USER} ]] && USER="$(whoami)"; export USER
  [[ -z ${GITDIR} ]] && GITDIR="/home/${USER}/git"; export GITDIR

  if [[ -z ${REGION} ]];
  then
    read -ep "[${qcnt}] Enter default home region [us-east-1]: " REGION; export REGION
  fi
  [[ -z ${REGION} ]] && REGION="us-east-1" && export REGION

  if [[ -z ${AWS_ACCESS_KEY_ID} ]];
  then
    qcnt=$(expr $qcnt + 1)
    read -ep "[${qcnt}] Enter AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID; export AWS_ACCESS_KEY_ID
  fi
  [[ -z ${AWS_ACCESS_KEY_ID} ]] && echo "INFO: please provide an access key id" && exit 1;

  if [[ -z ${AWS_SECRET_ACCESS_KEY} ]];
  then
    qcnt=$(expr $qcnt + 1)
    read -ep "[${qcnt}] Enter AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY; export AWS_SECRET_ACCESS_KEY
  fi
  [[ -z ${AWS_SECRET_ACCESS_KEY} ]] && echo "INFO: please provide the aws secret access key" && exit 1;

  if [[ -z ${SLACK_BOT_TOKEN} ]];
  then
    qcnt=$(expr $qcnt + 1)
    read -ep "[${qcnt}] Enter SLACK_BOT_TOKEN: " SLACK_BOT_TOKEN; export SLACK_BOT_TOKEN
  fi
  [[ -z ${SLACK_BOT_TOKEN} ]] && echo "INFO: please provide the slack bot token for GOAT to use for communication:" && exit 1
  qcnt=$(expr $qcnt + 1)
  SSH_PUB_KEY="$(cat ${HOME}/.ssh/id_rsa.pub)"
  SSH_PRV_KEY="$(cat ${HOME}/.ssh/id_rsa)"
}

function displayDetails() {

  echo
  echo "==================================================================================="
  printf "INFO: verify the following information is accurate:\n"
  echo "==================================================================================="
  echo

  printf "INFO: GUID User ID:                  ${USER}\n"
  printf "INFO: AWS_ACCESS_KEY_ID:             ${AWS_ACCESS_KEY_ID}\n"
  printf "INFO: AWS_SECRET_ACCESS_KEY:         ${AWS_SECRET_ACCESS_KEY}\n"
  printf "INFO: SLACK_BOT_TOKEN:               ${SLACK_BOT_TOKEN}\n"
  printf "INFO: GIT:                           ${GITDIR}\n"
  printf "INFO: REGION:                        ${REGION}\n"
  echo
}

if [[ -f "${ENV}" ]] && [[ ! -z "${ENV}" ]];
then
  qcnt=0
  read -ep "[${qcnt}] would you like to use ${ENV} for docker preparation? [y/n] " ANS
  case $ANS in
          y|Y) # ok we will not ask for input
               if [[ -z ${SSO_PASS} ]];
               then
                 get_sso;
                 qcnt=$(expr $qcnt + 1)
               fi
               source ${ENV} >/dev/null 2>&1
               ;;
          n|N) # ok we will ask for input
               ask;
               ;;
            *) # ok we will ask for input
               ask;
               ;;
  esac
else
  ask;
fi

displayDetails;

cat << EOF > $MYDIR/.env
REGION="${REGION}"
GITDIR="${GITDIR}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN}"
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
