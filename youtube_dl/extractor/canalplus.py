# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    dict_get,
    ExtractorError,
    HEADRequest,
    int_or_none,
    qualities,
    remove_end,
    unified_strdate,
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
                                    (?:(?:football|www)\.)?cstar\.fr|
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
        'cstar': 'd17',
        'itele': 'itele',
    }

    _TESTS = [{
        'url': 'http://www.canalplus.fr/c-emissions/pid1830-c-zapping.html?vid=1192814',
        'info_dict': {
            'id': '1405510',
            'display_id': 'pid1830-c-zapping',
            'ext': 'mp4',
            'title': 'Zapping - 02/07/2016',
            'description': 'Le meilleur de toutes les chaînes, tous les jours',
            'upload_date': '20160702',
        },
    }, {
        'url': 'http://www.piwiplus.fr/videos-piwi/pid1405-le-labyrinthe-boing-super-ranger.html?vid=1108190',
        'info_dict': {
            'id': '1108190',
            'display_id': 'pid1405-le-labyrinthe-boing-super-ranger',
            'ext': 'mp4',
            'title': 'BOING SUPER RANGER - Ep : Le labyrinthe',
            'description': 'md5:4cea7a37153be42c1ba2c1d3064376ff',
            'upload_date': '20140724',
        },
        'skip': 'Only works from France',
    }, {
        'url': 'http://www.c8.fr/c8-divertissement/ms-touche-pas-a-mon-poste/pid6318-videos-integrales.html',
        'md5': '4b47b12b4ee43002626b97fad8fb1de5',
        'info_dict': {
            'id': '1420213',
            'display_id': 'pid6318-videos-integrales',
            'ext': 'mp4',
            'title': 'TPMP ! Même le matin - Les 35H de Baba - 14/10/2016',
            'description': 'md5:f96736c1b0ffaa96fd5b9e60ad871799',
            'upload_date': '20161014',
        },
        'skip': 'Only works from France',
    }, {
        'url': 'http://www.itele.fr/chroniques/invite-michael-darmon/rachida-dati-nicolas-sarkozy-est-le-plus-en-phase-avec-les-inquietudes-des-francais-171510',
        'info_dict': {
            'id': '1420176',
            'display_id': 'rachida-dati-nicolas-sarkozy-est-le-plus-en-phase-avec-les-inquietudes-des-francais-171510',
            'ext': 'mp4',
            'title': 'L\'invité de Michaël Darmon du 14/10/2016 - ',
            'description': 'Chaque matin du lundi au vendredi, Michaël Darmon reçoit un invité politique à 8h25.',
            'upload_date': '20161014',
        },
    }, {
        'url': 'http://football.cstar.fr/cstar-minisite-foot/pid7566-feminines-videos.html?vid=1416769',
        'info_dict': {
            'id': '1416769',
            'display_id': 'pid7566-feminines-videos',
            'ext': 'mp4',
            'title': 'France - Albanie : les temps forts de la soirée - 20/09/2016',
            'description': 'md5:c3f30f2aaac294c1c969b3294de6904e',
            'upload_date': '20160921',
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

        site_id = self._SITE_ID_MAP[compat_urllib_parse_urlparse(url).netloc.rsplit('.', 2)[-2]]

        # Beware, some subclasses do not define an id group
        display_id = remove_end(dict_get(mobj.groupdict(), ('display_id', 'id', 'vid')), '.html')

        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            [r'<canal:player[^>]+?videoId=(["\'])(?P<id>\d+)',
             r'id=["\']canal_video_player(?P<id>\d+)',
             r'data-video=["\'](?P<id>\d+)'],
            webpage, 'video id', default=mobj.group('vid'), group='id')

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
