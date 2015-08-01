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
    bytes_to_intlist,
    intlist_to_bytes
)
from ..aes import aes_cbc_decrypt


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
        def convert_to_big_endian(value, size):
            big_endian = [0] * size
            for i in range(size):
                block = value % 256
                value //= 256
                big_endian[size - 1 - i] = block
            return big_endian

        url = info_dict['url']
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        self.to_screen(
            '[hlsnative] %s: Downloading m3u8 manifest' % info_dict['id'])
        data = self.ydl.urlopen(url).read()
        m3u8_data = data.decode('utf-8', 'ignore')

        segment_count = 0
        for m3u8_line in m3u8_data.splitlines():
            m3u8_line = m3u8_line.strip()
            if m3u8_line and not m3u8_line.startswith('#'):
                segment_count += 1

        is_test = self.params.get('test', False)
        remaining_bytes = self._TEST_FILE_SIZE if is_test else None
        byte_counter = 0
        media_sequence = 0
        # Function to decrypt segment or None
        decrypt_fn = None
        segment_index = 0
        for m3u8_line in m3u8_data.splitlines():
            m3u8_line = m3u8_line.strip()
            mo = re.match(r'^#\s*EXT-X-MEDIA-SEQUENCE\s*:\s*(?P<seq>\d+)$',
                          m3u8_line, re.IGNORECASE)
            if mo:
                media_sequence = int(mo.group('seq'))
                continue
            mo = re.match(r'^#\s*EXT-X-KEY\s*:\s*'
                          # METHOD
                          r'METHOD\s*=\s*(?P<type>(?P<AES>AES-128)|NONE)'
                          r'(?(AES)' # if AES
                              r'\s*,\s*'
                              # URI
                              r'URI\s*=\s*'
                              r'(?P<uri_delim>["\'])'
                              r'(?P<uri>.*?)'
                              r'(?P=uri_delim)'
                              # IV (optional)
                              r'(?:'
                                  r'\s*,\s*'
                                  # IV
                                  r'IV\s*=\s*'
                                  r'(?:0X)?'
                                  r'(?P<iv>[0-9a-f]+)'
                              r')?'
                          r'|' # else
                              r'$'
                          r')', m3u8_line, re.IGNORECASE)
            if mo:
                _type = mo.group('type').upper()
                if _type == 'NONE':
                    decrypt_fn = None
                elif _type == 'AES-128':
                    self.to_screen(
                        '[hlsnative] %s: Downloading encryption key' %
                        (info_dict['id']))
                    key = bytes_to_intlist(self.ydl.urlopen(mo.group('uri')).read())
                    if len(key) != 16:
                        self.report_warning('Invalid encryption key')
                        continue
                    if mo.group('iv'):
                        iv = int(mo.group('iv'), 16)
                        iv_big_endian = convert_to_big_endian(iv, 16)
                        decrypt_fn = lambda data: aes_cbc_decrypt(bytes_to_intlist(data), key, iv_big_endian)
                    else:
                        decrypt_fn = lambda data: aes_cbc_decrypt(bytes_to_intlist(data), key,
                            convert_to_big_endian(media_sequence, 16))
                continue

            if m3u8_line and not m3u8_line.startswith('#'):
                segment_url = (
                    m3u8_line
                    if re.match(r'^https?://', m3u8_line)
                    else compat_urlparse.urljoin(url, m3u8_line))

                seg_req = compat_urllib_request.Request(segment_url)
                if remaining_bytes is not None:
                    seg_req.add_header('Range', 'bytes=0-%d' % (remaining_bytes - 1))

                segment_filename = '%s-%d' % (tmpfilename, segment_index)
                if os.path.exists(segment_filename):
                    self.to_screen(
                        '[hlsnative] %s: Segment content already downloaded %d / %d' %
                        (info_dict['id'], segment_index + 1, segment_count))
                    with open(segment_filename, "rb") as inf:
                        segment = inf.read()
                else:
                    self.to_screen(
                        '[hlsnative] %s: Downloading segment %d / %d' %
                        (info_dict['id'], segment_index + 1, segment_count))
                    segment = self.ydl.urlopen(seg_req).read()
                    if decrypt_fn is not None:
                        segment = intlist_to_bytes(decrypt_fn(segment))
                if remaining_bytes is not None:
                    segment = segment[:remaining_bytes]
                    remaining_bytes -= len(segment)
                with open(segment_filename, 'wb') as outf:
                    outf.write(segment)

                segment_index += 1
                media_sequence += 1

                byte_counter += len(segment)
                if remaining_bytes is not None and remaining_bytes <= 0:
                    break
        segment_count = segment_index

        # Concatenate segments
        segment_filenames = ['%s-%d' % (tmpfilename, segment_index) for segment_index in range(segment_count)]
        with open(tmpfilename, "wb") as outf:
            for segment_filename in segment_filenames:
                with open(segment_filename, "rb") as inf:
                    outf.write(inf.read())
                os.remove(segment_filename)

        self._hook_progress({
            'downloaded_bytes': byte_counter,
            'total_bytes': byte_counter,
            'filename': filename,
            'status': 'finished',
        })
        self.try_rename(tmpfilename, filename)
        return True
