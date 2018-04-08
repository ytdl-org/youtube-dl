from __future__ import unicode_literals

import subprocess

from .common import PostProcessor
from ..compat import compat_shlex_quote
from ..utils import (
    encodeArgument,
    PostProcessingError,
)


class ExecAfterDownloadPP(PostProcessor):
    def __init__(self, downloader, exec_cmd):
        super(ExecAfterDownloadPP, self).__init__(downloader)
        self.exec_cmd = exec_cmd

    def run(self, information):
        cmd = self.exec_cmd
        if '{}' not in cmd:
            cmd += ' {}'

        # expose the playlist_index and title variables to exec argument
        # youtube-dl -x -o "%(playlist_index)s - %(title)s.%(ext)s" --exec "id3v2 -T {playlist_index} -t {title} {}" PLAYLIST_ID
        cmd = cmd.replace('{}', compat_shlex_quote(information['filepath']))
        cmd = cmd.replace('{title}', compat_shlex_quote(information['title']))
        cmd = cmd.replace('{playlist_index}', str(information['playlist_index']))

        self._downloader.to_screen('[exec] Executing command: %s' % cmd)
        retCode = subprocess.call(encodeArgument(cmd), shell=True)
        if retCode != 0:
            raise PostProcessingError(
                'Command returned error code %d' % retCode)

        return [], information
