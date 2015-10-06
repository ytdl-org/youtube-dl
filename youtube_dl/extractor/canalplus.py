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
)


class CanalplusIE(InfoExtractor):
    IE_DESC = 'canalplus.fr, piwiplus.fr and d8.tv'
    _VALID_URL = r'https?://(?:www\.(?P<site>canalplus\.fr|piwiplus\.fr|d8\.tv|itele\.fr)/.*?/(?P<path>.*)|player\.canalplus\.fr/#/(?P<id>[0-9]+))'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/%s/%s'
    _SITE_ID_MAP = {
        'canalplus.fr': 'cplus',
        'piwiplus.fr': 'teletoon',
        'd8.tv': 'd8',
        'itele.fr': 'itele',
    }

    _TESTS = [{
        'url': 'http://www.canalplus.fr/c-emissions/pid1830-c-zapping.html?vid=1263092',
        'md5': 'b3481d7ca972f61e37420798d0a9d934',
        'info_dict': {
            'id': '1263092',
            'ext': 'flv',
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
        'md5': 'f3a46edcdf28006598ffaf5b30e6a2d4',
        'info_dict': {
            'id': '1213714',
            'ext': 'flv',
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
        doc = self._download_xml(info_url, video_id, 'Downloading video XML')

        video_info = [video for video in doc if video.find('ID').text == video_id][0]
        media = video_info.find('MEDIA')
        infos = video_info.find('INFOS')

        preference = qualities(['MOBILE', 'BAS_DEBIT', 'HAUT_DEBIT', 'HD', 'HLS', 'HDS'])

        fmt_url = next(iter(media.find('VIDEOS'))).text
        if '/geo' in fmt_url.lower():
            response = self._request_webpage(
                HEADRequest(fmt_url), video_id,
                'Checking if the video is georestricted')
            if '/blocage' in response.geturl():
                raise ExtractorError(
                    'The video is not available in your country',
                    expected=True)

        formats = []
        for fmt in media.find('VIDEOS'):
            format_url = fmt.text
            if not format_url:
                continue
            format_id = fmt.tag
            if format_id == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', preference=preference(format_id)))
            elif format_id == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url + '?hdcore=2.11.3', video_id, preference=preference(format_id)))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'preference': preference(format_id),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': '%s - %s' % (infos.find('TITRAGE/TITRE').text,
                                  infos.find('TITRAGE/SOUS_TITRE').text),
            'upload_date': unified_strdate(infos.find('PUBLICATION/DATE').text),
            'thumbnail': media.find('IMAGES/GRAND').text,
            'description': infos.find('DESCRIPTION').text,
            'view_count': int(infos.find('NB_VUES').text),
            'like_count': int(infos.find('NB_LIKES').text),
            'comment_count': int(infos.find('NB_COMMENTS').text),
            'formats': formats,
        }
