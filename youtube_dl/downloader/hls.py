from __future__ import unicode_literals

import os
import re
import subprocess

from ..postprocessor.ffmpeg import FFmpegPostProcessor
from .common import FileDownloader
from ..compat import (
    compat_urlparse,
    compat_urllib_request,
)
from ..utils import (
    encodeArgument,
    encodeFilename,
    sanitize_open,
)
from .http import HttpFD

class HlsFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        ffpp = FFmpegPostProcessor(downloader=self)
        if not ffpp.available:
            self.report_error('m3u8 download detected but ffmpeg or avconv could not be found. Please install one.')
            return False
        ffpp.check_version()

        args = [
            encodeArgument(opt)
            for opt in (ffpp.executable, '-y', '-i', url, '-f', 'mp4', '-c', 'copy', '-bsf:a', 'aac_adtstoasc')]
        args.append(encodeFilename(tmpfilename, True))

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
            self.report_error('%s exited with code %d' % (ffpp.basename, retval))
            return False


class NativeHlsFD(FileDownloader):
    """ A more limited implementation that does not require ffmpeg """

    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        (dest_stream, tmpfilename) = sanitize_open(tmpfilename, 'wb')

        self.to_screen(
            '[hlsnative] %s: Downloading m3u8 manifest' % info_dict['id'])
        data = self.ydl.urlopen(url).read()
        s = data.decode('utf-8', 'ignore')
        segment_urls = []
        for line in s.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                segment_url = (
                    line
                    if re.match(r'^https?://', line)
                    else compat_urlparse.urljoin(url, line))
                segment_urls.append(segment_url)

        downloader = HttpFD(
            self.ydl,
            {
                'continuedl': True,
                'quiet': True,
                'noprogress': True,
            }
        )
        for i, segurl in enumerate(segment_urls):
            self.to_screen(
                '[hlsnative] %s: Downloading segment %d / %d' %
                (info_dict['id'], i + 1, len(segment_urls)))
            success = downloader.download(tmpfilename + str(i), {'url': segurl})
            if not success:
                return False
        for i, segurl in enumerate(segment_urls):
            with open(tmpfilename + str(i), 'rb') as down:
                dest_stream.write(down.read())
            os.remove(tmpfilename + str(i))
        dest_stream.close()
        self.try_rename(tmpfilename, filename)
        fsize = os.path.getsize(encodeFilename(filename))
        self._hook_progress({
            'downloaded_bytes': fsize,
            'total_bytes': fsize,
            'filename': filename,
            'status': 'finished',
        })
        return True
