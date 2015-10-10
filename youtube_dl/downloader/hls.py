from __future__ import unicode_literals

import os
import re
import subprocess

from .common import FileDownloader
from .fragment import FragmentFD

from ..compat import compat_urlparse
from ..postprocessor.ffmpeg import FFmpegPostProcessor
from ..utils import (
    encodeArgument,
    encodeFilename,
    sanitize_open,
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

        if info_dict['http_headers']:
            # Trailing \r\n after each HTTP header is important to prevent warning from ffmpeg/avconv:
            # [http @ 00000000003d2fa0] No trailing CRLF found in HTTP header.
            args += [
                '-headers',
                ''.join('%s: %s\r\n' % (key, val) for key, val in info_dict['http_headers'].items())]

        args += ['-i', url, '-f', 'mp4', '-c', 'copy', '-bsf:a', 'aac_adtstoasc']

        args = [encodeArgument(opt) for opt in args]
        args.append(encodeFilename(ffpp._ffmpeg_filename_argument(tmpfilename), True))

        self._debug_cmd(args)

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


class NativeHlsFD(FragmentFD):
    """ A more limited implementation that does not require ffmpeg """

    FD_NAME = 'hlsnative'

    def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        self.to_screen('[%s] Downloading m3u8 manifest' % self.FD_NAME)
        manifest = self.ydl.urlopen(man_url).read()

        last_downloaded_segment_filename = encodeFilename(filename + ".last_downloaded_segment")
        last_downloaded_segment = None
        if os.path.isfile(last_downloaded_segment_filename):
            segment_file = open(last_downloaded_segment_filename, 'r')
            try:
                last_downloaded_segment = int(segment_file.readline().strip())
            except ValueError:
                pass
            segment_file.close()

        s = manifest.decode('utf-8', 'ignore')
        fragment_urls = []
        arrived_at_last_downloaded_segment = (last_downloaded_segment is None)
        current_fragment = 0
        for line in s.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                segment_url = (
                    line
                    if re.match(r'^https?://', line)
                    else compat_urlparse.urljoin(man_url, line))
                if arrived_at_last_downloaded_segment:
                    fragment_urls.append(segment_url)
                else:
                    if current_fragment == last_downloaded_segment:
                        arrived_at_last_downloaded_segment = True
                # We only download the first fragment during the test
                if self.params.get('test', False):
                    break
                current_fragment += 1

        skipped_fragments = (
            last_downloaded_segment + 1
            if last_downloaded_segment is not None
            else 0)

        ctx = {
            'filename': filename,
            'total_frags': skipped_fragments + len(fragment_urls),
            'continue_dl': True,
            'continue_fragment': last_downloaded_segment
        }

        self._prepare_and_start_frag_download(ctx)

        for i, frag_url in enumerate(fragment_urls):
            frag_filename = '%s-Frag%d' % (ctx['tmpfilename'], skipped_fragments + i)
            success = ctx['dl'].download(frag_filename, {'url': frag_url})
            if not success:
                return False
            down, frag_sanitized = sanitize_open(frag_filename, 'rb')
            ctx['dest_stream'].write(down.read())
            down.close()
            os.remove(encodeFilename(frag_sanitized))
            segments_file = open(last_downloaded_segment_filename, 'w')
            segments_file.write(str(skipped_fragments + i) + '\n')
            segments_file.close()
            

        self._finish_frag_download(ctx)

        os.remove(last_downloaded_segment_filename)

        return True
