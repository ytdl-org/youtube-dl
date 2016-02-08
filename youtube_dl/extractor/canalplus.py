# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
    unified_strdate,
    url_basename,
    qualities,
    int_or_none,
)


class CanalplusIE(InfoExtractor):
    IE_DESC = 'canalplus.fr, piwiplus.fr and d8.tv'
    _VALID_URL = r'https?://(?:www\.(?P<site>canalplus\.fr|piwiplus\.fr|d8\.tv|itele\.fr)/.*?/(?P<path>.*)|player\.canalplus\.fr/#/(?P<id>[0-9]+))'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/%s/%s?format=json'
    _SITE_ID_MAP = {
        'canalplus.fr': 'cplus',
        'piwiplus.fr': 'teletoon',
        'd8.tv': 'd8',
        'itele.fr': 'itele',
    }

    _TESTS = [{
        'url': 'http://www.canalplus.fr/c-emissions/pid1830-c-zapping.html?vid=1263092',
        'md5': '12164a6f14ff6df8bd628e8ba9b10b78',
        'info_dict': {
            'id': '1263092',
            'ext': 'mp4',
            'title': 'Le Zapping - 13/05/15',
            'description': 'md5:09738c0d06be4b5d06a0940edb0da73f',
            'upload_date': '20150513',
        },
    }, {
        'url': 'http://www.piwiplus.fr/videos-piwi/pid1405-le-labyrinthe-boing-super-ranger.html?vid=1108190',
        'info_dict': {
            'id': '1108190',
            'ext': 'flv',
            'title': 'Le labyrinthe - Boing super ranger',
            'description': 'md5:4cea7a37153be42c1ba2c1d3064376ff',
            'upload_date': '20140724',
        },
        'skip': 'Only works from France',
    }, {
        'url': 'http://www.d8.tv/d8-docs-mags/pid6589-d8-campagne-intime.html',
        'info_dict': {
            'id': '966289',
            'ext': 'flv',
            'title': 'Campagne intime - Documentaire exceptionnel',
            'description': 'md5:d2643b799fb190846ae09c61e59a859f',
            'upload_date': '20131108',
        },
        'skip': 'videos get deleted after a while',
    }, {
        'url': 'http://www.itele.fr/france/video/aubervilliers-un-lycee-en-colere-111559',
        'md5': '38b8f7934def74f0d6f3ba6c036a5f82',
        'info_dict': {
            'id': '1213714',
            'ext': 'mp4',
            'title': 'Aubervilliers : un lycée en colère - Le 11/02/2015 à 06h45',
            'description': 'md5:8216206ec53426ea6321321f3b3c16db',
            'upload_date': '20150211',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.groupdict().get('id')

        site_id = self._SITE_ID_MAP[mobj.group('site') or 'canal']

        # Beware, some subclasses do not define an id group
        display_id = url_basename(mobj.group('path'))

        if video_id is None:
            webpage = self._download_webpage(url, display_id)
            video_id = self._search_regex(
                [r'<canal:player[^>]+?videoId=(["\'])(?P<id>\d+)', r'id=["\']canal_video_player(?P<id>\d+)'],
                webpage, 'video id', group='id')

        info_url = self._VIDEO_INFO_TEMPLATE % (site_id, video_id)
        video_data = self._download_json(info_url, video_id, 'Downloading video JSON')

        if isinstance(video_data, list):
            video_data = [video for video in video_data if video.get('ID') == video_id][0]
        media = video_data['MEDIA']
        infos = video_data['INFOS']

        preference = qualities(['MOBILE', 'BAS_DEBIT', 'HAUT_DEBIT', 'HD'])

        fmt_url = next(iter(media.get('VIDEOS')))
        if '/geo' in fmt_url.lower():
            response = self._request_webpage(
                HEADRequest(fmt_url), video_id,
                'Checking if the video is georestricted')
            if '/blocage' in response.geturl():
                raise ExtractorError(
                    'The video is not available in your country',
                    expected=True)

        formats = []
        for format_id, format_url in media['VIDEOS'].items():
            if not format_url:
                continue
            if format_id == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', 'm3u8_native', m3u8_id=format_id, fatal=False))
            elif format_id == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url + '?hdcore=2.11.3', video_id, f4m_id=format_id, fatal=False))
            else:
                formats.append({
                    # the secret extracted ya function in http://player.canalplus.fr/common/js/canalPlayer.js
                    'url': format_url + '?secret=pqzerjlsmdkjfoiuerhsdlfknaes',
                    'format_id': format_id,
                    'preference': preference(format_id),
                })
        self._sort_formats(formats)

        thumbnails = [{
            'id': image_id,
            'url': image_url,
        } for image_id, image_url in media.get('images', {}).items()]

        titrage = infos['TITRAGE']

        return {
            'id': video_id,
            'display_id': display_id,
            'title': '%s - %s' % (titrage['TITRE'],
                                  titrage['SOUS_TITRE']),
            'upload_date': unified_strdate(infos.get('PUBLICATION', {}).get('DATE')),
            'thumbnails': thumbnails,
            'description': infos.get('DESCRIPTION'),
            'duration': int_or_none(infos.get('DURATION')),
            'view_count': int_or_none(infos.get('NB_VUES')),
            'like_count': int_or_none(infos.get('NB_LIKES')),
            'comment_count': int_or_none(infos.get('NB_COMMENTS')),
            'formats': formats,
        }
