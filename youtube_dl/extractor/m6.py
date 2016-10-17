# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class M6IE(InfoExtractor):
    IE_NAME = 'm6'
    _VALID_URL = r'https?://(?:www\.)?m6\.fr/[^/]+/videos/(?P<id>\d+)-[^\.]+\.html'

    _TEST = {
        'url': 'http://www.m6.fr/emission-les_reines_du_shopping/videos/11323908-emeline_est_la_reine_du_shopping_sur_le_theme_ma_fete_d_8217_anniversaire.html',
        'md5': '242994a87de2c316891428e0176bcb77',
        'info_dict': {
            'id': '11323908',
            'ext': 'mp4',
            'title': 'Emeline est la Reine du Shopping sur le thème « Ma fête d’anniversaire ! »',
            'description': 'md5:1212ae8fb4b7baa4dc3886c5676007c2',
            'duration': 100,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        rss = self._download_xml('http://ws.m6.fr/v1/video/info/m6/bonus/%s' % video_id, video_id,
                                 'Downloading video RSS')

        title = rss.find('./channel/item/title').text
        description = rss.find('./channel/item/description').text
        thumbnail = rss.find('./channel/item/visuel_clip_big').text
        duration = int(rss.find('./channel/item/duration').text)
        view_count = int(rss.find('./channel/item/nombre_vues').text)

        formats = []
        for format_id in ['lq', 'sd', 'hq', 'hd']:
            video_url = rss.find('./channel/item/url_video_%s' % format_id)
            if video_url is None:
                continue
            formats.append({
                'url': video_url.text,
                'format_id': format_id,
            })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
