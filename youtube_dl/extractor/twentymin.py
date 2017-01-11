# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    remove_end,
    ExtractorError
)


class TwentyMinutenIE(InfoExtractor):
    IE_NAME = '20min'
    _VALID_URL = r'https?://(?:www\.)?20min\.ch/(?:videotv/*\?.*\bvid=(?P<id>\d+)|(?:[^/]+/)*(?P<display_id>[^/#?]+))'
    _TESTS = [{
        # regular video
        'url': 'http://www.20min.ch/videotv/?vid=469148&cid=2',
        'md5': 'e7264320db31eed8c38364150c12496e',
        'info_dict': {
            'id': '469148',
            'ext': 'mp4',
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
        },
        'skip': '"This video is no longer available" is shown both on the web page and in the downloaded file.',
    }, {
        # news article with video
        'url': 'http://www.20min.ch/schweiz/news/story/So-kommen-Sie-bei-Eis-und-Schnee-sicher-an-27032552',
        'md5': '807f9e1e06a69b77440a9b315e52e580',
        'info_dict': {
            'id': '523629',
            'display_id': 'So-kommen-Sie-bei-Eis-und-Schnee-sicher-an-27032552',
            'ext': 'mp4',
            'title': 'So kommen Sie bei Eis und Schnee sicher an',
            'description': 'Schneegestöber und Glatteis führten in den letzten Tagen zu zahlreichen Strassenunfällen. Ein Experte erklärt, worauf man nun beim Autofahren achten muss.',
            'thumbnail': 'http://www.20min.ch/images/content/2/7/0/27032552/83/teaserbreit.jpg',
        }
    }, {
        # YouTube embed
        'url': 'http://www.20min.ch/ro/sports/football/story/Il-marque-une-bicyclette-de-plus-de-30-metres--21115184',
        'md5': 'e7e237fd98da2a3cc1422ce683df234d',
        'info_dict': {
            'id': 'ivM7A7SpDOs',
            'ext': 'mp4',
            'title': 'GOLAZO DE CHILENA DE JAVI GÓMEZ, FINALISTA AL BALÓN DE CLM 2016',
            'description': 'md5:903c92fbf2b2f66c09de514bc25e9f5a',
            'upload_date': '20160424',
            'uploader': 'CMM Castilla-La Mancha Media',
            'uploader_id': 'RTVCM',
        },
        'add_ie': ['Youtube'],
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

        youtube_url = self._html_search_regex(
            r'<iframe[^>]+src="((?:https?:)?//www\.youtube\.com/embed/[^"]+)"',
            webpage, 'YouTube embed URL', default=None)
        if youtube_url is not None:
            return self.url_result(youtube_url, 'Youtube')

        title = self._html_search_regex(
            r'<h1>.*?<span>(.+?)</span></h1>',
            webpage, 'title', default=None)
        if not title:
            title = remove_end(re.sub(
                r'^20 [Mm]inuten.*? -', '', self._og_search_title(webpage)), ' - News')

        if not video_id:
            params = self._html_search_regex(
                r'<iframe[^>]+src="(?:https?:)?//www\.20min\.ch/videoplayer/videoplayer\.html\?params=(.+?[^"])"',
                webpage, '20min embed URL', default=None)
            video_id = self._search_regex(
                r'.*videoId@(\d+)',
                params, 'Video Id', default=None) if params is not None else ''
            if not video_id: # the article does not contain a video
                raise ExtractorError('No media links found on %s.' % url, expected=True)

        description = self._html_search_meta('description', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': 'http://podcast.20min-tv.ch/podcast/20min/%sh.mp4' % video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
