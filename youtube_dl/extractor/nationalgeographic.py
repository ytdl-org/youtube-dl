from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .adobepass import AdobePassIE
from .theplatform import ThePlatformIE
from ..utils import (
    smuggle_url,
    url_basename,
    update_url_query,
    get_element_by_class,
)


class NationalGeographicVideoIE(InfoExtractor):
    IE_NAME = 'natgeo:video'
    _VALID_URL = r'https?://video\.nationalgeographic\.com/.*?'

    _TESTS = [
        {
            'url': 'http://video.nationalgeographic.com/video/news/150210-news-crab-mating-vin?source=featuredvideo',
            'md5': '730855d559abbad6b42c2be1fa584917',
            'info_dict': {
                'id': '0000014b-70a1-dd8c-af7f-f7b559330001',
                'ext': 'mp4',
                'title': 'Mating Crabs Busted by Sharks',
                'description': 'md5:16f25aeffdeba55aaa8ec37e093ad8b3',
                'timestamp': 1423523799,
                'upload_date': '20150209',
                'uploader': 'NAGS',
            },
            'add_ie': ['ThePlatform'],
        },
        {
            'url': 'http://video.nationalgeographic.com/wild/when-sharks-attack/the-real-jaws',
            'md5': '6a3105eb448c070503b3105fb9b320b5',
            'info_dict': {
                'id': 'ngc-I0IauNSWznb_UV008GxSbwY35BZvgi2e',
                'ext': 'mp4',
                'title': 'The Real Jaws',
                'description': 'md5:8d3e09d9d53a85cd397b4b21b2c77be6',
                'timestamp': 1433772632,
                'upload_date': '20150608',
                'uploader': 'NAGS',
            },
            'add_ie': ['ThePlatform'],
        },
    ]

    def _real_extract(self, url):
        name = url_basename(url)

        webpage = self._download_webpage(url, name)
        guid = self._search_regex(
            r'id="(?:videoPlayer|player-container)"[^>]+data-guid="([^"]+)"',
            webpage, 'guid')

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/ngs/media/guid/2423130747/%s?mbr=true' % guid,
                {'force_smil_url': True}),
            'id': guid,
        }


class NationalGeographicIE(ThePlatformIE, AdobePassIE):
    IE_NAME = 'natgeo'
    _VALID_URL = r'https?://channel\.nationalgeographic\.com/(?:wild/)?[^/]+/(?:videos|episodes)/(?P<id>[^/?]+)'

    _TESTS = [
        {
            'url': 'http://channel.nationalgeographic.com/the-story-of-god-with-morgan-freeman/videos/uncovering-a-universal-knowledge/',
            'md5': '518c9aa655686cf81493af5cc21e2a04',
            'info_dict': {
                'id': 'vKInpacll2pC',
                'ext': 'mp4',
                'title': 'Uncovering a Universal Knowledge',
                'description': 'md5:1a89148475bf931b3661fcd6ddb2ae3a',
                'timestamp': 1458680907,
                'upload_date': '20160322',
                'uploader': 'NEWA-FNG-NGTV',
            },
            'add_ie': ['ThePlatform'],
        },
        {
            'url': 'http://channel.nationalgeographic.com/wild/destination-wild/videos/the-stunning-red-bird-of-paradise/',
            'md5': 'c4912f656b4cbe58f3e000c489360989',
            'info_dict': {
                'id': 'Pok5lWCkiEFA',
                'ext': 'mp4',
                'title': 'The Stunning Red Bird of Paradise',
                'description': 'md5:7bc8cd1da29686be4d17ad1230f0140c',
                'timestamp': 1459362152,
                'upload_date': '20160330',
                'uploader': 'NEWA-FNG-NGTV',
            },
            'add_ie': ['ThePlatform'],
        },
        {
            'url': 'http://channel.nationalgeographic.com/the-story-of-god-with-morgan-freeman/episodes/the-power-of-miracles/',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        release_url = self._search_regex(
            r'video_auth_playlist_url\s*=\s*"([^"]+)"',
            webpage, 'release url')
        theplatform_path = self._search_regex(r'https?://link.theplatform.com/s/([^?]+)', release_url, 'theplatform path')
        video_id = theplatform_path.split('/')[-1]
        query = {
            'mbr': 'true',
        }
        is_auth = self._search_regex(r'video_is_auth\s*=\s*"([^"]+)"', webpage, 'is auth', fatal=False)
        if is_auth == 'auth':
            auth_resource_id = self._search_regex(
                r"video_auth_resourceId\s*=\s*'([^']+)'",
                webpage, 'auth resource id')
            query['auth'] = self._extract_mvpd_auth(url, video_id, 'natgeo', auth_resource_id)

        formats = []
        subtitles = {}
        for key, value in (('switch', 'http'), ('manifest', 'm3u')):
            tp_query = query.copy()
            tp_query.update({
                key: value,
            })
            tp_formats, tp_subtitles = self._extract_theplatform_smil(
                update_url_query(release_url, tp_query), video_id, 'Downloading %s SMIL data' % value)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        self._sort_formats(formats)

        info = self._extract_theplatform_metadata(theplatform_path, display_id)
        info.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'display_id': display_id,
        })
        return info


class NationalGeographicEpisodeGuideIE(InfoExtractor):
    IE_NAME = 'natgeo:episodeguide'
    _VALID_URL = r'https?://channel\.nationalgeographic\.com/(?:wild/)?(?P<id>[^/]+)/episode-guide'
    _TESTS = [
        {
            'url': 'http://channel.nationalgeographic.com/the-story-of-god-with-morgan-freeman/episode-guide/',
            'info_dict': {
                'id': 'the-story-of-god-with-morgan-freeman-season-1',
                'title': 'The Story of God with Morgan Freeman - Season 1',
            },
            'playlist_mincount': 6,
        },
        {
            'url': 'http://channel.nationalgeographic.com/underworld-inc/episode-guide/?s=2',
            'info_dict': {
                'id': 'underworld-inc-season-2',
                'title': 'Underworld, Inc. - Season 2',
            },
            'playlist_mincount': 7,
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        show = get_element_by_class('show', webpage)
        selected_season = self._search_regex(
            r'<div[^>]+class="select-seasons[^"]*".*?<a[^>]*>(.*?)</a>',
            webpage, 'selected season')
        entries = [
            self.url_result(self._proto_relative_url(entry_url), 'NationalGeographic')
            for entry_url in re.findall('(?s)<div[^>]+class="col-inner"[^>]*?>.*?<a[^>]+href="([^"]+)"', webpage)]
        return self.playlist_result(
            entries, '%s-%s' % (display_id, selected_season.lower().replace(' ', '-')),
            '%s - %s' % (show, selected_season))
