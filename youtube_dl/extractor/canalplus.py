# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    ExtractorError,
    HEADRequest,
    unified_strdate,
    qualities,
    int_or_none,
)


class CanalplusIE(InfoExtractor):
    IE_DESC = 'canalplus.fr, piwiplus.fr and d8.tv'
    _VALID_URL = r'''(?x)
                        https?://
                            (?:
                                (?:
                                    (?:(?:www|m)\.)?canalplus\.fr|
                                    (?:www\.)?piwiplus\.fr|
                                    (?:www\.)?d8\.tv|
                                    (?:www\.)?c8\.fr|
                                    (?:www\.)?d17\.tv|
                                    (?:www\.)?itele\.fr
                                )/(?:(?:[^/]+/)*(?P<display_id>[^/?#&]+))?(?:\?.*\bvid=(?P<vid>\d+))?|
                                player\.canalplus\.fr/#/(?P<id>\d+)
                            )

                    '''
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/%s/%s?format=json'
    _SITE_ID_MAP = {
        'canalplus': 'cplus',
        'piwiplus': 'teletoon',
        'd8': 'd8',
        'c8': 'd8',
        'd17': 'd17',
        'itele': 'itele',
    }

    _TESTS = [{
        'url': 'http://www.canalplus.fr/c-emissions/pid1830-c-zapping.html?vid=1192814',
        'md5': '41f438a4904f7664b91b4ed0dec969dc',
        'info_dict': {
            'id': '1192814',
            'ext': 'mp4',
            'title': "L'Année du Zapping 2014 - L'Année du Zapping 2014",
            'description': "Toute l'année 2014 dans un Zapping exceptionnel !",
            'upload_date': '20150105',
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
        'url': 'http://www.d8.tv/d8-docs-mags/pid5198-d8-en-quete-d-actualite.html?vid=1390231',
        'info_dict': {
            'id': '1390231',
            'ext': 'mp4',
            'title': "Vacances pas chères : prix discount ou grosses dépenses ? - En quête d'actualité",
            'description': 'md5:edb6cf1cb4a1e807b5dd089e1ac8bfc6',
            'upload_date': '20160512',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.itele.fr/chroniques/invite-bruce-toussaint/thierry-solere-nicolas-sarkozy-officialisera-sa-candidature-a-la-primaire-quand-il-le-voudra-167224',
        'info_dict': {
            'id': '1398334',
            'ext': 'mp4',
            'title': "L'invité de Bruce Toussaint du 07/06/2016 - ",
            'description': 'md5:40ac7c9ad0feaeb6f605bad986f61324',
            'upload_date': '20160607',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://m.canalplus.fr/?vid=1398231',
        'only_matching': True,
    }, {
        'url': 'http://www.d17.tv/emissions/pid8303-lolywood.html?vid=1397061',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.groupdict().get('id') or mobj.groupdict().get('vid')

        site_id = self._SITE_ID_MAP[compat_urllib_parse_urlparse(url).netloc.rsplit('.', 2)[-2]]

        # Beware, some subclasses do not define an id group
        display_id = mobj.group('display_id') or video_id

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
