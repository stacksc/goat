#!/bin/bash
##########################################################
#Please edit "User Configuration" section before using   #
##########################################################

#=========================================================
#Terminal Color Codes
#=========================================================
WHITE='\[\033[1;37m\]'
LIGHTGRAY='\[\033[0;37m\]'
GRAY='\[\033[1;30m\]'
BLACK='\[\033[0;30m\]'
RED='\[\033[0;31m\]'
LIGHTRED='\[\033[1;31m\]'
GREEN='\[\033[0;32m\]'
LIGHTGREEN='\[\033[1;32m\]'
BROWN='\[\033[0;33m\]' #Orange
YELLOW='\[\033[1;33m\]'
BLUE='\[\033[0;34m\]'
LIGHTBLUE='\[\033[1;34m\]'
PURPLE='\[\033[0;35m\]'
PINK='\[\033[1;35m\]' #Light Purple
CYAN='\[\033[0;36m\]'
LIGHTCYAN='\[\033[1;36m\]'
DEFAULT='\[\033[0m\]'

#=========================================================
# User Configuration
#=========================================================
# Colors
cLINES=$GRAY #Lines and Arrow
cBRACKETS=$GRAY # Brackets around each data item
cERROR=$LIGHTRED # Error block when previous command did not return 0
cSUCCESS=$GREEN  # When last command ran successfully and return 0
cTIME=$LIGHTGRAY # The current time
cMPX1=$YELLOW # Color for terminal multiplexer threshold 1
cMPX2=$RED # Color for terminal multiplexer threshold 2
cBGJ1=$YELLOW # Color for background job threshold 1
cBGJ2=$RED # Color for background job threshold 2
cSTJ1=$YELLOW # Color for background job threshold 1
cSTJ2=$RED # Color for  background job threshold 2
cSSH=$PINK # Color for brackets if session is an SSH session
cUSR=$LIGHTBLUE # Color of user
cUHS=$CYAN # Color of the user and hostname separator, probably '@'
cHST=$LIGHTGREEN # Color of hostname
cRWN=$RED # Color of root warning
cPWD=$BLUE # Color of current directory
cCMD=$DEFAULT # Color of the command you type

# Enable block
eNL=1  # Have a newline between previous command output and new prompt
eERR=1 # Previous command return status tracker
eTIME=1 # Enable time display
eMPX=1 # Terminal multiplexer tracker enabled
eSSH=1 # Track if session is SSH
eBGJ=1 # Track background jobs
eSTJ=1 # Track stopped jobs
eHOST=1 # Show user and host
ePWD=1 # Show current directory

# Block settins
MPXT1="0" # Terminal multiplexer threshold 1 value
MPXT2="2" # Terminal multiplexer threshold 2 value
BGJT1="0" # Background job threshold 1 value
BGJT2="2" # Background job threshold 2 value
STJT1="0" # Stopped job threshold 1 value
STJT2="2" # Stopped job threshold 2 value
UHS="@"

