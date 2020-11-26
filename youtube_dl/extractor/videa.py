# coding: utf-8
from __future__ import unicode_literals

import re
import random
import string
import struct

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    mimetype2ext,
    parse_codecs,
    xpath_element,
    xpath_text,
)
from ..compat import (
    compat_b64decode,
    compat_ord,
    compat_parse_qs,
)


class VideaIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        videa(?:kid)?\.hu/
                        (?:
                            videok/(?:[^/]+/)*[^?#&]+-|
                            player\?.*?\bv=|
                            player/v/
                        )
                        (?P<id>[^?#&]+)
                    '''
    _TESTS = [{
        'url': 'http://videa.hu/videok/allatok/az-orult-kigyasz-285-kigyot-kigyo-8YfIAjxwWGwT8HVQ',
        'md5': '97a7af41faeaffd9f1fc864a7c7e7603',
        'info_dict': {
            'id': '8YfIAjxwWGwT8HVQ',
            'ext': 'mp4',
            'title': 'Az őrült kígyász 285 kígyót enged szabadon',
            'thumbnail': r're:^https?://.*',
            'duration': 21,
        },
    }, {
        'url': 'http://videa.hu/videok/origo/jarmuvek/supercars-elozes-jAHDWfWSJH5XuFhH',
        'only_matching': True,
    }, {
        'url': 'http://videa.hu/player?v=8YfIAjxwWGwT8HVQ',
        'only_matching': True,
    }, {
        'url': 'http://videa.hu/player/v/8YfIAjxwWGwT8HVQ?autoplay=1',
        'only_matching': True,
    }, {
        'url': 'https://videakid.hu/videok/origo/jarmuvek/supercars-elozes-jAHDWfWSJH5XuFhH',
        'only_matching': True,
    }, {
        'url': 'https://videakid.hu/player?v=8YfIAjxwWGwT8HVQ',
        'only_matching': True,
    }, {
        'url': 'https://videakid.hu/player/v/8YfIAjxwWGwT8HVQ?autoplay=1',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//videa\.hu/player\?.*?\bv=.+?)\1',
            webpage)]

    def rc4(self, ciphertext, key):
        res = b''

        keyLen = len(key)
        S = list(range(256))

        j = 0
        for i in range(256):
            j = (j + S[i] + ord(key[i % keyLen])) % 256
            S[i], S[j] = S[j], S[i]

        i = 0
        j = 0
        for m in range(len(ciphertext)):
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            k = S[(S[i] + S[j]) % 256]
            res += struct.pack("B", k ^ compat_ord(ciphertext[m]))

        return res

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, fatal=True)
        error = self._search_regex(r'<p class="error-text">([^<]+)</p>', webpage, 'error', default=None)
        if error:
            raise ExtractorError(error, expected=True)

        video_src_params_raw = self._search_regex(r'<iframe[^>]+id="videa_player_iframe"[^>]+src="/player\?([^"]+)"', webpage, 'video_src_params')
        video_src_params = compat_parse_qs(video_src_params_raw)
        player_page = self._download_webpage("https://videa.hu/videojs_player?%s" % video_src_params_raw, video_id, fatal=True)
        nonce = self._search_regex(r'_xt\s*=\s*"([^"]+)"', player_page, 'nonce')
        random_seed = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
        static_secret = 'xHb0ZvME5q8CBcoQi6AngerDu3FGO9fkUlwPmLVY_RTzj2hJIS4NasXWKy1td7p'
        l = nonce[:32]
        s = nonce[32:]
        result = ''
        for i in range(0, 32):
            result += s[i - (static_secret.index(l[i]) - 31)]

        video_src_params['_s'] = random_seed
        video_src_params['_t'] = result[:16]
        encryption_key_stem = result[16:] + random_seed

        [b64_info, handle] = self._download_webpage_handle(
            'http://videa.hu/videaplayer_get_xml.php', video_id,
            query=video_src_params, fatal=True)

        encrypted_info = compat_b64decode(b64_info)
        key = encryption_key_stem + handle.info()['x-videa-xs']
        info_str = self.rc4(encrypted_info, key).decode('utf8')
        info = self._parse_xml(info_str, video_id)

        video = xpath_element(info, './/video', 'video', fatal=True)
        sources = xpath_element(info, './/video_sources', 'sources', fatal=True)
        hash_values = xpath_element(info, './/hash_values', 'hash_values', fatal=True)

        title = xpath_text(video, './title', fatal=True)

        formats = []
        for source in sources.findall('./video_source'):
            source_url = source.text
            if not source_url:
                continue
            source_url += '?md5=%s&expires=%s' % (hash_values.find('hash_value_%s' % source.get('name')).text, source.get('exp'))
            f = parse_codecs(source.get('codecs'))
            f.update({
                'url': source_url,
                'ext': mimetype2ext(source.get('mimetype')) or 'mp4',
                'format_id': source.get('name'),
                'width': int_or_none(source.get('width')),
                'height': int_or_none(source.get('height')),
            })
            formats.append(f)
        self._sort_formats(formats)

        thumbnail = xpath_text(video, './poster_src')
        duration = int_or_none(xpath_text(video, './duration'))

        age_limit = None
        is_adult = xpath_text(video, './is_adult_content', default=None)
        if is_adult:
            age_limit = 18 if is_adult == '1' else 0

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }
