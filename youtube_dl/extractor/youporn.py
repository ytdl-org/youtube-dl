from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    sanitized_Request,
    str_to_int,
    unescapeHTML,
    unified_strdate,
)
from ..aes import aes_decrypt_text


class YouPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youporn\.com/watch/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.youporn.com/watch/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        'md5': '71ec5fcfddacf80f495efa8b6a8d9a89',
        'info_dict': {
            'id': '505835',
            'display_id': 'sex-ed-is-it-safe-to-masturbate-daily',
            'ext': 'mp4',
            'title': 'Sex Ed: Is It Safe To Masturbate Daily?',
            'description': 'Love & Sex Answers: http://bit.ly/DanAndJenn -- Is It Unhealthy To Masturbate Daily?',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'Ask Dan And Jennifer',
            'upload_date': '20101221',
            'average_rating': int,
            'view_count': int,
            'comment_count': int,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
    }, {
        # Anonymous User uploader
        'url': 'http://www.youporn.com/watch/561726/big-tits-awesome-brunette-on-amazing-webcam-show/?from=related3&al=2&from_id=561726&pos=4',
        'info_dict': {
            'id': '561726',
            'display_id': 'big-tits-awesome-brunette-on-amazing-webcam-show',
            'ext': 'mp4',
            'title': 'Big Tits Awesome Brunette On amazing webcam show',
            'description': 'http://sweetlivegirls.com Big Tits Awesome Brunette On amazing webcam show.mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'Anonymous User',
            'upload_date': '20111125',
            'average_rating': int,
            'view_count': int,
            'comment_count': int,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        request = sanitized_Request(url)
        request.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(request, display_id)

        title = self._search_regex(
            [r'(?:video_titles|videoTitle)\s*[:=]\s*(["\'])(?P<title>.+?)\1',
             r'<h1[^>]+class=["\']heading\d?["\'][^>]*>([^<])<'],
            webpage, 'title', group='title')

        links = []

        sources = self._search_regex(
            r'sources\s*:\s*({.+?})', webpage, 'sources', default=None)
        if sources:
            for _, link in re.findall(r'[^:]+\s*:\s*(["\'])(http.+?)\1', sources):
                links.append(link)

        # Fallback #1
        for _, link in re.findall(
                r'(?:videoUrl|videoSrc|videoIpadUrl|html5PlayerSrc)\s*[:=]\s*(["\'])(http.+?)\1', webpage):
            links.append(link)

        # Fallback #2, this also contains extra low quality 180p format
        for _, link in re.findall(r'<a[^>]+href=(["\'])(http.+?)\1[^>]+title=["\']Download [Vv]ideo', webpage):
            links.append(link)

        # Fallback #3, encrypted links
        for _, encrypted_link in re.findall(
                r'encryptedQuality\d{3,4}URL\s*=\s*(["\'])([\da-zA-Z+/=]+)\1', webpage):
            links.append(aes_decrypt_text(encrypted_link, title, 32).decode('utf-8'))

        formats = []
        for video_url in set(unescapeHTML(link) for link in links):
            f = {
                'url': video_url,
            }
            # Video URL's path looks like this:
            #  /201012/17/505835/720p_1500k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            # We will benefit from it by extracting some metadata
            mobj = re.search(r'/(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+/', video_url)
            if mobj:
                height = int(mobj.group('height'))
                bitrate = int(mobj.group('bitrate'))
                f.update({
                    'format_id': '%dp-%dk' % (height, bitrate),
                    'height': height,
                    'tbr': bitrate,
                })
            formats.append(f)
        self._sort_formats(formats)

        description = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']video-description["\'][^>]*>(.+?)</div>',
            webpage, 'description', default=None)
        thumbnail = self._search_regex(
            r'(?:imageurl\s*=|poster\s*:)\s*(["\'])(?P<thumbnail>.+?)\1',
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        uploader = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']videoInfoBy["\'][^>]*>\s*By:\s*</div>(.+?)</(?:a|div)>',
            webpage, 'uploader', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            r'(?s)<div[^>]+class=["\']videoInfoTime["\'][^>]*>(.+?)</div>',
            webpage, 'upload date', fatal=False))

        age_limit = self._rta_search(webpage)

        average_rating = int_or_none(self._search_regex(
            r'<div[^>]+class=["\']videoInfoRating["\'][^>]*>\s*<div[^>]+class=["\']videoRatingPercentage["\'][^>]*>(\d+)%</div>',
            webpage, 'average rating', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'(?s)<div[^>]+class=["\']videoInfoViews["\'][^>]*>.*?([\d,.]+)\s*</div>',
            webpage, 'view count', fatal=False))
        comment_count = str_to_int(self._search_regex(
            r'>All [Cc]omments? \(([\d,.]+)\)',
            webpage, 'comment count', fatal=False))

        def extract_tag_box(title):
            tag_box = self._search_regex(
                (r'<div[^>]+class=["\']tagBoxTitle["\'][^>]*>\s*%s\b.*?</div>\s*'
                 '<div[^>]+class=["\']tagBoxContent["\']>(.+?)</div>') % re.escape(title),
                webpage, '%s tag box' % title, default=None)
            if not tag_box:
                return []
            return re.findall(r'<a[^>]+href=[^>]+>([^<]+)', tag_box)

        categories = extract_tag_box('Category')
        tags = extract_tag_box('Tags')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'average_rating': average_rating,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
        }
