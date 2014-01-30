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

# This specific script just adds the downloaded folder to the end of the $PATH,
# which allows the contained youtube-dl executable to be found.
export PATH=${PATH}:$(dirname $0)
