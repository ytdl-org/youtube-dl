from __future__ import unicode_literals

import itertools

from .fragment import FragmentFD
from ..compat import compat_urllib_error
from ..utils import (
    DownloadError,
    urljoin,
)


class DashSegmentsFD(FragmentFD):
    """
    Download segments in a DASH manifest
    """

    FD_NAME = 'dashsegments'

    def real_download(self, filename, info_dict):
        fragment_base_url = info_dict.get('fragment_base_url')
        fragments = info_dict['fragments'][:1] if self.params.get(
            'test', False) else info_dict['fragments']

        ctx = {
            'filename': filename,
            'total_frags': len(fragments),
        }

        self._prepare_and_start_frag_download(ctx)

        fragment_retries = self.params.get('fragment_retries', 0)
        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)

        for frag_index, fragment in enumerate(fragments, 1):
            if frag_index <= ctx['fragment_index']:
                continue
            success = False
            # In DASH, the first segment contains necessary headers to
            # generate a valid MP4 file, so always abort for the first segment
            fatal = frag_index == 1 or not skip_unavailable_fragments
            fragment_url = fragment.get('url')
            if not fragment_url:
                assert fragment_base_url
                fragment_url = urljoin(fragment_base_url, fragment['path'])
            headers = info_dict.get('http_headers')
            fragment_range = fragment.get('range')
            if fragment_range:
                headers = headers.copy() if headers else {}
                headers['Range'] = 'bytes=%s' % (fragment_range,)
            for count in itertools.count():
                try:
                    success, frag_content = self._download_fragment(ctx, fragment_url, info_dict, headers)
                    if not success:
                        return False
                    self._append_fragment(ctx, frag_content)
                except compat_urllib_error.HTTPError as err:
                    # YouTube may often return 404 HTTP error for a fragment causing the
                    # whole download to fail. However if the same fragment is immediately
                    # retried with the same request data this usually succeeds (1-2 attempts
                    # is usually enough) thus allowing to download the whole file successfully.
                    # To be future-proof we will retry all fragments that fail with any
                    # HTTP error.
                    if count < fragment_retries:
                        self.report_retry_fragment(err, frag_index, count + 1, fragment_retries)
                        continue
                except DownloadError:
                    # Don't retry fragment if error occurred during HTTP downloading
                    # itself since it has its own retry settings
                    if fatal:
                        raise
                break

            if not success:
                if not fatal:
                    self.report_skip_fragment(frag_index)
                    continue
                self.report_error('giving up after %s fragment retries' % count)
                return False

        self._finish_frag_download(ctx)

        return True
