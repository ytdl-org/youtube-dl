from __future__ import unicode_literals

import time
import hmac
import hashlib
import itertools

from ..utils import (
    ExtractorError,
    int_or_none,
    parse_age_limit,
    parse_iso8601,
)
from .common import InfoExtractor


class VikiBaseIE(InfoExtractor):
    _VALID_URL_BASE = r'https?://(?:www\.)?viki\.(?:com|net|mx|jp|fr)/'
    _API_QUERY_TEMPLATE = '/v4/%sapp=%s&t=%s&site=www.viki.com'
    _API_URL_TEMPLATE = 'http://api.viki.io%s&sig=%s'

    _APP = '65535a'
    _APP_VERSION = '2.2.5.1428709186'
    _APP_SECRET = '-$iJ}@p7!G@SyU/je1bEyWg}upLu-6V6-Lg9VD(]siH,r.,m-r|ulZ,U4LC/SeR)'

    def _prepare_call(self, path, timestamp=None):
        path += '?' if '?' not in path else '&'
        if not timestamp:
            timestamp = int(time.time())
        query = self._API_QUERY_TEMPLATE % (path, self._APP, timestamp)
        sig = hmac.new(
            self._APP_SECRET.encode('ascii'),
            query.encode('ascii'),
            hashlib.sha1
        ).hexdigest()
        return self._API_URL_TEMPLATE % (query, sig)

    def _call_api(self, path, video_id, note, timestamp=None):
        resp = self._download_json(
            self._prepare_call(path, timestamp), video_id, note)

        error = resp.get('error')
        if error:
            if error == 'invalid timestamp':
                resp = self._download_json(
                    self._prepare_call(path, int(resp['current_timestamp'])),
                    video_id, '%s (retry)' % note)
                error = resp.get('error')
            if error:
                self._raise_error(resp['error'])

        return resp

    def _raise_error(self, error):
        raise ExtractorError(
            '%s returned error: %s' % (self.IE_NAME, error),
            expected=True)


