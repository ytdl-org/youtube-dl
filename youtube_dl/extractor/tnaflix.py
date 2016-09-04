from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    fix_xml_ampersands,
    float_or_none,
    int_or_none,
    parse_duration,
    str_to_int,
    unescapeHTML,
    xpath_text,
)


class TNAFlixNetworkBaseIE(InfoExtractor):
    # May be overridden in descendants if necessary
    _CONFIG_REGEX = [
        r'flashvars\.config\s*=\s*escape\("([^"]+)"',
        r'<input[^>]+name="config\d?" value="([^"]+)"',
    ]
    _TITLE_REGEX = r'<input[^>]+name="title" value="([^"]+)"'
    _DESCRIPTION_REGEX = r'<input[^>]+name="description" value="([^"]+)"'
    _UPLOADER_REGEX = r'<input[^>]+name="username" value="([^"]+)"'
    _VIEW_COUNT_REGEX = None
    _COMMENT_COUNT_REGEX = None
    _AVERAGE_RATING_REGEX = None
    _CATEGORIES_REGEX = r'<li[^>]*>\s*<span[^>]+class="infoTitle"[^>]*>Categories:</span>\s*<span[^>]+class="listView"[^>]*>(.+?)</span>\s*</li>'

    def _extract_thumbnails(self, flix_xml):

        def get_child(elem, names):
            for name in names:
                child = elem.find(name)
                if child is not None:
                    return child

        timeline = get_child(flix_xml, ['timeline', 'rolloverBarImage'])
        if timeline is None:
            return

        pattern_el = get_child(timeline, ['imagePattern', 'pattern'])
        if pattern_el is None or not pattern_el.text:
            return

        first_el = get_child(timeline, ['imageFirst', 'first'])
        last_el = get_child(timeline, ['imageLast', 'last'])
        if first_el is None or last_el is None:
            return

        first_text = first_el.text
        last_text = last_el.text
        if not first_text.isdigit() or not last_text.isdigit():
            return

        first = int(first_text)
        last = int(last_text)
        if first > last:
            return

        width = int_or_none(xpath_text(timeline, './imageWidth', 'thumbnail width'))
        height = int_or_none(xpath_text(timeline, './imageHeight', 'thumbnail height'))

        return [{
            'url': self._proto_relative_url(pattern_el.text.replace('#', compat_str(i)), 'http:'),
            'width': width,
            'height': height,
        } for i in range(first, last + 1)]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') if 'display_id' in mobj.groupdict() else video_id

        webpage = self._download_webpage(url, display_id)

        cfg_url = self._proto_relative_url(self._html_search_regex(
            self._CONFIG_REGEX, webpage, 'flashvars.config', default=None), 'http:')

        if not cfg_url:
            inputs = self._hidden_inputs(webpage)
            cfg_url = ('https://cdn-fck.tnaflix.com/tnaflix/%s.fid?key=%s&VID=%s&premium=1&vip=1&alpha'
                       % (inputs['vkey'], inputs['nkey'], video_id))

        cfg_xml = self._download_xml(
            cfg_url, display_id, 'Downloading metadata',
            transform_source=fix_xml_ampersands)

        formats = []

        def extract_video_url(vl):
            return re.sub('speed=\d+', 'speed=', unescapeHTML(vl.text))

        video_link = cfg_xml.find('./videoLink')
        if video_link is not None:
            formats.append({
                'url': extract_video_url(video_link),
                'ext': xpath_text(cfg_xml, './videoConfig/type', 'type', default='flv'),
            })

        for item in cfg_xml.findall('./quality/item'):
            video_link = item.find('./videoLink')
            if video_link is None:
                continue
            res = item.find('res')
            format_id = None if res is None else res.text
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]', format_id, 'height', default=None))
            formats.append({
                'url': self._proto_relative_url(extract_video_url(video_link), 'http:'),
                'format_id': format_id,
                'height': height,
            })

        self._sort_formats(formats)

        thumbnail = self._proto_relative_url(
            xpath_text(cfg_xml, './startThumb', 'thumbnail'), 'http:')
        thumbnails = self._extract_thumbnails(cfg_xml)

        title = None
        if self._TITLE_REGEX:
            title = self._html_search_regex(
                self._TITLE_REGEX, webpage, 'title', default=None)
        if not title:
            title = self._og_search_title(webpage)

        age_limit = self._rta_search(webpage) or 18

        duration = parse_duration(self._html_search_meta(
            'duration', webpage, 'duration', default=None))

        def extract_field(pattern, name):
            return self._html_search_regex(pattern, webpage, name, default=None) if pattern else None

        description = extract_field(self._DESCRIPTION_REGEX, 'description')
        uploader = extract_field(self._UPLOADER_REGEX, 'uploader')
        view_count = str_to_int(extract_field(self._VIEW_COUNT_REGEX, 'view count'))
        comment_count = str_to_int(extract_field(self._COMMENT_COUNT_REGEX, 'comment count'))
        average_rating = float_or_none(extract_field(self._AVERAGE_RATING_REGEX, 'average rating'))

        categories_str = extract_field(self._CATEGORIES_REGEX, 'categories')
        categories = [c.strip() for c in categories_str.split(',')] if categories_str is not None else []

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'thumbnails': thumbnails,
            'duration': duration,
            'age_limit': age_limit,
            'uploader': uploader,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'categories': categories,
            'formats': formats,
        }


