import os
import subprocess

from .common import FileDownloader
from ..utils import (
    encodeFilename,
)


class HlsFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        args = ['-y', '-i', url, '-f', 'mp4', '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc', tmpfilename]

        for program in ['avconv', 'ffmpeg']:
            try:
                subprocess.call([program, '-version'], stdout=(open(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
                break
            except (OSError, IOError):
                pass
        else:
            self.report_error(u'm3u8 download detected but ffmpeg or avconv could not be found')
        cmd = [program] + args

        retval = subprocess.call(cmd)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen(u'\r[%s] %s bytes' % (cmd[0], fsize))
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
            self.report_error(u'ffmpeg exited with code %d' % retval)
            return False