class VikiIE(VikiBaseIE):
    IE_NAME = 'viki'
    _VALID_URL = r'%s(?:videos|player)/(?P<id>[0-9]+v)' % VikiBaseIE._VALID_URL_BASE
    _TESTS = [{
        'url': 'http://www.viki.com/videos/1023585v-heirs-episode-14',
        'info_dict': {
            'id': '1023585v',
            'ext': 'mp4',
            'title': 'Heirs Episode 14',
            'uploader': 'SBS',
            'description': 'md5:c4b17b9626dd4b143dcc4d855ba3474e',
            'upload_date': '20131121',
            'age_limit': 13,
        },
        'skip': 'Blocked in the US',
    }, {
        # clip
        'url': 'http://www.viki.com/videos/1067139v-the-avengers-age-of-ultron-press-conference',
        'md5': '86c0b5dbd4d83a6611a79987cc7a1989',
        'info_dict': {
            'id': '1067139v',
            'ext': 'mp4',
            'title': "'The Avengers: Age of Ultron' Press Conference",
            'description': 'md5:d70b2f9428f5488321bfe1db10d612ea',
            'duration': 352,
            'timestamp': 1430380829,
            'upload_date': '20150430',
            'uploader': 'Arirang TV',
            'like_count': int,
            'age_limit': 0,
        }
    }, {
        'url': 'http://www.viki.com/videos/1048879v-ankhon-dekhi',
        'info_dict': {
            'id': '1048879v',
            'ext': 'mp4',
            'title': 'Ankhon Dekhi',
            'duration': 6512,
            'timestamp': 1408532356,
            'upload_date': '20140820',
            'uploader': 'Spuul',
            'like_count': int,
            'age_limit': 13,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        # episode
        'url': 'http://www.viki.com/videos/44699v-boys-over-flowers-episode-1',
        'md5': '190f3ef426005ba3a080a63325955bc3',
        'info_dict': {
            'id': '44699v',
            'ext': 'mp4',
            'title': 'Boys Over Flowers - Episode 1',
            'description': 'md5:52617e4f729c7d03bfd4bcbbb6e946f2',
            'duration': 4155,
            'timestamp': 1270496524,
            'upload_date': '20100405',
            'uploader': 'group8',
            'like_count': int,
            'age_limit': 13,
        }
    }, {
        # youtube external
        'url': 'http://www.viki.com/videos/50562v-poor-nastya-complete-episode-1',
        'md5': '216d1afdc0c64d1febc1e9f2bd4b864b',
        'info_dict': {
            'id': '50562v',
            'ext': 'mp4',
            'title': 'Poor Nastya [COMPLETE] - Episode 1',
            'description': '',
            'duration': 607,
            'timestamp': 1274949505,
            'upload_date': '20101213',
            'uploader': 'ad14065n',
            'uploader_id': 'ad14065n',
            'like_count': int,
            'age_limit': 13,
        }
    }, {
        'url': 'http://www.viki.com/player/44699v',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._call_api(
            'videos/%s.json' % video_id, video_id, 'Downloading video JSON')

        title = None
        titles = video.get('titles')
        if titles:
            title = titles.get('en') or titles[titles.keys()[0]]
        if not title:
            title = 'Episode %d' % video.get('number') if video.get('type') == 'episode' else video.get('id') or video_id
            container_titles = video.get('container', {}).get('titles')
            if container_titles:
                container_title = container_titles.get('en') or container_titles[container_titles.keys()[0]]
                title = '%s - %s' % (container_title, title)

        descriptions = video.get('descriptions')
        description = descriptions.get('en') or descriptions[titles.keys()[0]] if descriptions else None

        duration = int_or_none(video.get('duration'))
        timestamp = parse_iso8601(video.get('created_at'))
        uploader = video.get('author')
        like_count = int_or_none(video.get('likes', {}).get('count'))
        age_limit = parse_age_limit(video.get('rating'))

        thumbnails = []
        for thumbnail_id, thumbnail in video.get('images', {}).items():
            thumbnails.append({
                'id': thumbnail_id,
                'url': thumbnail.get('url'),
            })

        subtitles = {}
        for subtitle_lang, _ in video.get('subtitle_completions', {}).items():
            subtitles[subtitle_lang] = [{
                'ext': subtitles_format,
                'url': self._prepare_call(
                    'videos/%s/subtitles/%s.%s' % (video_id, subtitle_lang, subtitles_format)),
            } for subtitles_format in ('srt', 'vtt')]

        result = {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'uploader': uploader,
            'like_count': like_count,
            'age_limit': age_limit,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
        }

        streams = self._call_api(
            'videos/%s/streams.json' % video_id, video_id,
            'Downloading video streams JSON')

        if 'external' in streams:
            result.update({
                '_type': 'url_transparent',
                'url': streams['external']['url'],
            })
            return result

        formats = []
        for format_id, stream_dict in streams.items():
            height = self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)
            for protocol, format_dict in stream_dict.items():
                if format_id == 'm3u8':
                    formats = self._extract_m3u8_formats(
                        format_dict['url'], video_id, 'mp4', m3u8_id='m3u8-%s' % protocol)
                else:
                    formats.append({
                        'url': format_dict['url'],
                        'format_id': '%s-%s' % (format_id, protocol),
                        'height': height,
                    })
        self._sort_formats(formats)

        result['formats'] = formats
        return result


class VikiChannelIE(VikiBaseIE):
    IE_NAME = 'viki:channel'
    _VALID_URL = r'%s(?:tv|news|movies|artists)/(?P<id>[0-9]+c)' % VikiBaseIE._VALID_URL_BASE
    _TESTS = [{
        'url': 'http://www.viki.com/tv/50c-boys-over-flowers',
        'info_dict': {
            'id': '50c',
            'title': 'Boys Over Flowers',
            'description': 'md5:ecd3cff47967fe193cff37c0bec52790',
        },
        'playlist_count': 70,
    }, {
        'url': 'http://www.viki.com/tv/1354c-poor-nastya-complete',
        'info_dict': {
            'id': '1354c',
            'title': 'Poor Nastya [COMPLETE]',
            'description': 'md5:05bf5471385aa8b21c18ad450e350525',
        },
        'playlist_count': 127,
    }, {
        'url': 'http://www.viki.com/news/24569c-showbiz-korea',
        'only_matching': True,
    }, {
        'url': 'http://www.viki.com/movies/22047c-pride-and-prejudice-2005',
        'only_matching': True,
    }, {
        'url': 'http://www.viki.com/artists/2141c-shinee',
        'only_matching': True,
    }]

    _PER_PAGE = 25

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        channel = self._call_api(
            'containers/%s.json' % channel_id, channel_id,
            'Downloading channel JSON')

        titles = channel['titles']
        title = titles.get('en') or titles[titles.keys()[0]]

        descriptions = channel['descriptions']
        description = descriptions.get('en') or descriptions[descriptions.keys()[0]]

        entries = []
        for video_type in ('episodes', 'clips', 'movies'):
            for page_num in itertools.count(1):
                page = self._call_api(
                    'containers/%s/%s.json?per_page=%d&sort=number&direction=asc&with_paging=true&page=%d'
                    % (channel_id, video_type, self._PER_PAGE, page_num), channel_id,
                    'Downloading %s JSON page #%d' % (video_type, page_num))
                for video in page['response']:
                    video_id = video['id']
                    entries.append(self.url_result(
                        'http://www.viki.com/videos/%s' % video_id, 'Viki'))
                if not page['pagination']['next']:
                    break

        return self.playlist_result(entries, channel_id, title, description)
