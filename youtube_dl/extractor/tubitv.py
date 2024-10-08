# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_id,
    int_or_none,
    js_to_json,
    merge_dicts,
    parse_age_limit,
    sanitized_Request,
    strip_or_none,
    T,
    traverse_obj,
    url_or_none,
    urlencode_postdata,
)


class TubiTvIE(InfoExtractor):
    IE_NAME = 'tubitv'
    _VALID_URL = r'https?://(?:www\.)?tubitv\.com/(?P<type>video|movies|tv-shows)/(?P<id>\d+)'
    _LOGIN_URL = 'http://tubitv.com/login'
    _NETRC_MACHINE = 'tubitv'
    _TESTS = [{
        'url': 'https://tubitv.com/movies/100004539/the-39-steps',
        'info_dict': {
            'id': '100004539',
            'ext': 'mp4',
            'title': 'The 39 Steps',
            'description': 'md5:bb2f2dd337f0dc58c06cb509943f54c8',
            'uploader_id': 'abc2558d54505d4f0f32be94f2e7108c',
            'release_year': 1935,
            'thumbnail': r're:^https?://.+\.(jpe?g|png)$',
            'duration': 5187,
        },
        'params': {'skip_download': 'm3u8'},
        'skip': 'This content is currently unavailable',
    }, {
        'url': 'https://tubitv.com/tv-shows/554628/s01-e01-rise-of-the-snakes',
        'info_dict': {
            'id': '554628',
            'ext': 'mp4',
            'title': 'S01:E01 - Rise of the Snakes',
            'description': 'md5:ba136f586de53af0372811e783a3f57d',
            'episode': 'Rise of the Snakes',
            'episode_number': 1,
            'season': 'Season 1',
            'season_number': 1,
            'uploader_id': '2a9273e728c510d22aa5c57d0646810b',
            'release_year': 2011,
            'thumbnail': r're:^https?://.+\.(jpe?g|png)$',
            'duration': 1376,
        },
        'params': {'skip_download': 'm3u8'},
        'skip': 'This content is currently unavailable',
    }, {
        'url': 'http://tubitv.com/video/283829/the_comedian_at_the_friday',
        'md5': '43ac06be9326f41912dc64ccf7a80320',
        'info_dict': {
            'id': '283829',
            'ext': 'mp4',
            'title': 'The Comedian at The Friday',
            'description': 'A stand up comedian is forced to look at the decisions in his life while on a one week trip to the west coast.',
            'uploader_id': 'bc168bee0d18dd1cb3b86c68706ab434',
        },
        'skip': 'Content Unavailable',
    }, {
        'url': 'http://tubitv.com/tv-shows/321886/s01_e01_on_nom_stories',
        'only_matching': True,
    }, {
        'url': 'http://tubitv.com/movies/383676/tracker',
        'only_matching': True,
    }, {
        'url': 'https://tubitv.com/tv-shows/200141623/s01-e01-episode-1',
        'info_dict': {
            'id': '200141623',
            'ext': 'mp4',
            'title': 'Shameless S01:E01 - Episode 1',
            'description': 'Having her handbag stolen proves to be a blessing in disguise for Fiona when handsome stranger Steve comes to her rescue.',
            'timestamp': 1725148800,
            'upload_date': '20240901',
            'uploader': 'all3-media',
            'uploader_id': '9b8e3a8d789b1c843f4b680c025a1853',
            'release_year': 2004,
            'episode': 'Episode 1',
            'episode_number': 1,
            'season': 'Season 1',
            'season_number': 1,
            'series': 'Shameless',
            'cast': list,
            'age_limit': 17,
        },
        'params': {
            'format': 'best/bestvideo',
            'skip_download': 'm3u8'
        },
    }]

    # DRM formats are included only to raise appropriate error
    _UNPLAYABLE_FORMATS = ('hlsv6_widevine', 'hlsv6_widevine_nonclearlead', 'hlsv6_playready_psshv0',
                           'hlsv6_fairplay', 'dash_widevine', 'dash_widevine_nonclearlead')

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return
        self._perform_login(username, password)

    def _perform_login(self, username, password):
        self.report_login()
        form_data = {
            'username': username,
            'password': password,
        }
        payload = urlencode_postdata(form_data)
        request = sanitized_Request(self._LOGIN_URL, payload)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        login_page = self._download_webpage(
            request, None, False, 'Wrong login info')
        if get_element_by_id('tubi-logout', login_page) is None:
            raise ExtractorError(
                'Login failed (invalid username/password)', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        video_id, video_type = self._match_valid_url(url).group('id', 'type')
        webpage = self._download_webpage('https://tubitv.com/{0}/{1}/'.format(video_type, video_id), video_id)
        data = self._search_json(
            r'window\.__data\s*=', webpage, 'data', video_id,
            transform_source=js_to_json)['video']['byId']
        video_data = data[video_id]
        info = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        title = strip_or_none(info.get('title'))
        info['title'] = title or strip_or_none(video_data['title'])

        formats = []
        drm_formats = 0

        for resource in traverse_obj(video_data, ('video_resources', lambda _, v: v['type'] and v['manifest']['url'])):
            manifest_url = url_or_none(resource['manifest']['url'])
            if not manifest_url:
                continue
            resource_type = resource['type']
            if resource_type == 'dash':
                formats.extend(self._extract_mpd_formats(manifest_url, video_id, mpd_id=resource_type, fatal=False))
            elif resource_type in ('hlsv3', 'hlsv6'):
                formats.extend(self._extract_m3u8_formats(manifest_url, video_id, 'mp4', m3u8_id=resource_type, fatal=False))
            elif resource_type in self._UNPLAYABLE_FORMATS:
                drm_formats += 1
            else:
                self.report_warning('Skipping unknown resource type "{0}"'.format(resource_type))

        if not formats and drm_formats > 0:
            self.report_drm(video_id)
        elif not formats and not video_data.get('policy_match'):  # policy_match is False if content was removed
            raise ExtractorError('This content is currently unavailable', expected=True)
        self._sort_formats(formats)

        subtitles = {}
        for sub in traverse_obj(video_data, ('subtitles', lambda _, v: v['url'])):
            sub_url = self._proto_relative_url(sub['url'])
            if not sub_url:
                continue
            subtitles.setdefault(sub.get('lang', 'English'), []).append({
                'url': sub_url,
            })

        season_number, episode_number, episode_title = self._search_regex(
            r'\bS(\d+):E(\d+) - (.+)', info['title'], 'episode info', fatal=False, group=(1, 2, 3), default=(None, None, None))

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'season_number': int_or_none(season_number),
            'episode_number': int_or_none(episode_number),
            'episode': episode_title
        }, traverse_obj(video_data, {
            'description': ('description', T(strip_or_none)),
            'duration': ('duration', T(int_or_none)),
            'uploader': ('import_id', T(strip_or_none)),
            'uploader_id': ('publisher_id', T(strip_or_none)),
            'release_year': ('year', T(int_or_none)),
            'thumbnails': ('thumbnails', Ellipsis, T(self._proto_relative_url), {'url': T(url_or_none)}),
            'cast': ('actors', Ellipsis, T(strip_or_none)),
            'categories': ('tags', Ellipsis, T(strip_or_none)),
            'age_limit': ('ratings', 0, 'value', T(parse_age_limit)),
        }), traverse_obj(data, (lambda _, v: v['type'] == 's', {
            'series': ('title', T(strip_or_none)),
            # 'series_id': ('id', T(compat_str)),
        }), get_all=False), info)
