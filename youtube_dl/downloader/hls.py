from __future__ import unicode_literals

import os.path
import re
import binascii
try:
    from Crypto.Cipher import AES
    can_decrypt_frag = True
except ImportError:
    can_decrypt_frag = False

from .fragment import FragmentFD
from .external import FFmpegFD

from ..compat import (
    compat_urllib_error,
    compat_urlparse,
    compat_struct_pack,
)
from ..utils import (
    encodeFilename,
    sanitize_open,
    parse_m3u8_attributes,
    update_url_query,
)


class HlsFD(FragmentFD):
    """ A limited implementation that does not require ffmpeg """

    FD_NAME = 'hlsnative'

    @staticmethod
    def can_download(manifest, info_dict):
        UNSUPPORTED_FEATURES = (
            r'#EXT-X-KEY:METHOD=(?!NONE|AES-128)',  # encrypted streams [1]
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
        check_results = [not re.search(feature, manifest) for feature in UNSUPPORTED_FEATURES]
        check_results.append(can_decrypt_frag or '#EXT-X-KEY:METHOD=AES-128' not in manifest)
        check_results.append(not info_dict.get('is_live'))
        return all(check_results)

    def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        self.to_screen('[%s] Downloading m3u8 manifest' % self.FD_NAME)
        manifest = self.ydl.urlopen(man_url).read()

        s = manifest.decode('utf-8', 'ignore')

        if not self.can_download(s, info_dict):
            self.report_warning(
                'hlsnative has detected features it does not support, '
                'extraction will be delegated to ffmpeg')
            fd = FFmpegFD(self.ydl, self.params)
            for ph in self._progress_hooks:
                fd.add_progress_hook(ph)
            return fd.real_download(filename, info_dict)

        total_frags = 0
        for line in s.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                total_frags += 1

        ctx = {
            'filename': filename,
            'total_frags': total_frags,
        }

        self._prepare_and_start_frag_download(ctx)

        fragment_retries = self.params.get('fragment_retries', 0)
        skip_unavailable_fragments = self.params.get('skip_unavailable_fragments', True)
        test = self.params.get('test', False)

        extra_query = None
        extra_param_to_segment_url = info_dict.get('extra_param_to_segment_url')
        if extra_param_to_segment_url:
            extra_query = compat_urlparse.parse_qs(extra_param_to_segment_url)
        i = 0
        media_sequence = 0
        decrypt_info = {'METHOD': 'NONE'}
        frags_filenames = []
        for line in s.splitlines():
            line = line.strip()
            if line:
                if not line.startswith('#'):
                    frag_url = (
                        line
                        if re.match(r'^https?://', line)
                        else compat_urlparse.urljoin(man_url, line))
                    frag_name = 'Frag%d' % i
                    frag_filename = '%s-%s' % (ctx['tmpfilename'], frag_name)
                    if extra_query:
                        frag_url = update_url_query(frag_url, extra_query)
                    count = 0
                    while count <= fragment_retries:
                        try:
                            success = ctx['dl'].download(frag_filename, {'url': frag_url})
                            if not success:
                                return False
                            down, frag_sanitized = sanitize_open(frag_filename, 'rb')
                            frag_content = down.read()
                            down.close()
                            break
                        except compat_urllib_error.HTTPError as err:
                            # Unavailable (possibly temporary) fragments may be served.
                            # First we try to retry then either skip or abort.
                            # See https://github.com/rg3/youtube-dl/issues/10165,
                            # https://github.com/rg3/youtube-dl/issues/10448).
                            count += 1
                            if count <= fragment_retries:
                                self.report_retry_fragment(err, frag_name, count, fragment_retries)
                    if count > fragment_retries:
                        if skip_unavailable_fragments:
                            i += 1
                            media_sequence += 1
                            self.report_skip_fragment(frag_name)
                            continue
                        self.report_error(
                            'giving up after %s fragment retries' % fragment_retries)
                        return False
                    if decrypt_info['METHOD'] == 'AES-128':
                        iv = decrypt_info.get('IV') or compat_struct_pack('>8xq', media_sequence)
                        frag_content = AES.new(
                            decrypt_info['KEY'], AES.MODE_CBC, iv).decrypt(frag_content)
                    ctx['dest_stream'].write(frag_content)
                    frags_filenames.append(frag_sanitized)
                    # We only download the first fragment during the test
                    if test:
                        break
                    i += 1
                    media_sequence += 1
                elif line.startswith('#EXT-X-KEY'):
                    decrypt_info = parse_m3u8_attributes(line[11:])
                    if decrypt_info['METHOD'] == 'AES-128':
                        if 'IV' in decrypt_info:
                            decrypt_info['IV'] = binascii.unhexlify(decrypt_info['IV'][2:].zfill(32))
                        if not re.match(r'^https?://', decrypt_info['URI']):
                            decrypt_info['URI'] = compat_urlparse.urljoin(
                                man_url, decrypt_info['URI'])
                        if extra_query:
                            decrypt_info['URI'] = update_url_query(decrypt_info['URI'], extra_query)
                        decrypt_info['KEY'] = self.ydl.urlopen(decrypt_info['URI']).read()
                elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                    media_sequence = int(line[22:])

        self._finish_frag_download(ctx)

        for frag_file in frags_filenames:
            os.remove(encodeFilename(frag_file))

        return True
