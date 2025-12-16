# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CreaCastIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://(?:\w+\.)?creacast\.com/
                        (?:
                            channel/\w+/[^/]*iid=(?P<id>\d+)|
                            play.php\?k=(?P<id>[^/?#&]+)
                        )'''
    _TESTS = [
        {
            'url': 'https://www.creacast.com/play.php?k=GHGGRuQfeaJ4g4r6cpGSe4',
            'md5': 'a524c0a6096c583345603777596b439c',
            'info_dict': {
                'id': 'GHGGRuQfeaJ4g4r6cpGSe4',
                'ext': 'mp4',
                'title': 'Strasbourg VOD'
            }
        },
        {
            'url': 'https://www.creacast.com/channel/strasbourg/?sort=v&iid=5444&display=vod',
            'md5': 'TBC',
            'info_dict': {
                'id': '5444',
                'ext': 'mp4',
                'title': 'Conseils | Strasbourg.eu'
            }
        }
    ]


    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(
            self._search_regex(
                r'(?s)runParams\s*=\s*({.+?})\s*;?\s*var',
                webpage, 'runParams'),
            video_id)

        formats = self._extract_m3u8_formats(
            data['replyStreamUrl'], video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')

        print("toto\n\n")

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            'formats': formats,
        }
