from __future__ import unicode_literals

import re

from .common import FileDownloader
from ..utils import sanitized_Request


class DashSegmentsFD(FileDownloader):
    """
    Download segments in a DASH manifest
    """
    def real_download(self, filename, info_dict):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        base_url = info_dict['url']
        segment_urls = info_dict['segment_urls']

        is_test = self.params.get('test', False)
        remaining_bytes = self._TEST_FILE_SIZE if is_test else None
        byte_counter = 0

        def append_url_to_file(outf, target_url, target_name, remaining_bytes=None):
            self.to_screen('[DashSegments] %s: Downloading %s' % (info_dict['id'], target_name))
            req = sanitized_Request(target_url)
            if remaining_bytes is not None:
                req.add_header('Range', 'bytes=0-%d' % (remaining_bytes - 1))

            data = self.ydl.urlopen(req).read()

            if remaining_bytes is not None:
                data = data[:remaining_bytes]

            outf.write(data)
            return len(data)

        def combine_url(base_url, target_url):
            if re.match(r'^https?://', target_url):
                return target_url
            return '%s%s%s' % (base_url, '' if base_url.endswith('/') else '/', target_url)

        with open(tmpfilename, 'wb') as outf:
            append_url_to_file(
                outf, combine_url(base_url, info_dict['initialization_url']),
                'initialization segment')
            for i, segment_url in enumerate(segment_urls):
                segment_len = append_url_to_file(
                    outf, combine_url(base_url, segment_url),
                    'segment %d / %d' % (i + 1, len(segment_urls)),
                    remaining_bytes)
                byte_counter += segment_len
                if remaining_bytes is not None:
                    remaining_bytes -= segment_len
                    if remaining_bytes <= 0:
                        break

        self.try_rename(tmpfilename, filename)

        self._hook_progress({
            'downloaded_bytes': byte_counter,
            'total_bytes': byte_counter,
            'filename': filename,
            'status': 'finished',
        })

        return True
