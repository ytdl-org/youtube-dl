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
        https?://(?:www\.)?heise\.de/.+?(?P<id>[0-9]+)\.html(?:$|[?#])
    '''
    _TESTS = [
        {
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
                'thumbnail': r're:^https?://.*/gallery/$',
            }
        },
        {
            'url': (
                'http://www.heise.de/ct/artikel/c-t-uplink-3-3-Owncloud-Tastaturen-Peilsender-Smartphone-2403911.html'
            ),
            'md5': 'ffed432483e922e88545ad9f2f15d30e',
            'info_dict': {
                'id': '2403911',
                'ext': 'mp4',
                'title': (
                    "c't uplink 3.3: Owncloud, Tastaturen, Peilsender Smartphone"
                ),
                'format_id': 'mp4_720p',
                'timestamp': 1411803000,
                'upload_date': '20140927',
                'description': "In c't uplink erklären wir in dieser Woche, wie man mit Owncloud die Kontrolle über die eigenen Daten behält. Darüber hinaus erklären wir, dass zur Wahl der richtigen Tastatur mehr gehört, als man denkt und wie Smartphones uns weiter verraten.",
                'thumbnail': r're:^https?://.*/gallery/$',
            }
        },
        {
            'url': (
                'http://www.heise.de/newsticker/meldung/c-t-uplink-Owncloud-Tastaturen-Peilsender-Smartphone-2404251.html?wt_mc=rss.ho.beitrag.atom'
            ),
            'md5': 'ffed432483e922e88545ad9f2f15d30e',
            'info_dict': {
                'id': '2404251',
                'ext': 'mp4',
                'title': (
                    "c't uplink: Owncloud, Tastaturen, Peilsender Smartphone"
                ),
                'format_id': 'mp4_720p',
                'timestamp': 1411811400,
                'upload_date': '20140927',
                'description': 'In uplink-Episode 3.3 sprechen wir über Owncloud und wie man sich damit von Cloudanbietern emanzipieren kann. Außerdem erklären wir, woran man alles beim Kauf einer Tastatur denken sollte und was Smartphones nun über uns verraten.',
                'thumbnail': r're:^https?://.*/gallery/$',
            }
        },
        {
            'url': (
                'http://www.heise.de/ct/ausgabe/2016-12-Spiele-3214137.html'
            ),
            'md5': '0616c9297d9c989f9b2a23b483b408c3',
            'info_dict': {
                'id': '3214137',
                'ext': 'mp4',
                'title': (
                    "c\u2019t zockt \u201eGlitchspace\u201c, \u201eThe Mind's Eclipse\u201c und \u201eWindowframe\u201c."
                ),
                'format_id': 'mp4_720p',
                'timestamp': 1464011220,
                'upload_date': '20160523',
                'description': "Unsere Spiele-Tipps der Woche: Das Puzzle-Adventure Glitchspace, das Jump&Run-Spiel Windowframe und The Mind's Eclipse",
                'thumbnail': r're:^https?://.*/gallery/$',
            }
        },

    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        container_id = self._search_regex(
            r'<div class="videoplayerjw"[^>]*data-container="([0-9]+)"',
            webpage, 'container ID')
        sequenz_id = self._search_regex(
            r'<div class="videoplayerjw"[^>]*data-sequenz="([0-9]+)"',
            webpage, 'sequenz ID')
        data_url = 'http://www.heise.de/videout/feed?container=%s&sequenz=%s' % (container_id, sequenz_id)
        doc = self._download_xml(data_url, video_id)

        info = {
            'id': video_id,
            'thumbnail': doc.find('.//{http://rss.jwpcdn.com/}image').text,
            'timestamp': parse_iso8601(
                self._html_search_meta('date', webpage))
        }

        title = self._html_search_meta('fulltitle', webpage, default=None)
        if not title or title == "c't":
            title = self._search_regex(
                r'<div class="videoplayerjw"[^>]*data-title="([^"]+)"',
                webpage, 'video title')
        info['title'] = title

        desc = self._og_search_description(webpage, default=None)
        if not desc:
            desc = self._html_search_meta('description', webpage)
        info['description'] = desc

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
