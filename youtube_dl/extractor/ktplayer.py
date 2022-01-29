# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    date_from_ago,
    parse_duration,
    url_or_none,
)


class KtPlayerHelper:
    """KtPlayerHelper contains utility functions for video URL re-encoding
    performed by kt_player that is used by cambro, camhub, etc.
    """
    @staticmethod
    def _hash_kt_player_lic_code(code):
        """Some hash algorithm extracted from obfuscated JS
        in:  '$385023312702592'
        out: '49618502835613441220119020166725'
        """
        if not code:
            return code
        code_no_zeros = ''
        for lim in range(1, len(code)):
            val = int(code[lim])
            code_no_zeros += str(val) if val else '1'
        mid = int(len(code_no_zeros) / 2)
        left = int(code_no_zeros[0:mid + 1])
        right = int(code_no_zeros[mid:])
        val = abs(right - left) + abs(left - right)
        val *= 2
        val = str(val)
        lim = 10
        result = ""
        i = 0
        while i < mid + 1:
            for j in range(1, 5):
                n = int(code[i + j]) + int(val[i])
                if n >= lim:
                    n -= lim
                result += str(n)
            i += 1
        return result

    @staticmethod
    def convert_video_hash(lic_code, orig_hash, limit=32):
        """Video url hash converter extracted from obfuscated JS
        input '$385023312702592', 'bed397181d043299c43f63582406a20b'
        output '8b0bdf194430202ed49325c186633a79'
        input '$518170117095338', '8b25b576ffbf46fa3dc91e34eddc2190b7d3146586'
        output 'f34c6dff1f890e75b6b59422dde3b1acb7d3146586'
        In order to find a corresponding code in cambro.tv/camhub.com scripts
        do the following:
        1. Set a breakpoint at kt_start
        2. Execute in CDT console when triggered:
        flashvars._video_url = flashvars.video_url;
        Object.defineProperty(flashvars, 'video_url', {
            get: function () {
                return flashvars._video_url;
            },
            set: function (value) {
                debugger;
                flashvars._video_url = value;
            }
        });
        3. The second break is where the url re-encoding happens
        """
        i = KtPlayerHelper._hash_kt_player_lic_code(lic_code)
        h = orig_hash[0:limit]
        for k in range(len(h) - 1, -1, -1):
            l = k
            for m in range(k, len(i)):
                l += int(i[m])
            while l >= len(h):
                l -= len(h)
            n = ""
            for o in range(0, len(h)):
                if o == k:
                    n += h[l]
                elif o == l:
                    n += h[k]
                else:
                    n += h[o]
            h = n
        return h + orig_hash[limit:]

    @staticmethod
    def get_url(webpage):
        def search(pattern, string, flags=0):
            mobj = re.search(pattern, string, flags)
            if mobj:
                return next(g for g in mobj.groups() if g is not None)
            return None

        # extract video url
        license_code = search(r'license_code:\s+\'(.+?)\'', webpage)
        video_raw_url = search(r'video_url:\s+\'(.+?)\'', webpage)
        if not license_code or not video_raw_url:
            return None

        # decode a real video url
        parts = video_raw_url.split('/')
        video_pre_parts = []

        # cut some junk at the beginning
        for i in range(len(parts)):
            if parts[i].startswith('http'):
                video_pre_parts = parts[i:]
        if len(video_pre_parts) < 6:
            # it is expected to be
            # http://example.com/get_file/2/1039a5cd2f433e4d41adf41e0afc1773/223000/223101/223101.mp4/
            # with a hash value as 5th component
            raise ExtractorError('url too short: %s' % (video_pre_parts, ))

        # convert video hash to a real one
        orig_hash = video_pre_parts[5]
        new_hash = KtPlayerHelper.convert_video_hash(license_code, orig_hash)
        video_pre_parts[5] = new_hash
        video_url = '/'.join(video_pre_parts)

        return video_url


class KtPlayerExtractor(InfoExtractor):
    """Base class for kt-player based websites.
    Supports both inlined and embedded usage variants.

    _DURATION_RE and _UPLOADED_RE class vars
    must be set in subclasses as needed.
    """

    _DURATION_RE = None
    _UPLOADED_RE = None

    def _kt_extract(self, url, embedded=False):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        title = mobj.group('title')
        website = mobj.group('site')

        webpage = self._download_webpage(url, video_id)

        if 'This video is a private video' in webpage:
            raise ExtractorError(
                'Video %s is private' % video_id, expected=True)

        flashdata = webpage
        if embedded:
            # find the iframe with a player
            iframe_src = self._html_search_regex(
                r'<div class="embed-wrap".+?<iframe.+?src="(.+?)"\s+.+?</iframe>',
                webpage, 'iframe')

            flashdata = self._download_webpage(
                iframe_src, video_id, headers={'Referer': website})

        video_url = KtPlayerHelper.get_url(flashdata)
        if not video_url:
            raise ExtractorError(
                'Failed to extract video url for %s' % video_id, expected=True)

        preview_url = url_or_none(self._html_search_regex(
            r'preview_url:\s+\'(.+?)\'', flashdata, 'preview_url', default=None))
        ext = self._html_search_regex(
            r"""postfix:\s+'(.+?)'""", flashdata, 'ext', fatal=False)
        if ext:
            ext = ext[1:]

        description = self._og_search_title(webpage, fatal=False)
        duration = self._html_search_regex(
            self._DURATION_RE,
            webpage, description, fatal=False, flags=re.DOTALL)

        categories = self._html_search_regex(
            r'video_categories:\s+\'(.+?)\'',
            flashdata, 'categories', fatal=False, default='')
        categories = categories.split(',')
        tags = self._html_search_regex(
            r'video_tags:\s+\'(.+?)\'',
            flashdata, 'tags', fatal=False, default='')
        tags = tags.split(',')

        upload_date = date_from_ago(self._html_search_regex(
            self._UPLOADED_RE, webpage, 'upload_date',
            fatal=False, default=None))

        return {
            'id': video_id,
            'ext': ext,
            'title': title,
            'url': video_url,
            'description': description,
            'thumbnail': preview_url,
            'duration': parse_duration(duration),
            'categories': categories,
            'tags': tags,
            'upload_date': upload_date,
        }


