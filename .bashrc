# custom .bashrc for goat bashrc lovers

# Source global definitions
if [ -f /etc/bashrc ]; then
  source /etc/bashrc
fi

if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]
then
  export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi

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
eval "$(_GOAT_COMPLETE=bash_source goat)"
