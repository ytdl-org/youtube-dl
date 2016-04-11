from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    dict_get,
    float_or_none,
    int_or_none,
    unified_strdate,
)


class XHamsterIE(InfoExtractor):
    _VALID_URL = r'(?P<proto>https?)://(?:.+?\.)?xhamster\.com/movies/(?P<id>[0-9]+)/(?P<seo>.+?)\.html(?:\?.*)?'
    _TESTS = [
        {
            'url': 'http://xhamster.com/movies/1509445/femaleagent_shy_beauty_takes_the_bait.html',
            'info_dict': {
                'id': '1509445',
                'ext': 'mp4',
                'title': 'FemaleAgent Shy beauty takes the bait',
                'upload_date': '20121014',
                'uploader': 'Ruseful2011',
                'duration': 893.52,
                'age_limit': 18,
            }
        },
        {
            'url': 'http://xhamster.com/movies/2221348/britney_spears_sexy_booty.html?hd',
            'info_dict': {
                'id': '2221348',
                'ext': 'mp4',
                'title': 'Britney Spears  Sexy Booty',
                'upload_date': '20130914',
                'uploader': 'jojo747400',
                'duration': 200.48,
                'age_limit': 18,
            }
        },
        {
            'url': 'https://xhamster.com/movies/2272726/amber_slayed_by_the_knight.html',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        def extract_video_url(webpage, name):
            return self._search_regex(
                [r'''file\s*:\s*(?P<q>["'])(?P<mp4>.+?)(?P=q)''',
                 r'''<a\s+href=(?P<q>["'])(?P<mp4>.+?)(?P=q)\s+class=["']mp4Thumb''',
                 r'''<video[^>]+file=(?P<q>["'])(?P<mp4>.+?)(?P=q)[^>]*>'''],
                webpage, name, group='mp4')

        def is_hd(webpage):
            return '<div class=\'icon iconHD\'' in webpage

        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        seo = mobj.group('seo')
        proto = mobj.group('proto')
        mrss_url = '%s://xhamster.com/movies/%s/%s.html' % (proto, video_id, seo)
        webpage = self._download_webpage(mrss_url, video_id)

        title = self._html_search_regex(
            [r'<h1[^>]*>([^<]+)</h1>',
             r'<meta[^>]+itemprop=".*?caption.*?"[^>]+content="(.+?)"',
             r'<title[^>]*>(.+?)(?:,\s*[^,]*?\s*Porn\s*[^,]*?:\s*xHamster[^<]*| - xHamster\.com)</title>'],
            webpage, 'title')

        # Only a few videos have an description
        mobj = re.search(r'<span>Description: </span>([^<]+)', webpage)
        description = mobj.group(1) if mobj else None

        upload_date = unified_strdate(self._search_regex(
            r'hint=["\'](\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} [A-Z]{3,4}',
            webpage, 'upload date', fatal=False))

        uploader = self._html_search_regex(
            r'<span[^>]+itemprop=["\']author[^>]+><a[^>]+href=["\'].+?xhamster\.com/user/[^>]+>(?P<uploader>.+?)</a>',
            webpage, 'uploader', default='anonymous')

        thumbnail = self._search_regex(
            [r'''thumb\s*:\s*(?P<q>["'])(?P<thumbnail>.+?)(?P=q)''',
             r'''<video[^>]+poster=(?P<q>["'])(?P<thumbnail>.+?)(?P=q)[^>]*>'''],
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        duration = float_or_none(self._search_regex(
            r'(["\'])duration\1\s*:\s*(["\'])(?P<duration>.+?)\2',
            webpage, 'duration', fatal=False, group='duration'))

        view_count = int_or_none(self._search_regex(
            r'content=["\']User(?:View|Play)s:(\d+)',
            webpage, 'view count', fatal=False))

        mobj = re.search(r"hint='(?P<likecount>\d+) Likes / (?P<dislikecount>\d+) Dislikes'", webpage)
        (like_count, dislike_count) = (mobj.group('likecount'), mobj.group('dislikecount')) if mobj else (None, None)

        mobj = re.search(r'</label>Comments \((?P<commentcount>\d+)\)</div>', webpage)
        comment_count = mobj.group('commentcount') if mobj else 0

        age_limit = self._rta_search(webpage)

        hd = is_hd(webpage)

        format_id = 'hd' if hd else 'sd'

        video_url = extract_video_url(webpage, format_id)
        formats = [{
            'url': video_url,
            'format_id': 'hd' if hd else 'sd',
            'preference': 1,
        }]

        if not hd:
            mrss_url = self._search_regex(r'<link rel="canonical" href="([^"]+)', webpage, 'mrss_url')
            webpage = self._download_webpage(mrss_url + '?hd', video_id, note='Downloading HD webpage')
            if is_hd(webpage):
                video_url = extract_video_url(webpage, 'hd')
                formats.append({
                    'url': video_url,
                    'format_id': 'hd',
                    'preference': 2,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': int_or_none(like_count),
            'dislike_count': int_or_none(dislike_count),
            'comment_count': int_or_none(comment_count),
            'age_limit': age_limit,
            'formats': formats,
        }


class XHamsterEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xhamster\.com/xembed\.php\?video=(?P<id>\d+)'
    _TEST = {
        'url': 'http://xhamster.com/xembed.php?video=3328539',
        'info_dict': {
            'id': '3328539',
            'ext': 'mp4',
            'title': 'Pen Masturbation',
            'upload_date': '20140728',
            'uploader_id': 'anonymous',
            'duration': 5,
            'age_limit': 18,
        }
    }

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?xhamster\.com/xembed\.php\?video=\d+)\1',
            webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            r'href="(https?://xhamster\.com/movies/%s/[^"]+\.html[^"]*)"' % video_id,
            webpage, 'xhamster url', default=None)

        if not video_url:
            vars = self._parse_json(
                self._search_regex(r'vars\s*:\s*({.+?})\s*,\s*\n', webpage, 'vars'),
                video_id)
            video_url = dict_get(vars, ('downloadLink', 'homepageLink', 'commentsLink', 'shareUrl'))

        return self.url_result(video_url, 'XHamster')
