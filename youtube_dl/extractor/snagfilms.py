from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    int_or_none,
    js_to_json,
    parse_duration,
)


class SnagFilmsEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|embed)\.)?snagfilms\.com/embed/player\?.*\bfilmId=(?P<id>[\da-f-]{36})'
    _TESTS = [{
        'url': 'http://embed.snagfilms.com/embed/player?filmId=74849a00-85a9-11e1-9660-123139220831&w=500',
        'md5': '2924e9215c6eff7a55ed35b72276bd93',
        'info_dict': {
            'id': '74849a00-85a9-11e1-9660-123139220831',
            'ext': 'mp4',
            'title': '#whilewewatch',
        }
    }, {
        'url': 'http://www.snagfilms.com/embed/player?filmId=0000014c-de2f-d5d6-abcf-ffef58af0017',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = []
        for source in self._parse_json(js_to_json(self._search_regex(
                r'(?s)sources:\s*(\[.+?\]),', webpage, 'json')), video_id):
            file_ = source.get('file')
            if not file_:
                continue
            type_ = source.get('type')
            format_id = source.get('label')
            ext = determine_ext(file_)
            if any(_ == 'm3u8' for _ in (type_, ext)):
                formats.extend(self._extract_m3u8_formats(
                    file_, video_id, 'mp4', m3u8_id='hls'))
            else:
                bitrate = int_or_none(self._search_regex(
                    r'(\d+)kbps', file_, 'bitrate', default=None))
                height = int_or_none(self._search_regex(
                    r'^(\d+)[pP]$', format_id, 'height', default=None))
                formats.append({
                    'url': file_,
                    'format_id': format_id,
                    'tbr': bitrate,
                    'height': height,
                })
        self._sort_formats(formats)

        title = self._search_regex(
            [r"title\s*:\s*'([^']+)'", r'<title>([^<]+)</title>'],
            webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class SnagFilmsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?snagfilms\.com/films/title/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.snagfilms.com/films/title/lost_for_life',
        'md5': '19844f897b35af219773fd63bdec2942',
        'info_dict': {
            'id': '0000014c-de2f-d5d6-abcf-ffef58af0017',
            'display_id': 'lost_for_life',
            'ext': 'mp4',
            'title': 'Lost for Life',
            'description': 'md5:fbdacc8bb6b455e464aaf98bc02e1c82',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 4489,
            'categories': ['Documentary', 'Crime', 'Award Winning', 'Festivals']
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        film_id = self._search_regex(r'filmId=([\da-f-]{36})"', webpage, 'film id')

        snag = self._parse_json(
            self._search_regex(
                'Snag\.page\.data\s*=\s*(\[.+?\]);', webpage, 'snag'),
            display_id)

        for item in snag:
            if item.get('data', {}).get('film', {}).get('id') == film_id:
                data = item['data']['film']
                title = data['title']
                description = clean_html(data.get('synopsis'))
                thumbnail = data.get('image')
                duration = int_or_none(data.get('duration') or data.get('runtime'))
                categories = [
                    category['title'] for category in data.get('categories', [])
                    if category.get('title')]
                break
        else:
            title = self._search_regex(
                r'itemprop="title">([^<]+)<', webpage, 'title')
            description = self._html_search_regex(
                r'(?s)<div itemprop="description" class="film-synopsis-inner ">(.+?)</div>',
                webpage, 'description', default=None) or self._og_search_description(webpage)
            thumbnail = self._og_search_thumbnail(webpage)
            duration = parse_duration(self._search_regex(
                r'<span itemprop="duration" class="film-duration strong">([^<]+)<',
                webpage, 'duration', fatal=False))
            categories = re.findall(r'<a href="/movies/[^"]+">([^<]+)</a>', webpage)

        return {
            '_type': 'url_transparent',
            'url': 'http://embed.snagfilms.com/embed/player?filmId=%s' % film_id,
            'id': film_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'categories': categories,
        }
