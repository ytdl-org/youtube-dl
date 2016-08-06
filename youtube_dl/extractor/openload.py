# coding: utf-8
from __future__ import unicode_literals, division

import math

from .common import InfoExtractor
from ..compat import compat_chr
from ..utils import (
    decode_png,
    determine_ext,
    ExtractorError,
)


class OpenloadIE(InfoExtractor):
    _VALID_URL = r'https://openload.(?:co|io)/(?:f|embed)/(?P<id>[a-zA-Z0-9-_]+)'

    _TESTS = [{
        'url': 'https://openload.co/f/kUEfGclsU9o',
        'md5': 'bf1c059b004ebc7a256f89408e65c36e',
        'info_dict': {
            'id': 'kUEfGclsU9o',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://openload.co/embed/kUEfGclsU9o/skyrim_no-audio_1080.mp4',
        'only_matching': True,
    }, {
        'url': 'https://openload.io/f/ZAn6oz-VZGE/',
        'only_matching': True,
    }, {
        'url': 'https://openload.co/f/_-ztPaZtMhM/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/f/Sxz5sADo82g/, different layout
        # for title and ext
        'url': 'https://openload.co/embed/Sxz5sADo82g/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if 'File not found' in webpage:
            raise ExtractorError('File not found', expected=True)

        # The following extraction logic is proposed by @Belderak and @gdkchan
        # and declared to be used freely in youtube-dl
        # See https://github.com/rg3/youtube-dl/issues/9706

        numbers_js = self._download_webpage(
            'https://openload.co/assets/js/obfuscator/n.js', video_id,
            note='Downloading signature numbers')
        signums = self._search_regex(
            r'window\.signatureNumbers\s*=\s*[\'"](?P<data>[a-z]+)[\'"]',
            numbers_js, 'signature numbers', group='data')

        linkimg_uri = self._search_regex(
            r'<img[^>]+id="linkimg"[^>]+src="([^"]+)"', webpage, 'link image')
        linkimg = self._request_webpage(
            linkimg_uri, video_id, note=False).read()

        width, height, pixels = decode_png(linkimg)

        output = ''
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[y][3 * x:3 * x + 3]
                if r == 0 and g == 0 and b == 0:
                    break
                else:
                    output += compat_chr(r)
                    output += compat_chr(g)
                    output += compat_chr(b)

        img_str_length = len(output) // 200
        img_str = [[0 for x in range(img_str_length)] for y in range(10)]

        sig_str_length = len(signums) // 260
        sig_str = [[0 for x in range(sig_str_length)] for y in range(10)]

        for i in range(10):
            for j in range(img_str_length):
                begin = i * img_str_length * 20 + j * 20
                img_str[i][j] = output[begin:begin + 20]
            for j in range(sig_str_length):
                begin = i * sig_str_length * 26 + j * 26
                sig_str[i][j] = signums[begin:begin + 26]

        parts = []
        # TODO: find better names for str_, chr_ and sum_
        str_ = ''
        for i in [2, 3, 5, 7]:
            str_ = ''
            sum_ = float(99)
            for j in range(len(sig_str[i])):
                for chr_idx in range(len(img_str[i][j])):
                    if sum_ > float(122):
                        sum_ = float(98)
                    chr_ = compat_chr(int(math.floor(sum_)))
                    if sig_str[i][j][chr_idx] == chr_ and j >= len(str_):
                        sum_ += float(2.5)
                        str_ += img_str[i][j][chr_idx]
            parts.append(str_.replace(',', ''))

        video_url = 'https://openload.co/stream/%s~%s~%s~%s' % (parts[3], parts[1], parts[2], parts[0])

        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'<span[^>]+class=["\']title["\'][^>]*>([^<]+)', webpage,
            'title', default=None) or self._html_search_meta(
            'description', webpage, 'title', fatal=True)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
            # Seems all videos have extensions in their titles
            'ext': determine_ext(title),
        }
