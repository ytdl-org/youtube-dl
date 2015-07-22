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
    function_pool,
)


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

        input_arg = url
        if info_dict.get('hls_transform_source_key'):
            transform_source = function_pool[info_dict['hls_transform_source_key']]
            self.to_screen(
                '[hls] %s: Downloading m3u8 manifest' % info_dict['id'])
            data = self.ydl.urlopen(url).read()
            data = transform_source(data)
            input_arg = '%s.m3u8' % filename
            with open(input_arg, 'wb') as f:
                f.write(data)

        args = [
            encodeArgument(opt)
            for opt in (ffpp.executable, '-y', '-i', input_arg, '-f', 'mp4', '-c', 'copy', '-bsf:a', 'aac_adtstoasc')]
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
            if info_dict.get('hls_transform_source_key'):
                os.remove(input_arg)
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

        self.to_screen(
            '[hlsnative] %s: Downloading m3u8 manifest' % info_dict['id'])
        data = self.ydl.urlopen(url).read()
        if info_dict.get('hls_transform_source_key'):
            transform_source = function_pool.get(info_dict['hls_transform_source_key'])
            data = transform_source(data)
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
