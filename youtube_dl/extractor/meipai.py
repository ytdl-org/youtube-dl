# coding: utf-8
from __future__ import unicode_literals

from ..utils import parse_iso8601
from .common import InfoExtractor


class MeipaiIE(InfoExtractor):
    IE_DESC = '美拍'
    _VALID_URL = r'https?://(?:www\.)?meipai.com/media/(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.meipai.com/media/531697625',
            'md5': 'e3e9600f9e55a302daecc90825854b4f',
            'info_dict': {
                'id': '531697625',
                'ext': 'mp4',
                'title': '#葉子##阿桑##余姿昀##超級女聲#',
                'description': '#葉子##阿桑##余姿昀##超級女聲#',
                'thumbnail': 're:^https?://.*\.jpg$',
                'creator': '她她-TATA',
                'tags': ['葉子', '阿桑', '余姿昀', '超級女聲'],
                'release_date': 1465492420,
            }
        },
        {
            'url': 'http://www.meipai.com/media/576409659',
            'md5': '2e807c16ebe67b8b6b3c8dcacbc32f48',
            'info_dict': {
                'id': '576409659',
                'ext': 'mp4',
                'title': '#失語者##蔡健雅##吉他彈唱#',
                'description': '#失語者##蔡健雅##吉他彈唱#',
                'thumbnail': 're:^https?://.*\.jpg$',
                'creator': '她她-TATA',
                'tags': ['失語者', '蔡健雅', '吉他彈唱'],
                'release_date': 1472534847,
            }
        },
        # record of live streaming
        {
            'url': 'http://www.meipai.com/media/585526361',
            'md5': 'ff7d6afdbc6143342408223d4f5fb99a',
            'info_dict': {
                'id': '585526361',
                'ext': 'mp4',
                'title': '姿昀和善願 練歌練琴啦😁😁😁',
                'description': '姿昀和善願 練歌練琴啦😁😁😁',
                'thumbnail': 're:^https?://.*\.jpg$',
                'creator': '她她-TATA',
                'release_date': 1474311799,
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=None)
        if title is None:
            # fall back to text used in title
            title = self._html_search_regex(
                r'<title[^>]*>(.+)</title>', webpage, 'title')

        release_date = self._og_search_property(
            'video:release_date', webpage, 'release date', fatal=False)
        release_date = parse_iso8601(release_date)

        tags = self._og_search_property(
            'video:tag', webpage, 'tags', default='').split(',')

        info = {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'release_date': release_date,
            'creator': self._og_search_property(
                'video:director', webpage, 'creator', fatal=False),
            'tags': tags,
        }

        keywords = self._html_search_meta(
            'keywords', webpage, 'keywords', default=[])

        if '直播回放' in keywords:
            # recorded playback of live streaming
            m3u8_url = self._html_search_regex(
                r'file:\s*encodeURIComponent\(["\'](.+)["\']\)',
                webpage,
                'm3u8_url')
            info['formats'] = self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native')
        else:
            # regular uploaded video
            info['url'] = self._og_search_video_url(webpage)

        return info
