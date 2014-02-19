# This allows the youtube-dl command to be installed in ZSH using antigen.
# Antigen is a bundle manager. It allows you to enhance the functionality of
# your zsh session by installing bundles and themes easily.

# Antigen documentation:
# http://antigen.sharats.me/
# https://github.com/zsh-users/antigen

# Install youtube-dl:
# antigen bundle rg3/youtube-dl
# Bundles installed by antigen are available for use immediately.

# Update youtube-dl (and all other antigen bundles):
# antigen update

# The antigen command will download the git repository to a folder and then
# execute an enabling script (this file). The complete process for loading the
# code is documented here:
# https://github.com/zsh-users/antigen#notes-on-writing-plugins

# This specific script just aliases youtube-dl to the python script that this
# library provides. This requires updating the PYTHONPATH to ensure that the
# full set of code can be located.
alias youtube-dl="PYTHONPATH=$(dirname $0) $(dirname $0)/bin/youtube-dl"
