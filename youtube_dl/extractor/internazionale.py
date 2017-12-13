# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class InternazionaleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?internazionale\.it/video/(?P<id>.*)'
    _TESTS = [{
        'url': 'https://www.internazionale.it/video/2015/02/19/richard-linklater-racconta-una-scena-di-boyhood',
        'md5': '11b54a3d3333e455c00684e50a65c58e',
        'info_dict': {
            'id': '265968',
            'ext': 'mp4',
            'description': 'Il regista statunitense Richard Linklater ci racconta una scena del film Boyhood e la sua passione per l’imprecisione della memoria. Il film è un’avventura durata 12 anni, durante la quale Linklater ha seguito il protagonista dal 2002 al 2014 per raccontare la sua crescita e il rapporto con i genitori divorziati. Leggi',
            'title': 'Richard Linklater racconta una scena di Boyhood',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'https://www.internazionale.it/video/2017/10/18/storie-italiani-senza-cittadinanza',
        'md5': '4c6feb9658b22c95e3fa4b5c070d69ba',
        'info_dict': {
            'id': '648175',
            'ext': 'mp4',
            'description': 'Tre ragazzi raccontano quanto è difficile essere italiani di fatto ma non di diritto: una vita fatta di burocrazia, opportunità negate e grandi contraddizioni. Leggi',
            'title': 'Storie di italiani senza cittadinanza',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_container = self._html_search_regex(r'<div class="video-container" (.*)>', webpage, 'video_container')

        id = self._html_search_regex(r'data-job-id="([^"]+)"', video_container, 'id')
        video_path = self._html_search_regex(r'data-video-path="([^"]+)"', video_container, 'video_path')

        return {
            'id': id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'formats': [{
                'url': 'https://video.internazionale.it/%s/%s.m3u8'
                       % (video_path, id),
                'ext': 'mp4',
                'protocol': 'm3u8',
            }]
        }
