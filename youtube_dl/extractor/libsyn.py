# encoding: utf-8
from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)

class LibsynIE(InfoExtractor):
    _VALID_URL = r'(?:https?:)?//html5-player\.libsyn\.com/embed/episode/id/(?P<id>[0-9]+)(?:/.*)?'

    def _real_extract(self, url):
        if url.startswith('//'):
            url = 'https:' + url
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        podcast_title         = self._search_regex(r'<h2>(.*?)</h2>', webpage, 'show title')
        podcast_episode_title = self._search_regex(r'<h3>(.*?)</h3>', webpage, 'episode title')
        podcast_date          = unified_strdate(self._search_regex(r'<div class="release_date">Released: (.*?)</div>', webpage, 'release date'))
        podcast_description   = self._search_regex(r'<div id="info_text_body">(.*?)</div>', webpage, 'description')

        url0 = self._search_regex(r'var mediaURLLibsyn = "(?P<url0>https?://.*)";', webpage, 'first media URL')
        url1 = self._search_regex(r'var mediaURL = "(?P<url1>https?://.*)";', webpage, 'second media URL')

        if url0 != url1:
            formats = [{
                'url': url0
            }, {
                'url': url1
            }]
        else:
            formats = [{
                'url': url0
            }]

        return {
            'id': display_id,
            'title': podcast_episode_title,
            'description': podcast_description,
            'upload_date': podcast_date,
            'formats': formats,
        }
