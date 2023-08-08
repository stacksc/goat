#!/usr/bin/env bash
# this is a test

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
JIRAURL1="https://servicedesk.eng.vmware.com"
JIRAURL2="https://jira.eng.vmware.com"
JIRAURL3="https://servicedesk.vmwarefed.com"
JIRAURL4="https://servicedesk.vmwarefedstg.com"
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

function get_sso() {
  qcnt=$(expr $qcnt + 1)
  echo -ne "[${qcnt}] Enter SSO PASSWORD: "

  unset password
  unset charcount
  unset char
  unset prompt
  unset SSO_PASS

  while IFS= read -p "$prompt" -r -s -n 1 char
  do
    if [[ $char == $'\0' ]] ; then
      break
    fi
    if [[ $char == $'' ]] ; then
      prompt=$'\b \b'
      password="${password%?}"
    else
      prompt='*'
      password+="$char"
    fi
  done
  SSO_PASS=$password
  echo
  export SSO_PASS
}

chk_os;
staging=$(whoami | grep "vmwarefedstg" >/dev/null 2>&1; echo $?)
prod=$(whoami | grep "vmwarefed" >/dev/null 2>&1; echo $?)

if [[ $staging -eq 0 ]] || [[ $prod -eq 0 ]];
then
  echo "INFO: not able to prep for docker build in production"
  exit 1
fi

trap 'trap_exit; \
      exit 1' 1 2 3 15

printf "${COLOR_OFF}"

printf "INFO: preparing to build our docker container\n"
printf "      using multiple tools, scripts and utilities to make the magic happen. Enjoy!\n"
echo
printf "INFO: AWS ACCESS KEY ID & SECRET KEY can be retrieved from: https://sks-gov-ctrl.signin.amazonaws-us-gov.com\n"
printf "INFO: generate new keys if they are inactive, lost, etc...\n"
echo

function ask() {
  qcnt=$(expr $qcnt + 1)
  [[ -z ${USER} ]] && USER="$(whoami)"; export USER
  [[ -z ${GITDIR} ]] && GITDIR="/home/${USER}/git"; export GITDIR

  if [[ -z ${REGION} ]];
  then
    read -ep "[${qcnt}] Enter default home region [us-gov-west-1]: " REGION; export REGION
  fi
  [[ -z ${REGION} ]] && REGION="us-gov-west-1" && export REGION

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
  [[ -z ${SLACK_BOT_TOKEN} ]] && echo "INFO: please provide the slack bot token for GOAT (stored in production password state)" && exit 1

  get_sso;
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
JIRAURL1="${JIRAURL1}"
JIRAURL2="${JIRAURL2}"
JIRAURL3="${JIRAURL3}"
JIRAURL4="${JIRAURL4}"
REGION="${REGION}"
GITDIR="${GITDIR}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN}"
USER="${USER}"
SSO_PASS="${SSO_PASS}"
SSH_PUB_KEY="${SSH_PUB_KEY}"
SSH_PRV_KEY="${SSH_PRV_KEY}"
JIRA_API_TOKEN="${SSO_PASS}"
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
cat ${MYDIR}/.env | grep -vE "SSO_PASS|JIRA_API_TOKEN" > ${HOME}/.env 2>/dev/null
[[ -f .env ]] && rm -f .env >/dev/null 2>&1
echo "INFO: goat docker build is complete!"
echo
popd >/dev/null
