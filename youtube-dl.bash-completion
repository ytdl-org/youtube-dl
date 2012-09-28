__youtube-dl()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    opts="--all-formats --audio-format --audio-quality --auto-number --batch-file --console-title --continue --cookies --dump-user-agent --extract-audio --format --get-description --get-filename --get-format --get-thumbnail --get-title --get-url --help --ignore-errors --keep-video --list-extractors --list-formats --literal --match-title --max-downloads --max-quality --netrc --no-continue --no-mtime --no-overwrites --no-part --no-progress --output --password --playlist-end --playlist-start --prefer-free-formats --quiet --rate-limit --reject-title --retries --simulate --skip-download --srt-lang --title --update --user-agent --username --verbose --version --write-description --write-info-json --write-srt"

    if [[ ${cur} == * ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}

complete -F __youtube-dl youtube-dl
