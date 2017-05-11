# coding: utf-8
from __future__ import unicode_literals, division

from .common import InfoExtractor
from ..utils import int_or_none


class CrackleIE(InfoExtractor):
    _GEO_COUNTRIES = ['US']
    _VALID_URL = r'(?:crackle:|https?://(?:(?:www|m)\.)?crackle\.com/(?:playlist/\d+/|(?:[^/]+/)+))(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.crackle.com/comedians-in-cars-getting-coffee/2498934',
        'info_dict': {
            'id': '2498934',
            'ext': 'mp4',
            'title': 'Everybody Respects A Bloody Nose',
            'description': 'Jerry is kaffeeklatsching in L.A. with funnyman J.B. Smoove (Saturday Night Live, Real Husbands of Hollywood). They’re headed for brew at 10 Speed Coffee in a 1964 Studebaker Avanti.',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 906,
            'series': 'Comedians In Cars Getting Coffee',
            'season_number': 8,
            'episode_number': 4,
            'subtitles': {
                'en-US': [
                    {'ext': 'vtt'},
                    {'ext': 'tt'},
                ]
            },
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }

    _THUMBNAIL_RES = [
        (120, 90),
        (208, 156),
        (220, 124),
        (220, 220),
        (240, 180),
        (250, 141),
        (315, 236),
        (320, 180),
        (360, 203),
        (400, 300),
        (421, 316),
        (460, 330),
        (460, 460),
        (462, 260),
        (480, 270),
        (587, 330),
        (640, 480),
        (700, 330),
        (700, 394),
        (854, 480),
        (1024, 1024),
        (1920, 1080),
    ]

    # extracted from http://legacyweb-us.crackle.com/flash/ReferrerRedirect.ashx
    _MEDIA_FILE_SLOTS = {
        'c544.flv': {
            'width': 544,
            'height': 306,
        },
        '360p.mp4': {
            'width': 640,
            'height': 360,
        },
        '480p.mp4': {
            'width': 852,
            'height': 478,
        },
        '480p_1mbps.mp4': {
            'width': 852,
            'height': 478,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        config_doc = self._download_xml(
            'http://legacyweb-us.crackle.com/flash/QueryReferrer.ashx?site=16',
            video_id, 'Downloading config')

        item = self._download_xml(
            'http://legacyweb-us.crackle.com/app/revamp/vidwallcache.aspx?flags=-1&fm=%s' % video_id,
            video_id, headers=self.geo_verification_headers()).find('i')
        title = item.attrib['t']

        subtitles = {}
        formats = self._extract_m3u8_formats(
            'http://content.uplynk.com/ext/%s/%s.m3u8' % (config_doc.attrib['strUplynkOwnerId'], video_id),
            video_id, 'mp4', m3u8_id='hls', fatal=None)
        thumbnails = []
        path = item.attrib.get('p')
        if path:
            for width, height in self._THUMBNAIL_RES:
                res = '%dx%d' % (width, height)
                thumbnails.append({
                    'id': res,
                    'url': 'http://images-us-am.crackle.com/%stnl_%s.jpg' % (path, res),
                    'width': width,
                    'height': height,
                    'resolution': res,
                })
            http_base_url = 'http://ahttp.crackle.com/' + path
            for mfs_path, mfs_info in self._MEDIA_FILE_SLOTS.items():
                formats.append({
                    'url': http_base_url + mfs_path,
                    'format_id': 'http-' + mfs_path.split('.')[0],
                    'width': mfs_info['width'],
                    'height': mfs_info['height'],
                })
            for cc in item.findall('cc'):
                locale = cc.attrib.get('l')
                v = cc.attrib.get('v')
                if locale and v:
                    if locale not in subtitles:
                        subtitles[locale] = []
                    for url_ext, ext in (('vtt', 'vtt'), ('xml', 'tt')):
                        subtitles.setdefault(locale, []).append({
                            'url': '%s/%s%s_%s.%s' % (config_doc.attrib['strSubtitleServer'], path, locale, v, url_ext),
                            'ext': ext,
                        })
        self._sort_formats(formats, ('width', 'height', 'tbr', 'format_id'))

        return {
            'id': video_id,
            'title': title,
            'description': item.attrib.get('d'),
            'duration': int(item.attrib.get('r'), 16) / 1000 if item.attrib.get('r') else None,
            'series': item.attrib.get('sn'),
            'season_number': int_or_none(item.attrib.get('se')),
            'episode_number': int_or_none(item.attrib.get('ep')),
            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'formats': formats,
        }
