from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    compat_urllib_parse,
    ExtractorError,
)


class MixcloudIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([^/]+)/([^/]+)'
    IE_NAME = 'mixcloud'

    _TEST = {
        'url': 'http://www.mixcloud.com/dholbach/cryptkeeper/',
        'info_dict': {
            'id': 'dholbach-cryptkeeper',
            'ext': 'mp3',
            'title': 'Cryptkeeper',
            'description': 'After quite a long silence from myself, finally another Drum\'n\'Bass mix with my favourite current dance floor bangers.',
            'uploader': 'Daniel Holbach',
            'uploader_id': 'dholbach',
            'upload_date': '20111115',
        },
    }

    def check_urls(self, url_list):
        """Returns 1st active url from list"""
        for url in url_list:
            try:
                # We only want to know if the request succeed
                # don't download the whole file
                self._request_webpage(url, None, False)
                return url
            except ExtractorError:
                url = None

        return None

    def _get_url(self, template_url):
        return self.check_urls(template_url % i for i in range(30))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group(1)
        cloudcast_name = mobj.group(2)
        track_id = compat_urllib_parse.unquote('-'.join((uploader, cloudcast_name)))

        webpage = self._download_webpage(url, track_id)

        api_url = 'http://api.mixcloud.com/%s/%s/' % (uploader, cloudcast_name)
        info = self._download_json(
            api_url, track_id, 'Downloading cloudcast info')

        preview_url = self._search_regex(
            r'\s(?:data-preview-url|m-preview)="(.+?)"', webpage, 'preview url')
        song_url = preview_url.replace('/previews/', '/c/originals/')
        template_url = re.sub(r'(stream\d*)', 'stream%d', song_url)
        final_song_url = self._get_url(template_url)
        if final_song_url is None:
            self.to_screen('Trying with m4a extension')
            template_url = template_url.replace('.mp3', '.m4a').replace('originals/', 'm4a/64/')
            final_song_url = self._get_url(template_url)
        if final_song_url is None:
            raise ExtractorError(u'Unable to extract track url')

        return {
            'id': track_id,
            'title': info['name'],
            'url': final_song_url,
            'description': info.get('description'),
            'thumbnail': info['pictures'].get('extra_large'),
            'uploader': info['user']['name'],
            'uploader_id': info['user']['username'],
            'upload_date': unified_strdate(info['created_time']),
            'view_count': info['play_count'],
        }
