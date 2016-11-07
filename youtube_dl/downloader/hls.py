from __future__ import unicode_literals

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
            # r'#EXT-X-BYTERANGE',  # playlists composed of byte ranges of media files [2]

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
        is_aes128_enc = '#EXT-X-KEY:METHOD=AES-128' in manifest
        check_results.append(can_decrypt_frag or not is_aes128_enc)
        check_results.append(not (is_aes128_enc and r'#EXT-X-BYTERANGE' in manifest))
        check_results.append(not info_dict.get('is_live'))
        return all(check_results)

    def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        self.to_screen('[%s] Downloading m3u8 manifest' % self.FD_NAME)

        urlh = self.ydl.urlopen(self._prepare_url(info_dict, man_url))
        man_url = urlh.geturl()
        s = urlh.read().decode('utf-8', 'ignore')

        if not self.can_download(s, info_dict):
            if info_dict.get('extra_param_to_segment_url'):
                self.report_error('pycrypto not found. Please install it.')
                return False
            self.report_warning(
                'hlsnative has detected features it does not support, '
                'extraction will be delegated to ffmpeg')
            fd = FFmpegFD(self.ydl, self.params)
            for ph in self._progress_hooks:
                fd.add_progress_hook(ph)
            return fd.real_download(filename, info_dict)

        def is_ad_fragment_start(s):
            return (s.startswith('#ANVATO-SEGMENT-INFO') and 'type=ad' in s
                    or s.startswith('#UPLYNK-SEGMENT') and s.endswith(',ad'))

        def is_ad_fragment_end(s):
            return (s.startswith('#ANVATO-SEGMENT-INFO') and 'type=master' in s
                    or s.startswith('#UPLYNK-SEGMENT') and s.endswith(',segment'))

        media_frags = 0
        ad_frags = 0
        ad_frag_next = False
        for line in s.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                if is_ad_fragment_start(line):
                    ad_frag_next = True
                elif is_ad_fragment_end(line):
                    ad_frag_next = False
                continue
            if ad_frag_next:
                ad_frags += 1
                continue
            media_frags += 1

        ctx = {
            'filename': filename,
            'total_frags': media_frags,
            'ad_frags': ad_frags,
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
        byte_range = {}
        frag_index = 0
        ad_frag_next = False
        for line in s.splitlines():
            line = line.strip()
            if line:
                if not line.startswith('#'):
                    if ad_frag_next:
                        continue
                    frag_index += 1
                    if frag_index <= ctx['fragment_index']:
                        continue
                    frag_url = (
                        line
                        if re.match(r'^https?://', line)
                        else compat_urlparse.urljoin(man_url, line))
                    if extra_query:
                        frag_url = update_url_query(frag_url, extra_query)
                    count = 0
                    headers = info_dict.get('http_headers', {})
                    if byte_range:
                        headers['Range'] = 'bytes=%d-%d' % (byte_range['start'], byte_range['end'])
                    while count <= fragment_retries:
                        try:
                            success, frag_content = self._download_fragment(
                                ctx, frag_url, info_dict, headers)
                            if not success:
                                return False
                            break
                        except compat_urllib_error.HTTPError as err:
                            # Unavailable (possibly temporary) fragments may be served.
                            # First we try to retry then either skip or abort.
                            # See https://github.com/ytdl-org/youtube-dl/issues/10165,
                            # https://github.com/ytdl-org/youtube-dl/issues/10448).
                            count += 1
                            if count <= fragment_retries:
                                self.report_retry_fragment(err, frag_index, count, fragment_retries)
                    if count > fragment_retries:
                        if skip_unavailable_fragments:
                            i += 1
                            media_sequence += 1
                            self.report_skip_fragment(frag_index)
                            continue
                        self.report_error(
                            'giving up after %s fragment retries' % fragment_retries)
                        return False
                    if decrypt_info['METHOD'] == 'AES-128':
                        iv = decrypt_info.get('IV') or compat_struct_pack('>8xq', media_sequence)
                        decrypt_info['KEY'] = decrypt_info.get('KEY') or self.ydl.urlopen(
                            self._prepare_url(info_dict, decrypt_info['URI'])).read()
                        frag_content = AES.new(
                            decrypt_info['KEY'], AES.MODE_CBC, iv).decrypt(frag_content)
                    self._append_fragment(ctx, frag_content)
                    # We only download the first fragment during the test
                    if test:
                        break
                    i += 1
                    media_sequence += 1
                elif line.startswith('#EXT-X-KEY'):
                    decrypt_url = decrypt_info.get('URI')
                    decrypt_info = parse_m3u8_attributes(line[11:])
                    if decrypt_info['METHOD'] == 'AES-128':
                        if 'IV' in decrypt_info:
                            decrypt_info['IV'] = binascii.unhexlify(decrypt_info['IV'][2:].zfill(32))
                        if not re.match(r'^https?://', decrypt_info['URI']):
                            decrypt_info['URI'] = compat_urlparse.urljoin(
                                man_url, decrypt_info['URI'])
                        if extra_query:
                            decrypt_info['URI'] = update_url_query(decrypt_info['URI'], extra_query)
                        if decrypt_url != decrypt_info['URI']:
                            decrypt_info['KEY'] = None
                elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
                    media_sequence = int(line[22:])
                elif line.startswith('#EXT-X-BYTERANGE'):
                    splitted_byte_range = line[17:].split('@')
                    sub_range_start = int(splitted_byte_range[1]) if len(splitted_byte_range) == 2 else byte_range['end']
                    byte_range = {
                        'start': sub_range_start,
                        'end': sub_range_start + int(splitted_byte_range[0]),
                    }
                elif is_ad_fragment_start(line):
                    ad_frag_next = True
                elif is_ad_fragment_end(line):
                    ad_frag_next = False

        self._finish_frag_download(ctx)

        return True


class WebVttHlsFD(FragmentFD):
    """ A downloader for HLS WebVTT subtitles. """
    FD_NAME = 'hlswebvtt'

    @staticmethod
    def _parse_ts(ts):
        m = re.match('(?:(?:([0-9]+):)?([0-9]+):)?([0-9]+)(?:\.([0-9]+))?', ts)
        hrs, min, sec, msc = m.groups()
        return 90 * (
            int(hrs or 0) * 3600000 +
            int(min or 0) *   60000 +
            int(sec or 0) *    1000 +
            int(msc or 0)
        )

    @staticmethod
    def _format_ts(ts):
        ts  = int(ts / 90)
        hrs = ts / 3600000
        ts %=      3600000
        min = ts /   60000
        ts %=        60000
        sec = ts /    1000
        ts %=         1000
        return '%02u:%02u:%02u.%03u' % (hrs, min, sec, ts)

    def real_download(self, filename, info_dict):
        url = info_dict['url']
        self.to_screen('[%s] Downloading m3u8 manifest' % self.FD_NAME)
        data = self.ydl.urlopen(url).read()
        s = data.decode('utf-8', 'ignore')
        segment_urls = []
        for line in s.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                segment_url = (
                    line if re.match(r'^https?://', line)
                    else compat_urlparse.urljoin(url, line))
                segment_urls.append(segment_url)

        ctx = {
            'filename': filename,
            'total_frags': len(segment_urls),
        }

        self._prepare_and_start_frag_download(ctx)

        cues = []
        header = []
        frags_filenames = []
        for i, frag_url in enumerate(segment_urls):
            frag_name = 'Frag%d' % i
            frag_filename = '%s-%s' % (ctx['tmpfilename'], frag_name)

            success = ctx['dl'].download(frag_filename, {'url': frag_url})
            if not success:
                return False
            down, frag_sanitized = sanitize_open(frag_filename, 'rb')
            lines = down.read().decode('utf-8', 'ignore').splitlines()
            down.close()
            frags_filenames.append(frag_sanitized)

            line_iter = iter(lines)
            line = next(line_iter)
            if not line.startswith('WEBVTT'):
                self.report_error('Not a valid WebVTT subtitles segment')
            if len(line) > 6 and not (line.startswith('WEBVTT ') or line.startswith('WEBVTT\t')):
                self.report_error('Not a valid WebVTT subtitles segment')

            try:
                # read header
                tsadj = 0
                while True:
                    line = next(line_iter)
                    if line == '':
                        break
                    elif line.find('-->') != -1:
                        break

                    if line.startswith('X-TIMESTAMP-MAP='):
                        m = re.search(r'LOCAL:([0-9:.]+)', line)
                        locl_ts = self._parse_ts(m.group(1))
                        m = re.search(r'MPEGTS:([0-9]+)', line)
                        mpeg_ts = int(m.group(1))
                        tsadj = mpeg_ts - locl_ts
                    else:
                        header.append(line)

                subtitle = None
                while True:
                    while line == '':
                        line = next(line_iter)
                    cue = {}

                    if line.find('-->') == -1:
                        cue['id'] = line
                        line = next(line_iter)
                        if line == '':
                            continue

                    m = re.match(r'^([0-9:.]+\s*)-->\s*([0-9:.]+)(\s+.*)?', line)
                    if m:
                        ts_start = self._parse_ts(m.group(1))
                        ts_end   = self._parse_ts(m.group(2))
                        cue['style'] = m.group(3) or ''
                    else:
                        continue

                    ts_start += tsadj
                    ts_end   += tsadj

                    cue['start_ts'] = self._format_ts(ts_start)
                    cue['end_ts'] = self._format_ts(ts_end)

                    line = next(line_iter)

                    cue['text'] = ''

                    try:
                        while line != '':
                            if line.find('-->') != -1:
                                break
                            cue['text'] += line + '\n'
                            line = next(line_iter)
                    finally:
                        cues.append(cue)
            except StopIteration:
                pass

        cues.sort(key=lambda cue: cue['start_ts'])
        with ctx['dest_stream'] as outf:
            outf.write(b'WEBVTT\n')
            for item in header:
                outf.write(('%s\n' % item).encode('utf-8'))
            for cue in cues:
                outf.write(b'\n')
                if cue.get('id'):
                    outf.write(('%s\n' % cue['id']).encode('utf-8'))
                outf.write(
                    ('%s --> %s%s\n' % (cue['start_ts'], cue['end_ts'], cue['style']))
                        .encode('utf-8')
                )
                outf.write(cue['text'].encode('utf-8'))

        self._finish_frag_download(ctx)

        for frag_file in frags_filenames:
            os.remove(encodeFilename(frag_file))
