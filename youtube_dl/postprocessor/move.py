from __future__ import unicode_literals

import subprocess
import os
import shutil

from .common import PostProcessor
from ..utils import PostProcessingError


class MovePP(PostProcessor):

    def __init__(self, downloader, destination):
        super(MovePP, self).__init__(downloader)
        self.destination = destination

    def run(self, information):
        source = os.path.abspath(information['filepath'])
        destination = os.path.abspath(self.destination)
        if not os.path.exists(source):
            raise PostProcessingError('Source file not available')
        if not os.path.exists(destination):
            raise PostProcessingError('Destination not available')
        self._downloader.to_screen(
            '[exec] Moving %s to %s' % (source, destination))
        shutil.move(source, destination)
        return [], information
