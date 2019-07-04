# coding: utf-8
from __future__ import unicode_literals

from .adobepass import AdobePassIE
from ..utils import (
    extract_attributes,
    update_url_query,
    smuggle_url,
)


class SproutIE(AdobePassIE):
    _VALID_URL = r'https?://(?:www\.)?sproutonline\.com/watch/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.sproutonline.com/watch/cowboy-adventure',
        'md5': '74bf14128578d1e040c3ebc82088f45f',
        'info_dict': {
            'id': '9dexnwtmh8_X',
            'ext': 'mp4',
            'title': 'A Cowboy Adventure',
            'description': 'Ruff-Ruff, Tweet and Dave get to be cowboys for the day at Six Cow Corral.',
            'timestamp': 1437758640,
            'upload_date': '20150724',
            'uploader': 'NBCU-SPROUT-NEW',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_component = self._search_regex(
            r'(?s)(<div[^>]+data-component="video"[^>]*?>)',
            webpage, 'video component', default=None)
        if video_component:
            options = self._parse_json(extract_attributes(
                video_component)['data-options'], video_id)
            theplatform_url = options['video']
            query = {
                'mbr': 'true',
                'manifest': 'm3u',
            }
            if options.get('protected'):
                query['auth'] = self._extract_mvpd_auth(url, options['pid'], 'sprout', 'sprout')
            theplatform_url = smuggle_url(update_url_query(
                theplatform_url, query), {'force_smil_url': True})
        else:
            iframe = self._search_regex(
                r'(<iframe[^>]+id="sproutVideoIframe"[^>]*?>)',
                webpage, 'iframe')
            theplatform_url = extract_attributes(iframe)['src']

        return self.url_result(theplatform_url, 'ThePlatform')