class TNAFlixNetworkEmbedIE(TNAFlixNetworkBaseIE):
    _VALID_URL = r'https?://player\.(?:tna|emp)flix\.com/video/(?P<id>\d+)'

    _TITLE_REGEX = r'<title>([^<]+)</title>'

    _TESTS = [{
        'url': 'https://player.tnaflix.com/video/6538',
        'info_dict': {
            'id': '6538',
            'display_id': '6538',
            'ext': 'mp4',
            'title': 'Educational xxx video',
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://player.empflix.com/video/33051',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//player\.(?:tna|emp)flix\.com/video/\d+)\1',
            webpage)]


class TNAFlixIE(TNAFlixNetworkBaseIE):
    _VALID_URL = r'https?://(?:www\.)?tnaflix\.com/[^/]+/(?P<display_id>[^/]+)/video(?P<id>\d+)'

    _TITLE_REGEX = r'<title>(.+?) - (?:TNAFlix Porn Videos|TNAFlix\.com)</title>'
    _DESCRIPTION_REGEX = r'(?s)>Description:</[^>]+>(.+?)<'
    _UPLOADER_REGEX = r'<i>\s*Verified Member\s*</i>\s*<h\d+>(.+?)<'
    _CATEGORIES_REGEX = r'(?s)<span[^>]*>Categories:</span>(.+?)</div>'

    _TESTS = [{
        # anonymous uploader, no categories
        'url': 'http://www.tnaflix.com/porn-stars/Carmella-Decesare-striptease/video553878',
        'md5': 'ecf3498417d09216374fc5907f9c6ec0',
        'info_dict': {
            'id': '553878',
            'display_id': 'Carmella-Decesare-striptease',
            'ext': 'mp4',
            'title': 'Carmella Decesare - striptease',
            'thumbnail': 're:https?://.*\.jpg$',
            'duration': 91,
            'age_limit': 18,
            'categories': ['Porn Stars'],
        }
    }, {
        # non-anonymous uploader, categories
        'url': 'https://www.tnaflix.com/teen-porn/Educational-xxx-video/video6538',
        'md5': '0f5d4d490dbfd117b8607054248a07c0',
        'info_dict': {
            'id': '6538',
            'display_id': 'Educational-xxx-video',
            'ext': 'mp4',
            'title': 'Educational xxx video',
            'description': 'md5:b4fab8f88a8621c8fabd361a173fe5b8',
            'thumbnail': 're:https?://.*\.jpg$',
            'duration': 164,
            'age_limit': 18,
            'uploader': 'bobwhite39',
            'categories': ['Amateur Porn', 'Squirting Videos', 'Teen Girls 18+'],
        }
    }, {
        'url': 'https://www.tnaflix.com/amateur-porn/bunzHD-Ms.Donk/video358632',
        'only_matching': True,
    }]


class EMPFlixIE(TNAFlixNetworkBaseIE):
    _VALID_URL = r'https?://(?:www\.)?empflix\.com/videos/(?P<display_id>.+?)-(?P<id>[0-9]+)\.html'

    _UPLOADER_REGEX = r'<span[^>]+class="infoTitle"[^>]*>Uploaded By:</span>(.+?)</li>'

    _TESTS = [{
        'url': 'http://www.empflix.com/videos/Amateur-Finger-Fuck-33051.html',
        'md5': 'b1bc15b6412d33902d6e5952035fcabc',
        'info_dict': {
            'id': '33051',
            'display_id': 'Amateur-Finger-Fuck',
            'ext': 'mp4',
            'title': 'Amateur Finger Fuck',
            'description': 'Amateur solo finger fucking.',
            'thumbnail': 're:https?://.*\.jpg$',
            'duration': 83,
            'age_limit': 18,
            'uploader': 'cwbike',
            'categories': ['Amateur', 'Anal', 'Fisting', 'Home made', 'Solo'],
        }
    }, {
        'url': 'http://www.empflix.com/videos/[AROMA][ARMD-718]-Aoi-Yoshino-Sawa-25826.html',
        'only_matching': True,
    }]


class MovieFapIE(TNAFlixNetworkBaseIE):
    _VALID_URL = r'https?://(?:www\.)?moviefap\.com/videos/(?P<id>[0-9a-f]+)/(?P<display_id>[^/]+)\.html'

    _VIEW_COUNT_REGEX = r'<br>Views\s*<strong>([\d,.]+)</strong>'
    _COMMENT_COUNT_REGEX = r'<span[^>]+id="comCount"[^>]*>([\d,.]+)</span>'
    _AVERAGE_RATING_REGEX = r'Current Rating\s*<br>\s*<strong>([\d.]+)</strong>'
    _CATEGORIES_REGEX = r'(?s)<div[^>]+id="vid_info"[^>]*>\s*<div[^>]*>.+?</div>(.*?)<br>'

    _TESTS = [{
        # normal, multi-format video
        'url': 'http://www.moviefap.com/videos/be9867c9416c19f54a4a/experienced-milf-amazing-handjob.html',
        'md5': '26624b4e2523051b550067d547615906',
        'info_dict': {
            'id': 'be9867c9416c19f54a4a',
            'display_id': 'experienced-milf-amazing-handjob',
            'ext': 'mp4',
            'title': 'Experienced MILF Amazing Handjob',
            'description': 'Experienced MILF giving an Amazing Handjob',
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
            'uploader': 'darvinfred06',
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'categories': ['Amateur', 'Masturbation', 'Mature', 'Flashing'],
        }
    }, {
        # quirky single-format case where the extension is given as fid, but the video is really an flv
        'url': 'http://www.moviefap.com/videos/e5da0d3edce5404418f5/jeune-couple-russe.html',
        'md5': 'fa56683e291fc80635907168a743c9ad',
        'info_dict': {
            'id': 'e5da0d3edce5404418f5',
            'display_id': 'jeune-couple-russe',
            'ext': 'flv',
            'title': 'Jeune Couple Russe',
            'description': 'Amateur',
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
            'uploader': 'whiskeyjar',
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'categories': ['Amateur', 'Teen'],
        }
    }]
