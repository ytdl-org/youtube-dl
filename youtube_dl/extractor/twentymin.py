# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import remove_end


class TwentyMinutenIE(InfoExtractor):
    IE_NAME = '20min'
    _VALID_URL = r'https?://(?:www\.)?20min\.ch/(?:videotv/*\?.*\bvid=(?P<id>\d+)|(?:[^/]+/)*(?P<display_id>[^/#?]+))'
    _TESTS = [{
        # regular video
        'url': 'http://www.20min.ch/videotv/?vid=469148&cid=2',
        'md5': 'b52d6bc6ea6398e6a38f12cfd418149c',
        'info_dict': {
            'id': '469148',
            'ext': 'flv',
            'title': '85 000 Franken für 15 perfekte Minuten',
            'description': 'Was die Besucher vom Silvesterzauber erwarten können. (Video: Alice Grosjean/Murat Temel)',
            'thumbnail': 'http://thumbnails.20min-tv.ch/server063/469148/frame-72-469148.jpg'
        }
    }, {
        # news article with video
        'url': 'http://www.20min.ch/schweiz/news/story/-Wir-muessen-mutig-nach-vorne-schauen--22050469',
        'md5': 'cd4cbb99b94130cff423e967cd275e5e',
        'info_dict': {
            'id': '469408',
            'display_id': '-Wir-muessen-mutig-nach-vorne-schauen--22050469',
            'ext': 'flv',
            'title': '«Wir müssen mutig nach vorne schauen»',
            'description': 'Kein Land sei innovativer als die Schweiz, sagte Johann Schneider-Ammann in seiner Neujahrsansprache. Das Land müsse aber seine Hausaufgaben machen.',
            'thumbnail': 'http://www.20min.ch/images/content/2/2/0/22050469/10/teaserbreit.jpg'
        }
    }, {
        'url': 'http://www.20min.ch/videotv/?cid=44&vid=468738',
        'only_matching': True,
    }, {
        'url': 'http://www.20min.ch/ro/sortir/cinema/story/Grandir-au-bahut--c-est-dur-18927411',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_regex(
            r'<h1>.*?<span>(.+?)</span></h1>',
            webpage, 'title', default=None)
        if not title:
            title = remove_end(re.sub(
                r'^20 [Mm]inuten.*? -', '', self._og_search_title(webpage)), ' - News')

        if not video_id:
            video_id = self._search_regex(
                r'"file\d?"\s*,\s*\"(\d+)', webpage, 'video id')

        description = self._html_search_meta(
            'description', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': 'http://speed.20min-tv.ch/%sm.flv' % video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
