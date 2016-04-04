from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    smuggle_url,
    url_basename,
    update_url_query,
)


class NationalGeographicIE(InfoExtractor):
    IE_NAME = 'natgeo'
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


class NationalGeographicChannelIE(InfoExtractor):
    IE_NAME = 'natgeo:channel'
    _VALID_URL = r'https?://channel\.nationalgeographic\.com/(?:wild/)?[^/]+/videos/(?P<id>[^/?]+)'

    _TESTS = [
        {
            'url': 'http://channel.nationalgeographic.com/the-story-of-god-with-morgan-freeman/videos/uncovering-a-universal-knowledge/',
            'md5': '518c9aa655686cf81493af5cc21e2a04',
            'info_dict': {
                'id': 'nB5vIAfmyllm',
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
                'id': '3TmMv9OvGwIR',
                'ext': 'mp4',
                'title': 'The Stunning Red Bird of Paradise',
                'description': 'md5:7bc8cd1da29686be4d17ad1230f0140c',
                'timestamp': 1459362152,
                'upload_date': '20160330',
                'uploader': 'NEWA-FNG-NGTV',
            },
            'add_ie': ['ThePlatform'],
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        release_url = self._search_regex(
            r'video_auth_playlist_url\s*=\s*"([^"]+)"',
            webpage, 'release url')

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                update_url_query(release_url, {'mbr': 'true', 'switch': 'http'}),
                {'force_smil_url': True}),
            'display_id': display_id,
        }
