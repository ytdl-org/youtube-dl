# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    xpath_text,
)

import re


class HeiseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?heise\.de/(?:[^/]+/)+[^/]+-(?P<id>[0-9]+)\.html'# noqa
    _TESTS = [{
        'url': 'http://www.heise.de/video/artikel/Podcast-c-t-uplink-3-3-Owncloud-Tastaturen-Peilsender-Smartphone-2404147.html',# noqa
        'md5': 'ffed432483e922e88545ad9f2f15d30e',
        'info_dict': {
            'id': '2404147',
            'ext': 'mp4',
            'title': "Podcast: c't uplink 3.3 – Owncloud / Tastaturen / Peilsender Smartphone",# noqa
            'format_id': 'mp4_720p',
            'timestamp': 1411812600,
            'upload_date': '20140927',
            'description': 'md5:c934cbfb326c669c2bcabcbe3d3fcd20',
            'thumbnail': r're:^https?://.*/gallery/$',
        }
    }, {
        'url': 'https://www.heise.de/ct/artikel/c-t-uplink-18-5-Android-Oreo-Nokia-Galaxy-Note-8-AMD-Ryzen-Threadripper-3812972.html',# noqa
        'info_dict': {
            'id': '3812972',
            'ext': 'mp4',
            'title': "c't uplink 18.5: Android Oreo, Nokia, Galaxy Note 8, AMD Ryzen Threadripper",# noqa
            'description': 'md5:0601ade34ae5c4f5058d378327928348'
            }
    }, {
        'url': 'http://www.heise.de/ct/artikel/c-t-uplink-3-3-Owncloud-Tastaturen-Peilsender-Smartphone-2403911.html',# noqa
        'only_matching': True,
    }, {
        'url': 'http://www.heise.de/newsticker/meldung/c-t-uplink-Owncloud-Tastaturen-Peilsender-Smartphone-2404251.html?wt_mc=rss.ho.beitrag.atom',# noqa
        'only_matching': True,
    }, {
        'url': 'http://www.heise.de/ct/ausgabe/2016-12-Spiele-3214137.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('fulltitle', webpage, default=None)
        if not title or title == "c't":
            title = self._search_regex(
                    r'<div[^>]+class="videoplayerjw"[^>]+data-title="([^"]+)"',
                    webpage, 'title')

        # Find embedded youtube videos
        yt_videos = re.findall(
            r'<iframe class="yt_video" width="[0-9]+" height="[0-9]+" src="//(.+?)"', # noqa
            webpage)
        if yt_videos:
            return self.playlist_from_matches(yt_videos, title, 'Youtube')

        container_id = self._search_regex(
            r'<div class="videoplayerjw"[^>]+data-container="([0-9]+)"',
            webpage, 'container ID')

        sequenz_id = self._search_regex(
            r'<div class="videoplayerjw"[^>]+data-sequenz="([0-9]+)"',
            webpage, 'sequenz ID')

        try:
            doc = self._download_xml(
                'http://www.heise.de/videout/feed', video_id,
                query={
                    'container': container_id,
                    'sequenz': sequenz_id,
                })
        except Exception as e:
            if e.cause.code == 404:
                if title.rfind('c\'t') != -1:
                    return self.ctUplinkRss(title, video_id)
            else:
                raise e

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
            'thumbnail': (xpath_text(doc, './/{http://rss.jwpcdn.com/}image') or # noqa
                self._og_search_thumbnail(webpage)), # noqa
            'timestamp': parse_iso8601(
                self._html_search_meta('date', webpage)),
            'formats': formats
        }

    def ctUplinkRss(self, title, video_id):
        formats = []

        # e.g. "18.5" from "c't uplink 18.5:"
        episode_str = re.findall(r'[0-9]{1,2}.[0-9]{1,2}', title)

        # are there other feeds?
        sd_rss_feed = self._download_xml(
                'https://blog.ct.de/ctuplink/ctuplinkvideo.rss',
                video_id, "Downloading alternative XML (SD)")
        hd_rss_feed = self._download_xml(
                'https://blog.ct.de/ctuplink/ctuplinkvideohd.rss',
                video_id, "Downloading alternative XML (HD)")

        # should be same for both sd/hd
        titles = hd_rss_feed.findall('./channel/item/title')
        descriptions = hd_rss_feed.findall('./channel/item/description')

        sd_video_urls = sd_rss_feed.findall('./channel/item/guid')
        hd_video_urls = hd_rss_feed.findall('./channel/item/guid')

        # try to find the real matching title. it might be misformatted or so.
        # thereby only rely on the episode_str, e.g. "18.5"
        episode_index = -1
        for index, item in enumerate(titles):
            if titles[index].text.rfind(episode_str[0]) != -1:
                episode_index = index
                break

        # in case something went wrong
        if episode_index == -1:
            return

        formats.append({
            'url': sd_video_urls[episode_index].text,
            'height': 360})

        formats.append({
            'url': hd_video_urls[episode_index].text,
            'height': 720})

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': descriptions[episode_index].text,
            'formats': formats
        }
