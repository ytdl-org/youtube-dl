from __future__ import unicode_literals

import os.path
import re

from .fragment import FragmentFD

from ..compat import compat_urlparse
from ..utils import (
    encodeFilename,
    sanitize_open,
)


class HlsFD(FragmentFD):
    """ A limited implementation that does not require ffmpeg """

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