class CambroIE(KtPlayerExtractor):
    _VALID_URL = r'(?P<site>https?://(?:www\.)?cambro\.tv)/(?P<id>[0-9]+)/(?P<title>[^/?#&]+)/'
    _TEST = {
        'url': 'https://www.cambro.tv/223101/artoftease-chaturbate-nude-cam-porn-video/',
        'md5': '4019439bae333f5cdb171807bf406abf',
        'info_dict': {
            'id': '223101',
            'ext': 'mp4',
            'title': 'artoftease-chaturbate-nude-cam-porn-video',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': r're:.*',
            'categories': ['Chaturbate'],
            'duration': 1802.0,
            'upload_date': r're:\d{8}',
        }
    }
    _DURATION_RE = r'<div class="headline">.+?<h1>.+?</h1>.+?' + \
        r'<span><em>((?:\d+:)?(?:\d+:)?\d+)</em></span>.+?</div>'
    _UPLOADED_RE = r'<span><em>(.+?\s+ago)</em></span>'

    def _real_extract(self, url):
        return self._kt_extract(url)


class CamWhoresIE(KtPlayerExtractor):
    _VALID_URL = r'''(?x)
                    (?P<site>https?://(?:www\.)?
                        (?:
                            (?:camwhores\.tv)|
                            (?:webpussi\.com)
                        )
                    )/videos/(?P<id>[0-9]+)/(?P<title>[^/?#&]+)/'''
    _TESTS = [{
        'url': 'https://www.camwhores.tv/videos/7195634/lizistrata-adammeva-vl-2b/',
        'md5': '6dd5ac7952cf1ac32d95bb44318c91d0',
        'info_dict': {
            'id': '7195634',
            'ext': 'mp4',
            'title': 'lizistrata-adammeva-vl-2b',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': r're:.*',
            'categories': ['CB'],
            'duration': 1387.0,
            'upload_date': r're:\d{8}',
        }
    }, {
        'url': 'http://www.webpussi.com/videos/60725/aliska-dark-new-free-show-petite-teen-part-3/',
        'md5': '60b3ac7dd16be6bc1cf45d0285217718',
        'info_dict': {
            'id': '60725',
            'ext': 'mp4',
            'title': 'aliska-dark-new-free-show-petite-teen-part-3',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': r're:.*',
            'duration': 729.0,
            'upload_date': r're:\d{8}',
        }
    }]
    _DURATION_RE = r'<span>Duration: <em>((?:\d+:)?(?:\d+:)?\d+)</em></span>'
    _UPLOADED_RE = r'<span>Submitted:\s+<em>(.+?\s+ago)</em></span>'

    def _real_extract(self, url):
        return self._kt_extract(url)


class CamhubIE(KtPlayerExtractor):
    _VALID_URL = r'(?P<site>https?://(?:www\.)?camhub\.cc)/videos/(?P<id>[0-9]+)/(?P<title>[^/?#&]+)/'
    _TEST = {
        'url': 'http://www.camhub.cc/videos/48002/ehotlovea-skinny-hooker-private-show-ee59e3907cf1c935/',
        'md5': '6da44cc3148cad08243c78575b94b49f',
        'info_dict': {
            'id': '48002',
            'ext': 'mp4',
            'title': 'ehotlovea-skinny-hooker-private-show-ee59e3907cf1c935',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': r're:.*',
            'duration': 853.0,
            'upload_date': r're:\d{8}',
        }
    }
    _DURATION_RE = r'<span>Duration: <em>((?:\d+hour\s)?(?:\d+min\s)?\d+sec)</em></span>'
    _UPLOADED_RE = r'<span>Submitted:\s+<em>(.+?\s+ago)</em></span>'

    def _real_extract(self, url):
        return self._kt_extract(url, embedded=True)


class NudespreeIE(KtPlayerExtractor):
    _VALID_URL = r'(?P<site>https?://(?:www\.)?nudespree\.com)/videos/(?P<id>[0-9]+)/(?P<title>[^/?#&]+)/'
    _TEST = {
        'url': 'http://nudespree.com/videos/1048640/loloxxgocoffe-foryou-hot-brunette/',
        'md5': '67a759471cac087d0ad312d4d6d0bdd3',
        'info_dict': {
            'id': '1048640',
            'ext': 'mp4',
            'title': 'loloxxgocoffe-foryou-hot-brunette',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': r're:.*',
            'duration': 528.0,
            'upload_date': r're:\d{8}',
        }
    }
    _DURATION_RE = r'<span>Duration: <em>((?:\d+:)?(?:\d+:)?\d+)</em></span>'
    _UPLOADED_RE = r'<span>Submitted:\s+<em>(.+?\s+ago)</em></span>'

    def _real_extract(self, url):
        return self._kt_extract(url, embedded=True)
