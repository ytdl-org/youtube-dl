from __future__ import unicode_literals

import os.path
import re

from .fragment import FragmentFD
from .external import FFmpegFD

from ..compat import compat_urlparse
from ..utils import (
    encodeFilename,
    sanitize_open,
)


class HlsFD(FragmentFD):
    """ A limited implementation that does not require ffmpeg """

    FD_NAME = 'hlsnative'

    @staticmethod
    def can_download(manifest):
        UNSUPPORTED_FEATURES = (
            r'#EXT-X-KEY:METHOD=(?!NONE)',  # encrypted streams [1]
            r'#EXT-X-BYTERANGE',  # playlists composed of byte ranges of media files [2]

            # Live streams heuristic does not always work (e.g. geo restricted to Germany
            # http://hls-geo.daserste.de/i/videoportal/Film/c_620000/622873/format,716451,716457,716450,716458,716459,.mp4.csmil/index_4_av.m3u8?null=0)
            # r'#EXT-X-MEDIA-SEQUENCE:(?!0$)',  # live streams [3]

            # This heuristic also is not correct since segments may not be appended as well.
            # Twitch vods of finished streams have EXT-X-PLAYLIST-TYPE:EVENT despite
            # no segments will definitely be appended to the end of the playlist.
            # r'#EXT-X-PLAYLIST-TYPE:EVENT',  # media segments may be appended to the end of
            #                                 # event media playlists [4]

            # 1. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.2.4
            # 2. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.2.2
            # 3. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.3.2
            # 4. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.3.5
        )
        return all(not re.search(feature, manifest) for feature in UNSUPPORTED_FEATURES)

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

        if not self.can_download(s):
            self.report_warning(
                'hlsnative has detected features it does not support, '
                'extraction will be delegated to ffmpeg')
            fd = FFmpegFD(self.ydl, self.params)
            for ph in self._progress_hooks:
                fd.add_progress_hook(ph)
            return fd.real_download(filename, info_dict)

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
