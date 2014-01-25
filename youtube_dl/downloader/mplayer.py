import os
import subprocess

from .common import FileDownloader
from ..utils import (
    encodeFilename,
)


class MplayerFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        args = ['mplayer', '-really-quiet', '-vo', 'null', '-vc', 'dummy', '-dumpstream', '-dumpfile', tmpfilename, url]
        # Check for mplayer first
        try:
            subprocess.call(['mplayer', '-h'], stdout=(open(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
        except (OSError, IOError):
            self.report_error(u'MMS or RTSP download detected but "%s" could not be run' % args[0])
            return False

        # Download using mplayer.
        retval = subprocess.call(args)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen(u'\r[%s] %s bytes' % (args[0], fsize))
            self.try_rename(tmpfilename, filename)
            self._hook_progress({
                'downloaded_bytes': fsize,
                'total_bytes': fsize,
                'filename': filename,
                'status': 'finished',
            })
            return True
        else:
            self.to_stderr(u"\n")
            self.report_error(u'mplayer exited with code %d' % retval)
            return False
