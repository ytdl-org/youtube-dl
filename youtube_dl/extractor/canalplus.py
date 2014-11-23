# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    url_basename,
    qualities,
)


class CanalplusIE(InfoExtractor):
    IE_DESC = 'canalplus.fr, piwiplus.fr and d8.tv'
    _VALID_URL = r'https?://(?:www\.(?P<site>canalplus\.fr|piwiplus\.fr|d8\.tv)/.*?/(?P<path>.*)|player\.canalplus\.fr/#/(?P<id>[0-9]+))'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/%s/%s'
    _SITE_ID_MAP = {
        'canalplus.fr': 'cplus',
        'piwiplus.fr': 'teletoon',
        'd8.tv': 'd8',
    }

    _TESTS = [{
        'url': 'http://www.canalplus.fr/c-infos-documentaires/pid1830-c-zapping.html?vid=922470',
        'md5': '3db39fb48b9685438ecf33a1078023e4',
        'info_dict': {
            'id': '922470',
            'ext': 'flv',
            'title': 'Zapping - 26/08/13',
            'description': 'Le meilleur de toutes les chaînes, tous les jours.\nEmission du 26 août 2013',
            'upload_date': '20130826',
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
                r'<canal:player[^>]+?videoId="(\d+)"', webpage, 'video id')

        info_url = self._VIDEO_INFO_TEMPLATE % (site_id, video_id)
        doc = self._download_xml(info_url, video_id, 'Downloading video XML')

        video_info = [video for video in doc if video.find('ID').text == video_id][0]
        media = video_info.find('MEDIA')
        infos = video_info.find('INFOS')

        preference = qualities(['MOBILE', 'BAS_DEBIT', 'HAUT_DEBIT', 'HD', 'HLS', 'HDS'])

        formats = []
        for fmt in media.find('VIDEOS'):
            format_url = fmt.text
            if not format_url:
                continue
            format_id = fmt.tag
            if format_id == 'HLS':
                hls_formats = self._extract_m3u8_formats(format_url, video_id, 'flv')
                for fmt in hls_formats:
                    fmt['preference'] = preference(format_id)
                formats.extend(hls_formats)
            elif format_id == 'HDS':
                hds_formats = self._extract_f4m_formats(format_url + '?hdcore=2.11.3', video_id)
                for fmt in hds_formats:
                    fmt['preference'] = preference(format_id)
                formats.extend(hds_formats)
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
