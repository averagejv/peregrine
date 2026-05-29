alias vim="nvim"
alias ff="fastfetch"
alias finder="dolphin ."
alias startenv="source /home/quicksort/Personal/dev/env/bin/activate"
alias showaliases="cat ~/.bash_aliases"
alias cdisk="cd /run/media/quicksort/SSD"
alias note="cd /run/media/quicksort/SSD && obsidian"
alias burp='/opt/burpsuite.sh'
alias obi='/opt/obsidian.AppImage'


alias gte="gnome-text-editor"
alias ghidra="/home/quicksort/Applications/ghidra_12.0_PUBLIC/ghidraRun"
alias notebook="cd /home/quicksort/Personal/ephemeral"
alias school="cd /home/quicksort/School/"
alias scapy="sudo /home/quicksort/Applications/scapy/run_scapy"
alias please="sudo"
alias clock='google-chrome --app=file:/home/quicksort/Personal/dev/clock/index3.html --full-screen'
alias jupyter='startenv && jupyter lab --no-browser'
alias vol='/home/quicksort/Personal/dev/globalenv/bin/vol'
alias ss='loupe "$(ls -t ~/Screenshots/* | head -n 1)"'

#tmux that i prolly wont even use
alias tmuxa=''
alias tmuxk='tmux kill-session -t '


# start tmux always
if [[ $- == *i* ]] && [[ -z "$TMUX" ]]; then
    exec tmux
fi

