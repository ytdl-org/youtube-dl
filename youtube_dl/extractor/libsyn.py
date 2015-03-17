# encoding: utf-8
from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)

class LibsynIE(InfoExtractor):
    _VALID_URL = r'(?:https?:)?//html5-player\.libsyn\.com/embed/episode/id/(?P<id>[0-9]+)(?:/.*)?'
    _TESTS = [{
        'url': "http://html5-player.libsyn.com/embed/episode/id/3377616/",
        'info_dict': {
            'id': "3377616",
            'ext': "mp3",
            'title': "Episode 12: Bassem Youssef: Egypt's Jon Stewart",
            'description': "<p>Bassem Youssef joins executive producer Steve Bodow and senior producer Sara Taksler for a conversation about how&nbsp;<em style=\"font-family: Tahoma, Geneva, sans-serif; font-size: 12.8000001907349px;\">The Daily Show</em>&nbsp;inspired Bassem to create&nbsp;<em style=\"font-family: Tahoma, Geneva, sans-serif; font-size: 12.8000001907349px;\">Al-Bernameg</em>, his massively popular (and now banned) Egyptian news satire program. Sara discusses her soon-to-be-released documentary,&nbsp;<em style=\"font-family: Tahoma, Geneva, sans-serif; font-size: 12.8000001907349px;\">Tickling Giants</em>, which chronicles how Bassem and his staff risked their safety every day to tell jokes.</p>",
        },
    }]

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
