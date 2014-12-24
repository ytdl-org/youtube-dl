from __future__ import unicode_literals

import os
import subprocess

from .common import FileDownloader
from ..compat import compat_subprocess_get_DEVNULL
from ..utils import (
    encodeFilename,
)


class MplayerFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        args = [
            'mplayer', '-really-quiet', '-vo', 'null', '-vc', 'dummy',
            '-dumpstream', '-dumpfile', tmpfilename, url]
        # Check for mplayer first
        try:
            subprocess.call(
                ['mplayer', '-h'],
                stdout=compat_subprocess_get_DEVNULL(), stderr=subprocess.STDOUT)
        except (OSError, IOError):
            self.report_error('MMS or RTSP download detected but "%s" could not be run' % args[0])
            return False

        # Download using mplayer.
        retval = subprocess.call(args)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen('\r[%s] %s bytes' % (args[0], fsize))
            self.try_rename(tmpfilename, filename)
            self._hook_progress({
                'downloaded_bytes': fsize,
                'total_bytes': fsize,
                'filename': filename,
                'status': 'finished',
            })
            return True
        else:
            self.to_stderr('\n')
            self.report_error('mplayer exited with code %d' % retval)
            return False
