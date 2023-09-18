if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]
then
  export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
