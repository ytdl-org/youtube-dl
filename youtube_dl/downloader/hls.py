from __future__ import unicode_literals

import os
import re
import subprocess

from ..postprocessor.ffmpeg import FFmpegPostProcessor
from .common import FileDownloader
from ..utils import (
    compat_urlparse,
    compat_urllib_request,
    check_executable,
    encodeFilename,
)


class HlsFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        args = [
            '-y', '-i', url, '-f', 'mp4', '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            encodeFilename(tmpfilename, for_subprocess=True)]

        for program in ['avconv', 'ffmpeg']:
            if check_executable(program, ['-version']):
                break
        else:
            self.report_error('m3u8 download detected but ffmpeg or avconv could not be found. Please install one.')
            return False
        cmd = [program] + args

        ffpp = FFmpegPostProcessor(downloader=self)
        ffpp.check_version()

        retval = subprocess.call(cmd)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen('\r[%s] %s bytes' % (cmd[0], fsize))
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
            self.report_error('%s exited with code %d' % (program, retval))
            return False


class NativeHlsFD(FileDownloader):
    """ A more limited implementation that does not require ffmpeg """

    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

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

        is_test = self.params.get('test', False)
        remaining_bytes = self._TEST_FILE_SIZE if is_test else None
        byte_counter = 0
        with open(tmpfilename, 'wb') as outf:
            for i, segurl in enumerate(segment_urls):
                self.to_screen(
                    '[hlsnative] %s: Downloading segment %d / %d' %
                    (info_dict['id'], i + 1, len(segment_urls)))
                seg_req = compat_urllib_request.Request(segurl)
                if remaining_bytes is not None:
                    seg_req.add_header('Range', 'bytes=0-%d' % (remaining_bytes - 1))

                segment = self.ydl.urlopen(seg_req).read()
                if remaining_bytes is not None:
                    segment = segment[:remaining_bytes]
                    remaining_bytes -= len(segment)
                outf.write(segment)
                byte_counter += len(segment)
                if remaining_bytes is not None and remaining_bytes <= 0:
                    break

        self._hook_progress({
            'downloaded_bytes': byte_counter,
            'total_bytes': byte_counter,
            'filename': filename,
            'status': 'finished',
        })
        self.try_rename(tmpfilename, filename)
        return True
