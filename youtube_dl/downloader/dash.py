from __future__ import unicode_literals

import os

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
        segments = info_dict['fragments'][:1] if self.params.get(
            'test', False) else info_dict['fragments']

        ctx = {
            'filename': filename,
            'total_frags': len(segments),
        }

        self._prepare_and_start_frag_download(ctx)

        segments_filenames = []

        fragment_retries = self.params.get('fragment_retries', 0)
        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)

        def process_segment(segment, tmp_filename, num):
            segment_url = segment['url']
            segment_name = 'Frag%d' % num
            target_filename = '%s-%s' % (tmp_filename, segment_name)
            # In DASH, the first segment contains necessary headers to
            # generate a valid MP4 file, so always abort for the first segment
            fatal = num == 0 or not skip_unavailable_fragments
            count = 0
            while count <= fragment_retries:
                try:
                    success = ctx['dl'].download(target_filename, {'url': segment_url})
                    if not success:
                        return False
                    down, target_sanitized = sanitize_open(target_filename, 'rb')
                    ctx['dest_stream'].write(down.read())
                    down.close()
                    segments_filenames.append(target_sanitized)
                    break
                except compat_urllib_error.HTTPError as err:
                    # YouTube may often return 404 HTTP error for a fragment causing the
                    # whole download to fail. However if the same fragment is immediately
                    # retried with the same request data this usually succeeds (1-2 attemps
                    # is usually enough) thus allowing to download the whole file successfully.
                    # To be future-proof we will retry all fragments that fail with any
                    # HTTP error.
                    count += 1
                    if count <= fragment_retries:
                        self.report_retry_fragment(err, segment_name, count, fragment_retries)
            if count > fragment_retries:
                if not fatal:
                    self.report_skip_fragment(segment_name)
                    return True
                self.report_error('giving up after %s fragment retries' % fragment_retries)
                return False
            return True

        for i, segment in enumerate(segments):
            if not process_segment(segment, ctx['tmpfilename'], i):
                return False

        self._finish_frag_download(ctx)

        for segment_file in segments_filenames:
            os.remove(encodeFilename(segment_file))

        return True
