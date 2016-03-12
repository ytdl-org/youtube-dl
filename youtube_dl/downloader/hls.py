from __future__ import unicode_literals

import os
import re
import subprocess
import sys
import time

from .common import FileDownloader
from .fragment import FragmentFD

from ..compat import compat_urlparse
from ..postprocessor.ffmpeg import FFmpegPostProcessor
from ..utils import (
    encodeArgument,
    encodeFilename,
    sanitize_open,
    handle_youtubedl_headers,
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

        args = [ffpp.executable, '-y']

        if info_dict['http_headers'] and re.match(r'^https?://', url):
            # Trailing \r\n after each HTTP header is important to prevent warning from ffmpeg/avconv:
            # [http @ 00000000003d2fa0] No trailing CRLF found in HTTP header.
            headers = handle_youtubedl_headers(info_dict['http_headers'])
            args += [
                '-headers',
                ''.join('%s: %s\r\n' % (key, val) for key, val in headers.items())]

        args += ['-i', url, '-c', 'copy']
        if self.params.get('hls_use_mpegts', False):
            args += ['-f', 'mpegts']
        else:
            args += ['-f', 'mp4', '-bsf:a', 'aac_adtstoasc']

        args = [encodeArgument(opt) for opt in args]
        args.append(encodeFilename(ffpp._ffmpeg_filename_argument(tmpfilename), True))

        self._debug_cmd(args)

        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            lineAfterCarriage = ''
            totalstream = ''
            start = time.time()
            while True:
                tmpoutput = proc.stderr.read(1)
                if tmpoutput == '' and proc.poll() != None:
                    break
                if tmpoutput != '':
                    downloadedstream = ''
                    size_av = '0'
                    lineAfterCarriage += tmpoutput
                    if tmpoutput == '\r':
                        if 'Duration' in lineAfterCarriage:
                            duration_str = [string.split('Duration:')[1:] for string in lineAfterCarriage.split(', ') if 'Duration' in string]
                            if duration_str and duration_str[0][0]:
                                totalstream = duration_str[0][0].strip()

                        if 'frame' in lineAfterCarriage:
                            frame_str = [string.strip().split('=') for string in lineAfterCarriage.split(' ') if 'time=' in string]
                            size_str =  [string.lower().split('kb') for string in lineAfterCarriage.split(' ') if 'kb' in string.lower()]
                            if frame_str and frame_str[0][0] == 'time':
                                downloadedstream = frame_str[0][1].strip()



                            if size_str and size_str[0][0]:
                                size_av = size_str[0][0][1].strip()

                            size_strn = self.parse_bytes(size_av + 'k')
                            percent = self.calc_percent(self.calc_miliseconds(downloadedstream),self.calc_miliseconds(totalstream))
                            data_len = None
                            if percent > 0:
                                data_len = int(size_strn * 100 / percent)
                            now = time.time()
                            speed = self.calc_speed(start,now,size_strn)
                            self._hook_progress({
                                'downloaded_bytes': size_strn,
                                'total_bytes_estimate': data_len,
                                'tmpfilename': tmpfilename,
                                'filename': filename,
                                'status': 'downloading',
                                'elapsed': now - start,
                                'speed': speed,
                            })

                        lineAfterCarriage = ''
            retval = proc.wait()
        except KeyboardInterrupt:
            # subprocces.run would send the SIGKILL signal to ffmpeg and the
            # mp4 file couldn't be played, but if we ask ffmpeg to quit it
            # produces a file that is playable (this is mostly useful for live
            # streams). Note that Windows is not affected and produces playable
            # files (see https://github.com/rg3/youtube-dl/issues/8300).
            if sys.platform != 'win32':
                proc.communicate(b'q')
            raise
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


class NativeHlsFD(FragmentFD):
    """ A more limited implementation that does not require ffmpeg """

    FD_NAME = 'hlsnative'

    def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        self.to_screen('[%s] Downloading m3u8 manifest' % self.FD_NAME)
        manifest = self.ydl.urlopen(man_url).read()

        s = manifest.decode('utf-8', 'ignore')
        fragment_urls = []
        for line in s.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                segment_url = (
                    line
                    if re.match(r'^https?://', line)
                    else compat_urlparse.urljoin(man_url, line))
                fragment_urls.append(segment_url)
                # We only download the first fragment during the test
                if self.params.get('test', False):
                    break

        ctx = {
            'filename': filename,
            'total_frags': len(fragment_urls),
        }

        self._prepare_and_start_frag_download(ctx)

        frags_filenames = []
        for i, frag_url in enumerate(fragment_urls):
            frag_filename = '%s-Frag%d' % (ctx['tmpfilename'], i)
            success = ctx['dl'].download(frag_filename, {'url': frag_url})
            if not success:
                return False
            down, frag_sanitized = sanitize_open(frag_filename, 'rb')
            ctx['dest_stream'].write(down.read())
            down.close()
            frags_filenames.append(frag_sanitized)

        self._finish_frag_download(ctx)

        for frag_file in frags_filenames:
            os.remove(encodeFilename(frag_file))

        return True
