from __future__ import unicode_literals

import re

from .common import FileDownloader
from ..compat import compat_urllib_request


class DashSegmentsFD(FileDownloader):
    """
    Download segments in a DASH manifest
    """
    def real_download(self, filename, info_dict):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        base_url = info_dict['url']
        segment_urls = info_dict['segment_urls']

        byte_counter = 0

        def append_url_to_file(outf, target_url, target_name):
            self.to_screen('[DashSegments] %s: Downloading %s' % (info_dict['id'], target_name))
            req = compat_urllib_request.Request(target_url)
            data = self.ydl.urlopen(req).read()
            outf.write(data)
            return len(data)

        def combine_url(base_url, target_url):
            if re.match(r'^https?://', target_url):
                return target_url
            return '%s/%s' % (base_url, target_url)

        with open(tmpfilename, 'wb') as outf:
            append_url_to_file(
                outf, combine_url(base_url, info_dict['initialization_url']),
                'initialization segment')
            for i, segment_url in enumerate(segment_urls):
                segment_len = append_url_to_file(
                    outf, combine_url(base_url, segment_url),
                    'segment %d / %d' % (i + 1, len(segment_urls)))
                byte_counter += segment_len

        self.try_rename(tmpfilename, filename)

        self._hook_progress({
            'downloaded_bytes': byte_counter,
            'total_bytes': byte_counter,
            'filename': filename,
            'status': 'finished',
        })

        return True
