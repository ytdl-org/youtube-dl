from __future__ import unicode_literals

from .common import FileDownloader

from ..utils import prepend_extension


class MultiPartFD(FileDownloader):

    FD_NAME = 'multipart'

    def real_download(self, filename, info_dict):
        parts = info_dict['parts']
        self.to_screen('[%s] Total parts: %d' % (self.FD_NAME, len(parts)))

        for i in range(len(parts)):
            fd = get_suitable_downloader(parts[i], self.params)(self.ydl, self.params)
            frag_filename = prepend_extension(filename, 'part%d' % i)
            success = fd.download(frag_filename, parts[i])
            if not success:
                return False
            # We only download the first fragment during the test
            if self.params.get('test', False):
                break

        return True

# workaround circular imports
from .__init__ import get_suitable_downloader
