from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    clean_html,
    dict_get,
    ExtractorError,
    int_or_none,
    parse_duration,
    unified_strdate,
)


class XHamsterIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:.+?\.)?xhamster\.com/
                        (?:
                            movies/(?P<id>\d+)/(?P<display_id>[^/]*)\.html|
                            videos/(?P<display_id_2>[^/]*)-(?P<id_2>\d+)
                        )
                    '''

    _TESTS = [{
        'url': 'http://xhamster.com/movies/1509445/femaleagent_shy_beauty_takes_the_bait.html',
        'md5': '8281348b8d3c53d39fffb377d24eac4e',
        'info_dict': {
            'id': '1509445',
            'display_id': 'femaleagent_shy_beauty_takes_the_bait',
            'ext': 'mp4',
            'title': 'FemaleAgent Shy beauty takes the bait',
            'upload_date': '20121014',
            'uploader': 'Ruseful2011',
            'duration': 893,
            'age_limit': 18,
            'categories': ['Fake Hub', 'Amateur', 'MILFs', 'POV', 'Boss', 'Office', 'Oral', 'Reality', 'Sexy'],
        },
    }, {
        'url': 'http://xhamster.com/movies/2221348/britney_spears_sexy_booty.html?hd',
        'info_dict': {
            'id': '2221348',
            'display_id': 'britney_spears_sexy_booty',
            'ext': 'mp4',
            'title': 'Britney Spears  Sexy Booty',
            'upload_date': '20130914',
            'uploader': 'jojo747400',
            'duration': 200,
            'age_limit': 18,
            'categories': ['Britney Spears', 'Celebrities', 'HD Videos', 'Sexy', 'Sexy Booty'],
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # empty seo
        'url': 'http://xhamster.com/movies/5667973/.html',
        'info_dict': {
            'id': '5667973',
            'ext': 'mp4',
            'title': '....',
            'upload_date': '20160208',
            'uploader': 'parejafree',
            'duration': 72,
            'age_limit': 18,
            'categories': ['Amateur', 'Blowjobs'],
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://xhamster.com/movies/2272726/amber_slayed_by_the_knight.html',
        'only_matching': True,
    }, {
        # This video is visible for marcoalfa123456's friends only
        'url': 'https://it.xhamster.com/movies/7263980/la_mia_vicina.html',
        'only_matching': True,
    }, {
        # new URL schema
        'url': 'https://pt.xhamster.com/videos/euro-pedal-pumping-7937821',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('id_2')
        display_id = mobj.group('display_id') or mobj.group('display_id_2')

        webpage = self._download_webpage(url, video_id)

        error = self._html_search_regex(
            r'<div[^>]+id=["\']videoClosed["\'][^>]*>(.+?)</div>',
            webpage, 'error', default=None)
        if error:
            raise ExtractorError(error, expected=True)

        title = self._html_search_regex(
            [r'<h1[^>]*>([^<]+)</h1>',
             r'<meta[^>]+itemprop=".*?caption.*?"[^>]+content="(.+?)"',
             r'<title[^>]*>(.+?)(?:,\s*[^,]*?\s*Porn\s*[^,]*?:\s*xHamster[^<]*| - xHamster\.com)</title>'],
            webpage, 'title')

        formats = []
        format_urls = set()

        sources = self._parse_json(
            self._search_regex(
                r'sources\s*:\s*({.+?})\s*,?\s*\n', webpage, 'sources',
                default='{}'),
            video_id, fatal=False)
        for format_id, format_url in sources.items():
            if not isinstance(format_url, compat_str):
                continue
            if format_url in format_urls:
                continue
            format_urls.add(format_url)
            formats.append({
                'format_id': format_id,
                'url': format_url,
                'height': int_or_none(self._search_regex(
                    r'^(\d+)[pP]', format_id, 'height', default=None))
            })

        video_url = self._search_regex(
            [r'''file\s*:\s*(?P<q>["'])(?P<mp4>.+?)(?P=q)''',
             r'''<a\s+href=(?P<q>["'])(?P<mp4>.+?)(?P=q)\s+class=["']mp4Thumb''',
             r'''<video[^>]+file=(?P<q>["'])(?P<mp4>.+?)(?P=q)[^>]*>'''],
            webpage, 'video url', group='mp4', default=None)
        if video_url and video_url not in format_urls:
            formats.append({
                'url': video_url,
            })

        self._sort_formats(formats)

        # Only a few videos have an description
        mobj = re.search(r'<span>Description: </span>([^<]+)', webpage)
        description = mobj.group(1) if mobj else None

        upload_date = unified_strdate(self._search_regex(
            r'hint=["\'](\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} [A-Z]{3,4}',
            webpage, 'upload date', fatal=False))

        uploader = self._html_search_regex(
            r'<span[^>]+itemprop=["\']author[^>]+><a[^>]+><span[^>]+>([^<]+)',
            webpage, 'uploader', default='anonymous')

        thumbnail = self._search_regex(
            [r'''thumb\s*:\s*(?P<q>["'])(?P<thumbnail>.+?)(?P=q)''',
             r'''<video[^>]+poster=(?P<q>["'])(?P<thumbnail>.+?)(?P=q)[^>]*>'''],
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        duration = parse_duration(self._search_regex(
            [r'<[^<]+\bitemprop=["\']duration["\'][^<]+\bcontent=["\'](.+?)["\']',
             r'Runtime:\s*</span>\s*([\d:]+)'], webpage,
            'duration', fatal=False))

        view_count = int_or_none(self._search_regex(
            r'content=["\']User(?:View|Play)s:(\d+)',
            webpage, 'view count', fatal=False))

        mobj = re.search(r'hint=[\'"](?P<likecount>\d+) Likes / (?P<dislikecount>\d+) Dislikes', webpage)
        (like_count, dislike_count) = (mobj.group('likecount'), mobj.group('dislikecount')) if mobj else (None, None)

        mobj = re.search(r'</label>Comments \((?P<commentcount>\d+)\)</div>', webpage)
        comment_count = mobj.group('commentcount') if mobj else 0

        age_limit = self._rta_search(webpage)

        categories_html = self._search_regex(
            r'(?s)<table.+?(<span>Categories:.+?)</table>', webpage,
            'categories', default=None)
        categories = [clean_html(category) for category in re.findall(
            r'<a[^>]+>(.+?)</a>', categories_html)] if categories_html else None

        return {
            'id': video_id,
            'display_id': display_id,
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
            'categories': categories,
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
            r'href="(https?://xhamster\.com/movies/%s/[^"]*\.html[^"]*)"' % video_id,
            webpage, 'xhamster url', default=None)

        if not video_url:
            vars = self._parse_json(
                self._search_regex(r'vars\s*:\s*({.+?})\s*,\s*\n', webpage, 'vars'),
                video_id)
            video_url = dict_get(vars, ('downloadLink', 'homepageLink', 'commentsLink', 'shareUrl'))

        return self.url_result(video_url, 'XHamster')
