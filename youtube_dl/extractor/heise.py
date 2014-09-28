# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    get_meta_content,
    parse_iso8601,
)


class HeiseIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?heise\.de/video/artikel/
        .+?(?P<id>[0-9]+)\.html(?:$|[?#])
    '''
    _TEST = {
        'url': (
            'http://www.heise.de/video/artikel/Podcast-c-t-uplink-3-3-Owncloud-Tastaturen-Peilsender-Smartphone-2404147.html'
        ),
        'md5': 'ffed432483e922e88545ad9f2f15d30e',
        'info_dict': {
            'id': '2404147',
            'ext': 'mp4',
            'title': (
                "Podcast: c't uplink 3.3 – Owncloud / Tastaturen / Peilsender Smartphone"
            ),
            'format_id': 'mp4_720',
            'timestamp': 1411812600,
            'upload_date': '20140927',
            'description': 'In uplink-Episode 3.3 geht es darum, wie man sich von Cloud-Anbietern emanzipieren kann, worauf man beim Kauf einer Tastatur achten sollte und was Smartphones über uns verraten.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        json_url = self._search_regex(
            r'json_url:\s*"([^"]+)"', webpage, 'json URL')
        config = self._download_json(json_url, video_id)

        info = {
            'id': video_id,
            'thumbnail': config.get('poster'),
            'timestamp': parse_iso8601(get_meta_content('date', webpage)),
            'description': self._og_search_description(webpage),
        }

        title = get_meta_content('fulltitle', webpage)
        if title:
            info['title'] = title
        elif config.get('title'):
            info['title'] = config['title']
        else:
            info['title'] = self._og_search_title(webpage)

        formats = []
        for t, rs in config['formats'].items():
            if not rs or not hasattr(rs, 'items'):
                self._downloader.report_warning(
                    'formats: {0}: no resolutions'.format(t))
                continue

            for height_str, obj in rs.items():
                format_id = '{0}_{1}'.format(t, height_str)

                if not obj or not obj.get('url'):
                    self._downloader.report_warning(
                        'formats: {0}: no url'.format(format_id))
                    continue

                formats.append({
                    'url': obj['url'],
                    'format_id': format_id,
                    'height': self._int(height_str, 'height'),
                })

        self._sort_formats(formats)
        info['formats'] = formats

        return info
