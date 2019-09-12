# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class MrDeepfakesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mrdeepfakes\.com/video/(?P<id>[0-9]+)/.+'
    _TEST = {
        'url': 'https://mrdeepfakes.com/video/5/selena-gomez-pov-deep-fakes',
        'md5': 'fec4ad5ec150f655e0c74c696a4a2ff4',
        'info_dict': {
            'id': '5',
            'ext': 'mp4',
            'title': 'Selena Gomez POV (Deep Fakes)',
            'description': 'Deepfake Selena Gomez lets you fuck her tight shaved pussy',
            'height': 720,
            'age_limit': 18
        }
    }

    def _flashvars_get_string_value(self, key, webpage, **kargs):
        """Gets the string value of a key within the webpage's flashvars JSON."""
        return self._search_regex(key + r': \'(.*?)\'', webpage, key, **kargs)

    def _flashvars_get_format(self, key, webpage, fatal=True):
        """Returns tuple of format (url, quality) for format with URL key 'key', or (None, None) if it doesn't exist."""
        url = self._flashvars_get_string_value(key, webpage, default=None)
        if url is None:
            if fatal:
                raise ExtractorError("Unable to extract flashvars " + key)
            return [None, None]

        url = '/'.join(url.split('/')[2:])

        quality = self._flashvars_get_string_value(key + '_text', webpage, default=None)

        if quality is None:
            quality = self._search_regex(r'_([0-9]*?)p\.', url, 'quality', fatal=True)
        else:
            quality = quality[:-1]

        quality = int(quality)
        return (url, quality)

    def _license_code_decrypt(self, license_code, license_code_length=16):
        """Decrypts license code from form in flashvars to form usable by _uuid_decrypt."""
        if license_code != '':
            f = ''

            for char in license_code[1:]:
                if char == '0':
                    f += '1'
                else:
                    f += char

            j = len(f) / 2
            k = int(f[:j + 1])
            l = int(f[j:])
            g = abs(l - k)
            f = g
            g = abs(k - l)
            f += g
            f *= 2
            f = str(f)
            i = license_code_length / 2 + 2
            m = ''

            for g in range(j + 1):
                for h in range(1, 5):
                    n = int(license_code[g + h]) + int(f[g])
                    if n >= i:
                        n -= i
                    m += str(n)
            return m

        return license_code

    def _uuid_decrypt(self, uuid, license_code):
        """Decrypts the uuid section of a file URL, using a decrypted license code."""
        h = uuid[:32]

        j = h

        for k in range(len(h) - 1, -1, -1):
            l = k
            for m in range(k, len(license_code)):
                l += int(license_code[m])
            while(l >= len(h)):
                l -= len(h)
            n = ''
            for o in range(len(h)):
                if o == k:
                    n += str(h[l])
                else:
                    if o == l:
                        n += str(h[k])
                    else:
                        n += str(h[o])
            h = n
        uuid = uuid.replace(j, h)
        return uuid

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        license_code = self._flashvars_get_string_value('license_code', webpage, fatal=False)
        if license_code is None:
            # Support for accounts is as yet absent
            self.raise_login_required()

        license_code = self._license_code_decrypt(license_code)

        encrypted_formats = []
        encrypted_formats.append(self._flashvars_get_format('video_url', webpage))

        ix = 1
        while True:
            key = 'video_alt_url' + (str(ix) if ix > 1 else '')

            format = self._flashvars_get_format(key, webpage, fatal=False)

            if format[0] is not None and format[1] is not None:
                encrypted_formats.append(format)
            else:
                break

            ix += 1

        decrypted_formats = []

        for url, quality in encrypted_formats:
            url_split = url.split('/')

            for ix, chunk in enumerate(url_split):
                if len(chunk) == 42:
                    chosen = ix
                    break
            else:
                continue

            url_split[chosen] = self._uuid_decrypt(url_split[chosen], license_code)
            decrypted_url = '/'.join(url_split)
            decrypted_formats.append((decrypted_url, quality))

        # Sort by quality
        decrypted_formats.sort(key=lambda x: x[1])

        formats = []

        for url, quality in decrypted_formats:
            formats.append({
                'url': url,
                'height': quality,
                'ext': 'flv' if '.flv' in url else 'mp4',
                'http_headers': {
                    'Referer': 'https://mrdeepfakes.com/'
                }
            })

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'age_limit': 18,
            'formats': formats
        }