function promptcmd()
{
        PREVRET=$?

        #=========================================================
        #check if user is in ssh session
        #=========================================================
        if [ $eSSH -eq 1 ]; then
                if [[ $SSH_CLIENT ]] || [[ $SSH2_CLIENT ]]; then
                        lSSH_FLAG=1
                else
                        lSSH_FLAG=0
                fi
        fi

        #=========================================================
        # Insert a new line to clear space from previous command
        #=========================================================
        if [ $eNL -eq 1 ]; then
                PS1="\n"
        else
                PS1=""
        fi

        #=========================================================
        # Beginning of first line (arrow wrap around and color setup)
        #=========================================================
        PS1="${PS1}${cLINES}\342\224\214\342\224\200"

        #=========================================================
        # First Dynamic Block - Previous Command Error
        #=========================================================
        if [ $eERR -eq 1 ]; then
                if [ $PREVRET -ne 0 ] ; then
                        PS1="${PS1}${cBRACKETS}[${cERROR}:(${cBRACKETS}]${cLINES}\342\224\200"
                else
                        PS1="${PS1}${cBRACKETS}[${cSUCCESS}:)${cBRACKETS}]${cLINES}\342\224\200"
                fi
        fi

        #=========================================================
        # First static block - Current time
        #=========================================================
        if [ $eTIME -eq 1 ] ; then
                PS1="${PS1}${cBRACKETS}[${cTIME}\t${cBRACKETS}]${cLINES}\342\224\200"
        fi

        #=========================================================
        # Detached Screen Sessions
        #=========================================================
        if [ $eMPX -eq 1 ] ; then
                hTMUX=0
                hSCREEN=0
                MPXC=0
                hash tmux --help 2>/dev/null || hTMUX=1
                hash screen --version 2>/dev/null || hSCREEN=1
                if [ $hTMUX -eq 0 ] && [ $hSCREEN -eq 0 ] ; then
                        MPXC=$(echo "$(screen -ls | grep -c -i detach) + $(tmux ls 2>/dev/null | grep -c -i -v attach)" | bc)
                elif [ $hTMUX -eq 0 ] && [ $hSCREEN -eq 1 ] ; then
                        MPXC=$(tmux ls 2>/dev/null | grep -c -i -v attach)
                elif [ $hTMUX -eq 1 ] && [ $hSCREEN -eq 0 ] ; then
                        MPXC=$(screen -ls | grep -c -i detach)
                fi
                if [[ $MPXC -gt $MPXT2 ]] ; then
                        PS1="${PS1}${cBRACKETS}[${cMPX2}\342\230\220:${MPXC}${cBRACKETS}]${cLINES}\342\224\200"
                elif [[ $MPXC -gt $MPXT1 ]] ; then
                        PS1="${PS1}${cBRACKETS}[${cMPX1}\342\230\220:${MPXC}${cBRACKETS}]${cLINES}\342\224\200"
                fi
        fi
        #=========================================================
        # Backgrounded running jobs
        #=========================================================
        if [ $eBGJ -eq 1 ] ; then
                BGJC=$(jobs -r | wc -l )
                if [ $BGJC -gt $BGJT2 ] ; then
                        PS1="${PS1}${cBRACKETS}[${cBGJ2}&:${BGJC}${cBRACKETS}]${cLINES}\342\224\200"
                elif [ $BGJC -gt $BGJT1 ] ; then
                        PS1="${PS1}${cBRACKETS}[${cBGJ1}&:${BGJC}${cBRACKETS}]${cLINES}\342\224\200"
                fi
        fi

        #=========================================================
        # Stopped Jobs
        #=========================================================
        if [ $eSTJ -eq 1 ] ; then
                STJC=$(jobs -s | wc -l )
                if [ $STJC -gt $STJT2 ] ; then
                        PS1="${PS1}${cBRACKETS}[${cSTJ2}\342\234\227:${STJC}${cBRACKETS}]${cLINES}\342\224\200"
                elif [ $STJC -gt $STJT1 ] ; then
                        PS1="${PS1}${cBRACKETS}[${cSTJ1}\342\234\227:${STJC}${cBRACKETS}]${cLINES}\342\224\200"
                fi
        fi

        #=========================================================
        # Second Static block - User@host
        #=========================================================
        # set color for brackets if user is in ssh session
        if [ $eSSH -eq 1 ] && [ $lSSH_FLAG -eq 1 ] ; then
                sesClr="$cSSH"
        else
                sesClr="$cBRACKETS"
        fi
        # don't display user if root
        if [ $EUID -eq 0 ] ; then
                PS1="${PS1}${sesClr}[${cRWN}!"
        else
                PS1="${PS1}${sesClr}[${cUSR}\u"
        fi
        # Host Section
        if [ $eHOST -eq 1 ] || [ $lSSH_FLAG -eq 1 ] ; then   # Host is optional only without SSH
                PS1="${PS1}${cUHS}${UHS}${cHST}\h${sesClr}]${cLINES}\342\224\200"
        else
                PS1="${PS1}${sesClr}]${cLINES}\342\224\200"
        fi

        #=========================================================
        # Third Static Block - Current Directory
        #=========================================================
        if [ $ePWD -eq 1 ]; then
                PS1="${PS1}[${cPWD}\w${cBRACKETS}]"
        fi

        #=========================================================
        # Second Line
        #=========================================================
        PS1="${PS1}\n${cLINES}\342\224\224\342\224\200\342\224\200> ${cCMD}"
}

function load_prompt () {
    # Get PIDs
    #local parent_process=$(tr -d '\0' < /proc/$PPID/cmdline | cut -d \. -f 1)
    #local my_process=$(tr -d '\0' < /proc/$$/cmdline | cut -d \. -f 1)

    if  [[ $parent_process == script* ]]; then
        PROMPT_COMMAND=""
        PS1="\t - \# - \u@\H { \w }\$ "
    elif [[ $parent_process == emacs* || $parent_process == xemacs* ]]; then
        PROMPT_COMMAND=""
        PS1="\u@\h { \w }\$ "
    else
        export DAY=$(date +%A)
        PROMPT_COMMAND=promptcmd
     fi
    export PS1 PROMPT_COMMAND
}

load_prompt
