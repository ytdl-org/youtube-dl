# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    xpath_text,
)


class HeiseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?heise\.de/(?:[^/]+/)+[^/]+-(?P<id>[0-9]+)\.html'
    _TESTS = [{
        'url': 'http://www.heise.de/video/artikel/Podcast-c-t-uplink-3-3-Owncloud-Tastaturen-Peilsender-Smartphone-2404147.html',
        'md5': 'ffed432483e922e88545ad9f2f15d30e',
        'info_dict': {
            'id': '2404147',
            'ext': 'mp4',
            'title': "Podcast: c't uplink 3.3 – Owncloud / Tastaturen / Peilsender Smartphone",
            'format_id': 'mp4_720p',
            'timestamp': 1411812600,
            'upload_date': '20140927',
            'description': 'md5:c934cbfb326c669c2bcabcbe3d3fcd20',
            'thumbnail': r're:^https?://.*/gallery/$',
        }
    }, {
        'url': 'http://www.heise.de/ct/artikel/c-t-uplink-3-3-Owncloud-Tastaturen-Peilsender-Smartphone-2403911.html',
        'only_matching': True,
    }, {
        'url': 'http://www.heise.de/newsticker/meldung/c-t-uplink-Owncloud-Tastaturen-Peilsender-Smartphone-2404251.html?wt_mc=rss.ho.beitrag.atom',
        'only_matching': True,
    }, {
        'url': 'http://www.heise.de/ct/ausgabe/2016-12-Spiele-3214137.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        container_id = self._search_regex(
            r'<div class="videoplayerjw"[^>]+data-container="([0-9]+)"',
            webpage, 'container ID')
        sequenz_id = self._search_regex(
            r'<div class="videoplayerjw"[^>]+data-sequenz="([0-9]+)"',
            webpage, 'sequenz ID')

        title = self._html_search_meta('fulltitle', webpage, default=None)
        if not title or title == "c't":
            title = self._search_regex(
                r'<div[^>]+class="videoplayerjw"[^>]+data-title="([^"]+)"',
                webpage, 'title')

        doc = self._download_xml(
            'http://www.heise.de/videout/feed', video_id, query={
                'container': container_id,
                'sequenz': sequenz_id,
            })

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

        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'description', webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': (xpath_text(doc, './/{http://rss.jwpcdn.com/}image') or
                          self._og_search_thumbnail(webpage)),
            'timestamp': parse_iso8601(
                self._html_search_meta('date', webpage)),
            'formats': formats,
        }
