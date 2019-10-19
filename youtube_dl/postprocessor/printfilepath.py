from __future__ import unicode_literals

from .common import PostProcessor


class PrintFilePathPP(PostProcessor):
    def __init__(self, downloader):
        super(PrintFilePathPP, self).__init__(downloader)

    def run(self, information):
        self._downloader.to_stdout(information['filepath'])
        return [], information
