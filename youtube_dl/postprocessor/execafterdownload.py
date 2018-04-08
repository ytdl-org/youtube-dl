from __future__ import unicode_literals

import subprocess
import sys
import numbers

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
        info = {}

        for key in information:
            value = information[key]
            info[key] = compat_shlex_quote(value) if isinstance(value, (str, unicode)) else value

        # expose info to exec argument
        # youtube-dl -x -o "%(playlist_index)s - %(title)s.%(ext)s" --exec "id3v2 -T {0[playlist_index]} -t {0[title]} {0[filepath]}" PLAYLIST_ID
        cmd = cmd.format(info)

        self._downloader.to_screen('[exec] Executing command: %s' % cmd)
        retCode = subprocess.call(encodeArgument(cmd), shell=True)
        if retCode != 0:
            raise PostProcessingError(
                'Command returned error code %d' % retCode)

        return [], information
