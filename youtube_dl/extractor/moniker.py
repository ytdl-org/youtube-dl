# coding: utf-8
from __future__ import unicode_literals

import os.path
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    remove_start,
    sanitized_Request,
    urlencode_postdata,
)


class MonikerIE(InfoExtractor):
    IE_DESC = 'allmyvideos.net and vidspot.net'
    _VALID_URL = r'https?://(?:www\.)?(?:allmyvideos|vidspot)\.net/(?:(?:2|v)/v-)?(?P<id>[a-zA-Z0-9_-]+)'

    _TESTS = [{
        'url': 'http://allmyvideos.net/jih3nce3x6wn',
        'md5': '710883dee1bfc370ecf9fa6a89307c88',
        'info_dict': {
            'id': 'jih3nce3x6wn',
            'ext': 'mp4',
            'title': 'youtube-dl test video',
        },
    }, {
        'url': 'http://allmyvideos.net/embed-jih3nce3x6wn',
        'md5': '710883dee1bfc370ecf9fa6a89307c88',
        'info_dict': {
            'id': 'jih3nce3x6wn',
            'ext': 'mp4',
            'title': 'youtube-dl test video',
        },
    }, {
        'url': 'http://vidspot.net/l2ngsmhs8ci5',
        'md5': '710883dee1bfc370ecf9fa6a89307c88',
        'info_dict': {
            'id': 'l2ngsmhs8ci5',
            'ext': 'mp4',
            'title': 'youtube-dl test video',
        },
    }, {
        'url': 'https://www.vidspot.net/l2ngsmhs8ci5',
        'only_matching': True,
    }, {
        'url': 'http://vidspot.net/2/v-ywDf99',
        'md5': '5f8254ce12df30479428b0152fb8e7ba',
        'info_dict': {
            'id': 'ywDf99',
            'ext': 'mp4',
            'title': 'IL FAIT LE MALIN EN PORSHE CAYENNE ( mais pas pour longtemps)',
            'description': 'IL FAIT LE MALIN EN PORSHE CAYENNE.',
        },
    }, {
        'url': 'http://allmyvideos.net/v/v-HXZm5t',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        orig_video_id = self._match_id(url)
        video_id = remove_start(orig_video_id, 'embed-')
        url = url.replace(orig_video_id, video_id)
        assert re.match(self._VALID_URL, url) is not None
        orig_webpage = self._download_webpage(url, video_id)

        if '>File Not Found<' in orig_webpage:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        error = self._search_regex(
            r'class="err">([^<]+)<', orig_webpage, 'error', default=None)
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error), expected=True)

        builtin_url = self._search_regex(
            r'<iframe[^>]+src=(["\'])(?P<url>.+?/builtin-.+?)\1',
            orig_webpage, 'builtin URL', default=None, group='url')

        if builtin_url:
            req = sanitized_Request(builtin_url)
            req.add_header('Referer', url)
            webpage = self._download_webpage(req, video_id, 'Downloading builtin page')
            title = self._og_search_title(orig_webpage).strip()
            description = self._og_search_description(orig_webpage).strip()
        else:
            fields = re.findall(r'type="hidden" name="(.+?)"\s* value="?(.+?)">', orig_webpage)
            data = dict(fields)

            post = urlencode_postdata(data)
            headers = {
                b'Content-Type': b'application/x-www-form-urlencoded',
            }
            req = sanitized_Request(url, post, headers)
            webpage = self._download_webpage(
                req, video_id, note='Downloading video page ...')

            title = os.path.splitext(data['fname'])[0]
            description = None

        # Could be several links with different quality
        links = re.findall(r'"file" : "?(.+?)",', webpage)
        # Assume the links are ordered in quality
        formats = [{
            'url': l,
            'quality': i,
        } for i, l in enumerate(links)]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
