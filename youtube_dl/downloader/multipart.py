from __future__ import unicode_literals

import os

from .fragment import FragmentFD

from ..utils import (
    encodeFilename,
    sanitize_open,
)


class MultiPartFD(FragmentFD):
    """ A more limited implementation that does not require ffmpeg """

    FD_NAME = 'multipart'

    def real_download(self, filename, info_dict):
        parts = info_dict['parts']
        ctx = {
            'filename': filename,
            'total_frags': len(parts),
        }

        self._prepare_and_start_frag_download(ctx)

        frags_filenames = []
        for i in range(len(parts)):
            frag_filename = '%s%d' % (ctx['tmpfilename'], i)
            success = ctx['dl'].download(frag_filename, {'url': parts[i]['url']})
            if not success:
                return False
            down, frag_sanitized = sanitize_open(frag_filename, 'rb')
            ctx['dest_stream'].write(down.read())
            down.close()
            frags_filenames.append(frag_sanitized)
            # We only download the first fragment during the test
            if self.params.get('test', False):
                break

        self._finish_frag_download(ctx)

        for frag_file in frags_filenames:
            os.remove(encodeFilename(frag_file))

        return True
