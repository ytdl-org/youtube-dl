# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
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
            'format_id': 'mp4_720p',
            'timestamp': 1411812600,
            'upload_date': '20140927',
            'description': 'In uplink-Episode 3.3 geht es darum, wie man sich von Cloud-Anbietern emanzipieren kann, worauf man beim Kauf einer Tastatur achten sollte und was Smartphones über uns verraten.',
            'thumbnail': 're:^https?://.*\.jpe?g$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        container_id = self._search_regex(
            r'<div class="videoplayerjw".*?data-container="([0-9]+)"',
            webpage, 'container ID')
        sequenz_id = self._search_regex(
            r'<div class="videoplayerjw".*?data-sequenz="([0-9]+)"',
            webpage, 'sequenz ID')
        data_url = 'http://www.heise.de/videout/feed?container=%s&sequenz=%s' % (container_id, sequenz_id)
        doc = self._download_xml(data_url, video_id)

        info = {
            'id': video_id,
            'thumbnail': self._og_search_thumbnail(webpage),
            'timestamp': parse_iso8601(
                self._html_search_meta('date', webpage)),
            'description': self._og_search_description(webpage),
        }

        title = self._html_search_meta('fulltitle', webpage)
        if title:
            info['title'] = title
        else:
            info['title'] = self._og_search_title(webpage)

        formats = []
        for source_node in doc.findall('.//{http://rss.jwpcdn.com/}source'):
            label = source_node.attrib['label']
            height = int_or_none(self._search_regex(
                r'^(.*?_)?([0-9]+)p$', label, 'height', default=None))
            video_url = source_node.attrib['file']
            ext = determine_ext(video_url, '')
            formats.append({
                'url': video_url,
                'format_note': label,
                'format_id': '%s_%s' % (ext, label),
                'height': height,
            })
        self._sort_formats(formats)
        info['formats'] = formats

        return info
