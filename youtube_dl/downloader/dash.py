from __future__ import unicode_literals

import os
import re

from .fragment import FragmentFD
from ..compat import compat_urllib_error
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

        fragment_retries = self.params.get('fragment_retries', 0)

        def append_url_to_file(target_url, tmp_filename, segment_name):
            target_filename = '%s-%s' % (tmp_filename, segment_name)
            count = 0
            while count <= fragment_retries:
                try:
                    success = ctx['dl'].download(target_filename, {'url': combine_url(base_url, target_url)})
                    if not success:
                        return False
                    down, target_sanitized = sanitize_open(target_filename, 'rb')
                    ctx['dest_stream'].write(down.read())
                    down.close()
                    segments_filenames.append(target_sanitized)
                    break
                except (compat_urllib_error.HTTPError, ) as err:
                    # YouTube may often return 404 HTTP error for a fragment causing the
                    # whole download to fail. However if the same fragment is immediately
                    # retried with the same request data this usually succeeds (1-2 attemps
                    # is usually enough) thus allowing to download the whole file successfully.
                    # So, we will retry all fragments that fail with 404 HTTP error for now.
                    if err.code != 404:
                        raise
                    # Retry fragment
                    count += 1
                    if count <= fragment_retries:
                        self.report_retry_fragment(segment_name, count, fragment_retries)
            if count > fragment_retries:
                self.report_error('giving up after %s fragment retries' % fragment_retries)
                return False

        if initialization_url:
            append_url_to_file(initialization_url, ctx['tmpfilename'], 'Init')
        for i, segment_url in enumerate(segment_urls):
            append_url_to_file(segment_url, ctx['tmpfilename'], 'Seg%d' % i)

        self._finish_frag_download(ctx)

        for segment_file in segments_filenames:
            os.remove(encodeFilename(segment_file))

        return True
