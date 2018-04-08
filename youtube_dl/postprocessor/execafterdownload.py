from __future__ import unicode_literals

import subprocess
import sys

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

        # expose info to exec argument
        # youtube-dl -x -o "%(playlist_index)s - %(title)s.%(ext)s" --exec "id3v2 -T %(playlist_index)s -t %(title)s %(filepath)s" PLAYLIST_ID
        str_types = (str) if sys.version_info.major > 2 else (str, unicode)
        info = {}
        for key in information:
            value = information[key]
            info[key] = compat_shlex_quote(value) if isinstance(value, str_types) else value
        cmd = cmd % info

        self._downloader.to_screen('[exec] Executing command: %s' % cmd)
        retCode = subprocess.call(encodeArgument(cmd), shell=True)
        if retCode != 0:
            raise PostProcessingError(
                'Command returned error code %d' % retCode)

        return [], information
