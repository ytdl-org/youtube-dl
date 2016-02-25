from __future__ import unicode_literals

import os
import re

from .fragment import FragmentFD
from ..utils import (
    sanitize_open,
    encodeFilename,
)


class DashSegmentsFD(FragmentFD):
    """
    Download segments in a DASH manifest
    """

    FD_NAME = 'dashsegments'

    def real_download(self, filename, info_dict):
        base_url = info_dict['url']
        segment_urls = [info_dict['segment_urls'][0]] if self.params.get('test', False) else info_dict['segment_urls']
        initialization_url = info_dict.get('initialization_url')

        ctx = {
            'filename': filename,
            'total_frags': len(segment_urls) + (1 if initialization_url else 0),
        }

        self._prepare_and_start_frag_download(ctx)

        def combine_url(base_url, target_url):
            if re.match(r'^https?://', target_url):
                return target_url
            return '%s%s%s' % (base_url, '' if base_url.endswith('/') else '/', target_url)

        segments_filenames = []

        def append_url_to_file(target_url, target_filename):
            success = ctx['dl'].download(target_filename, {'url': combine_url(base_url, target_url)})
            if not success:
                return False
            down, target_sanitized = sanitize_open(target_filename, 'rb')
            ctx['dest_stream'].write(down.read())
            down.close()
            segments_filenames.append(target_sanitized)

        if initialization_url:
            append_url_to_file(initialization_url, ctx['tmpfilename'] + '-Init')
        for i, segment_url in enumerate(segment_urls):
            segment_filename = '%s-Seg%d' % (ctx['tmpfilename'], i)
            append_url_to_file(segment_url, segment_filename)

        self._finish_frag_download(ctx)

        for segment_file in segments_filenames:
            os.remove(encodeFilename(segment_file))

        return True
