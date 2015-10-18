# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urllib_request,
    compat_urllib_parse,
    compat_urllib_parse_unquote,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_iso8601,
    HEADRequest,
)


class ViewsterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?viewster\.com/(?:serie|movie)/(?P<id>\d+-\d+-\d+)'
    _TESTS = [{
        # movie, Type=Movie
        'url': 'http://www.viewster.com/movie/1140-11855-000/the-listening-project/',
        'md5': 'e642d1b27fcf3a4ffa79f194f5adde36',
        'info_dict': {
            'id': '1140-11855-000',
            'ext': 'mp4',
            'title': 'The listening Project',
            'description': 'md5:bac720244afd1a8ea279864e67baa071',
            'timestamp': 1214870400,
            'upload_date': '20080701',
            'duration': 4680,
        },
    }, {
        # series episode, Type=Episode
        'url': 'http://www.viewster.com/serie/1284-19427-001/the-world-and-a-wall/',
        'md5': '9243079a8531809efe1b089db102c069',
        'info_dict': {
            'id': '1284-19427-001',
            'ext': 'mp4',
            'title': 'The World and a Wall',
            'description': 'md5:24814cf74d3453fdf5bfef9716d073e3',
            'timestamp': 1428192000,
            'upload_date': '20150405',
            'duration': 1500,
        },
    }, {
        # serie, Type=Serie
        'url': 'http://www.viewster.com/serie/1303-19426-000/',
        'info_dict': {
            'id': '1303-19426-000',
            'title': 'Is It Wrong to Try to Pick up Girls in a Dungeon?',
            'description': 'md5:eeda9bef25b0d524b3a29a97804c2f11',
        },
        'playlist_count': 13,
    }, {
        # unfinished serie, no Type
        'url': 'http://www.viewster.com/serie/1284-19427-000/baby-steps-season-2/',
        'info_dict': {
            'id': '1284-19427-000',
            'title': 'Baby Steps—Season 2',
            'description': 'md5:e7097a8fc97151e25f085c9eb7a1cdb1',
        },
        'playlist_mincount': 16,
    }, {
        # geo restricted series
        'url': 'https://www.viewster.com/serie/1280-18794-002/',
        'only_matching': True,
    }, {
        # geo restricted video
        'url': 'https://www.viewster.com/serie/1280-18794-002/what-is-extraterritoriality-lawo/',
        'only_matching': True,
    }]

    _ACCEPT_HEADER = 'application/json, text/javascript, */*; q=0.01'

    def _download_json(self, url, video_id, note='Downloading JSON metadata', fatal=True):
        request = compat_urllib_request.Request(url)
        request.add_header('Accept', self._ACCEPT_HEADER)
        request.add_header('Auth-token', self._AUTH_TOKEN)
        return super(ViewsterIE, self)._download_json(request, video_id, note, fatal=fatal)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # Get 'api_token' cookie
        self._request_webpage(HEADRequest('http://www.viewster.com/'), video_id)
        cookies = self._get_cookies('http://www.viewster.com/')
        self._AUTH_TOKEN = compat_urllib_parse_unquote(cookies['api_token'].value)

        info = self._download_json(
            'https://public-api.viewster.com/search/%s' % video_id,
            video_id, 'Downloading entry JSON')

        entry_id = info.get('Id') or info['id']

        # unfinished serie has no Type
        if info.get('Type') in ('Serie', None):
            try:
                episodes = self._download_json(
                    'https://public-api.viewster.com/series/%s/episodes' % entry_id,
                    video_id, 'Downloading series JSON')
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                    self.raise_geo_restricted()
                else:
                    raise
            entries = [
                self.url_result(
                    'http://www.viewster.com/movie/%s' % episode['OriginId'], 'Viewster')
                for episode in episodes]
            title = (info.get('Title') or info['Synopsis']['Title']).strip()
            description = info.get('Synopsis', {}).get('Detailed')
            return self.playlist_result(entries, video_id, title, description)

        formats = []
        for media_type in ('application/f4m+xml', 'application/x-mpegURL', 'video/mp4'):
            media = self._download_json(
                'https://public-api.viewster.com/movies/%s/video?mediaType=%s'
                % (entry_id, compat_urllib_parse.quote(media_type)),
                video_id, 'Downloading %s JSON' % media_type, fatal=False)
            if not media:
                continue
            video_url = media.get('Uri')
            if not video_url:
                continue
            ext = determine_ext(video_url)
            if ext == 'f4m':
                video_url += '&' if '?' in video_url else '?'
                video_url += 'hdcore=3.2.0&plugin=flowplayer-3.2.0.1'
                formats.extend(self._extract_f4m_formats(
                    video_url, video_id, f4m_id='hds'))
            elif ext == 'm3u8':
                m3u8_formats = self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id='hls',
                    fatal=False)  # m3u8 sometimes fail
                if m3u8_formats:
                    formats.extend(m3u8_formats)
            else:
                format_id = media.get('Bitrate')
                f = {
                    'url': video_url,
                    'format_id': 'mp4-%s' % format_id,
                    'height': int_or_none(media.get('Height')),
                    'width': int_or_none(media.get('Width')),
                    'preference': 1,
                }
                if format_id and not f['height']:
                    f['height'] = int_or_none(self._search_regex(
                        r'^(\d+)[pP]$', format_id, 'height', default=None))
                formats.append(f)

        if not formats and not info.get('LanguageSets') and not info.get('VODSettings'):
            self.raise_geo_restricted()

        self._sort_formats(formats)

        synopsis = info.get('Synopsis', {})
        # Prefer title outside synopsis since it's less messy
        title = (info.get('Title') or synopsis['Title']).strip()
        description = synopsis.get('Detailed') or info.get('Synopsis', {}).get('Short')
        duration = int_or_none(info.get('Duration'))
        timestamp = parse_iso8601(info.get('ReleaseDate'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }
