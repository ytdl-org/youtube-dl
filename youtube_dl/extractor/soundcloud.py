# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import (
    InfoExtractor,
    SearchInfoExtractor
)
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    HEADRequest,
    int_or_none,
    KNOWN_EXTENSIONS,
    mimetype2ext,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
)


class SoundcloudEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:w|player|p)\.soundcloud\.com/player/?.*?url=(?P<id>.*)'

    @staticmethod
    def _extract_urls(webpage):
        return [m.group('url') for m in re.finditer(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?://)?(?:w\.)?soundcloud\.com/player.+?)\1',
            webpage)]

    def _real_extract(self, url):
        return self.url_result(compat_urlparse.parse_qs(
            compat_urlparse.urlparse(url).query)['url'][0])


class SoundcloudIE(InfoExtractor):
    """Information extractor for soundcloud.com
       To access the media, the uid of the song and a stream token
       must be extracted from the page source and the script must make
       a request to media.soundcloud.com/crossdomain.xml. Then
       the media can be grabbed by requesting from an url composed
       of the stream token and uid
     """

    _VALID_URL = r'''(?x)^(?:https?://)?
                    (?:(?:(?:www\.|m\.)?soundcloud\.com/
                            (?!stations/track)
                            (?P<uploader>[\w\d-]+)/
                            (?!(?:tracks|albums|sets(?:/.+?)?|reposts|likes|spotlight)/?(?:$|[?#]))
                            (?P<title>[\w\d-]+)/?
                            (?P<token>[^?]+?)?(?:[?].*)?$)
                       |(?:api(?:-v2)?\.soundcloud\.com/tracks/(?P<track_id>\d+)
                          (?:/?\?secret_token=(?P<secret_token>[^&]+))?)
                    )
                    '''
    IE_NAME = 'soundcloud'
    _TESTS = [
        {
            'url': 'http://soundcloud.com/ethmusic/lostin-powers-she-so-heavy',
            'md5': 'ebef0a451b909710ed1d7787dddbf0d7',
            'info_dict': {
                'id': '62986583',
                'ext': 'mp3',
                'title': 'Lostin Powers - She so Heavy (SneakPreview) Adrian Ackers Blueprint 1',
                'description': 'No Downloads untill we record the finished version this weekend, i was too pumped n i had to post it , earl is prolly gonna b hella p.o\'d',
                'uploader': 'E.T. ExTerrestrial Music',
                'uploader_id': '1571244',
                'timestamp': 1349920598,
                'upload_date': '20121011',
                'duration': 143.216,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            }
        },
        # not streamable song
        {
            'url': 'https://soundcloud.com/the-concept-band/goldrushed-mastered?in=the-concept-band/sets/the-royal-concept-ep',
            'info_dict': {
                'id': '47127627',
                'ext': 'mp3',
                'title': 'Goldrushed',
                'description': 'From Stockholm Sweden\r\nPovel / Magnus / Filip / David\r\nwww.theroyalconcept.com',
                'uploader': 'The Royal Concept',
                'uploader_id': '9615865',
                'timestamp': 1337635207,
                'upload_date': '20120521',
                'duration': 30,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
            'params': {
                # rtmp
                'skip_download': True,
            },
            'skip': 'Preview',
        },
        # private link
        {
            'url': 'https://soundcloud.com/jaimemf/youtube-dl-test-video-a-y-baw/s-8Pjrp',
            'md5': 'aa0dd32bfea9b0c5ef4f02aacd080604',
            'info_dict': {
                'id': '123998367',
                'ext': 'mp3',
                'title': 'Youtube - Dl Test Video \'\' Ä↭',
                'description': 'test chars:  \"\'/\\ä↭',
                'uploader': 'jaimeMF',
                'uploader_id': '69767071',
                'timestamp': 1386604920,
                'upload_date': '20131209',
                'duration': 9.927,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # private link (alt format)
        {
            'url': 'https://api.soundcloud.com/tracks/123998367?secret_token=s-8Pjrp',
            'md5': 'aa0dd32bfea9b0c5ef4f02aacd080604',
            'info_dict': {
                'id': '123998367',
                'ext': 'mp3',
                'title': 'Youtube - Dl Test Video \'\' Ä↭',
                'description': 'test chars:  \"\'/\\ä↭',
                'uploader': 'jaimeMF',
                'uploader_id': '69767071',
                'timestamp': 1386604920,
                'upload_date': '20131209',
                'duration': 9.927,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # downloadable song
        {
            'url': 'https://soundcloud.com/oddsamples/bus-brakes',
            'md5': '7624f2351f8a3b2e7cd51522496e7631',
            'info_dict': {
                'id': '128590877',
                'ext': 'mp3',
                'title': 'Bus Brakes',
                'description': 'md5:0053ca6396e8d2fd7b7e1595ef12ab66',
                'uploader': 'oddsamples',
                'uploader_id': '73680509',
                'timestamp': 1389232924,
                'upload_date': '20140109',
                'duration': 17.346,
                'license': 'cc-by-sa',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # private link, downloadable format
        {
            'url': 'https://soundcloud.com/oriuplift/uponly-238-no-talking-wav/s-AyZUd',
            'md5': '64a60b16e617d41d0bef032b7f55441e',
            'info_dict': {
                'id': '340344461',
                'ext': 'wav',
                'title': 'Uplifting Only 238 [No Talking] (incl. Alex Feed Guestmix) (Aug 31, 2017) [wav]',
                'description': 'md5:fa20ee0fca76a3d6df8c7e57f3715366',
                'uploader': 'Ori Uplift Music',
                'uploader_id': '12563093',
                'timestamp': 1504206263,
                'upload_date': '20170831',
                'duration': 7449.096,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # no album art, use avatar pic for thumbnail
        {
            'url': 'https://soundcloud.com/garyvee/sideways-prod-mad-real',
            'md5': '59c7872bc44e5d99b7211891664760c2',
            'info_dict': {
                'id': '309699954',
                'ext': 'mp3',
                'title': 'Sideways (Prod. Mad Real)',
                'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
                'uploader': 'garyvee',
                'uploader_id': '2366352',
                'timestamp': 1488152409,
                'upload_date': '20170226',
                'duration': 207.012,
                'thumbnail': r're:https?://.*\.jpg',
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
            'params': {
                'skip_download': True,
            },
        },
        # not available via api.soundcloud.com/i1/tracks/id/streams
        {
            'url': 'https://soundcloud.com/giovannisarani/mezzo-valzer',
            'md5': 'e22aecd2bc88e0e4e432d7dcc0a1abf7',
            'info_dict': {
                'id': '583011102',
                'ext': 'mp3',
                'title': 'Mezzo Valzer',
                'description': 'md5:4138d582f81866a530317bae316e8b61',
                'uploader': 'Giovanni Sarani',
                'uploader_id': '3352531',
                'timestamp': 1551394171,
                'upload_date': '20190228',
                'duration': 180.157,
                'thumbnail': r're:https?://.*\.jpg',
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
            'expected_warnings': ['Unable to download JSON metadata'],
        }
    ]

    _API_BASE = 'https://api.soundcloud.com/'
    _API_V2_BASE = 'https://api-v2.soundcloud.com/'
    _BASE_URL = 'https://soundcloud.com/'
    _CLIENT_ID = 'UW9ajvMgVdMMW3cdeBi8lPfN6dvOVGji'
    _IMAGE_REPL_RE = r'-([0-9a-z]+)\.jpg'

    _ARTWORK_MAP = {
        'mini': 16,
        'tiny': 20,
        'small': 32,
        'badge': 47,
        't67x67': 67,
        'large': 100,
        't300x300': 300,
        'crop': 400,
        't500x500': 500,
        'original': 0,
    }

    @classmethod
    def _resolv_url(cls, url):
        return SoundcloudIE._API_V2_BASE + 'resolve?url=' + url + '&client_id=' + cls._CLIENT_ID

    def _extract_info_dict(self, info, full_title=None, secret_token=None, version=2):
        track_id = compat_str(info['id'])
        title = info['title']
        track_base_url = self._API_BASE + 'tracks/%s' % track_id

        format_urls = set()
        formats = []
        query = {'client_id': self._CLIENT_ID}
        if secret_token:
            query['secret_token'] = secret_token

        if info.get('downloadable') and info.get('has_downloads_left'):
            format_url = update_url_query(
                info.get('download_url') or track_base_url + '/download', query)
            format_urls.add(format_url)
            if version == 2:
                v1_info = self._download_json(
                    track_base_url, track_id, query=query, fatal=False) or {}
            else:
                v1_info = info
            formats.append({
                'format_id': 'download',
                'ext': v1_info.get('original_format') or 'mp3',
                'filesize': int_or_none(v1_info.get('original_content_size')),
                'url': format_url,
                'preference': 10,
            })

        def invalid_url(url):
            return not url or url in format_urls or re.search(r'/(?:preview|playlist)/0/30/', url)

        def add_format(f, protocol):
            mobj = re.search(r'\.(?P<abr>\d+)\.(?P<ext>[0-9a-z]{3,4})(?=[/?])', stream_url)
            if mobj:
                for k, v in mobj.groupdict().items():
                    if not f.get(k):
                        f[k] = v
            format_id_list = []
            if protocol:
                format_id_list.append(protocol)
            for k in ('ext', 'abr'):
                v = f.get(k)
                if v:
                    format_id_list.append(v)
            abr = f.get('abr')
            if abr:
                f['abr'] = int(abr)
            f.update({
                'format_id': '_'.join(format_id_list),
                'protocol': 'm3u8_native' if protocol == 'hls' else 'http',
            })
            formats.append(f)

        # New API
        transcodings = try_get(
            info, lambda x: x['media']['transcodings'], list) or []
        for t in transcodings:
            if not isinstance(t, dict):
                continue
            format_url = url_or_none(t.get('url'))
            if not format_url or t.get('snipped') or '/preview/' in format_url:
                continue
            stream = self._download_json(
                format_url, track_id, query=query, fatal=False)
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('url'))
            if invalid_url(stream_url):
                continue
            format_urls.add(stream_url)
            stream_format = t.get('format') or {}
            protocol = stream_format.get('protocol')
            if protocol != 'hls' and '/hls' in format_url:
                protocol = 'hls'
            ext = None
            preset = str_or_none(t.get('preset'))
            if preset:
                ext = preset.split('_')[0]
            if ext not in KNOWN_EXTENSIONS:
                ext = mimetype2ext(stream_format.get('mime_type'))
            add_format({
                'url': stream_url,
                'ext': ext,
            }, 'http' if protocol == 'progressive' else protocol)

        if not formats:
            # Old API, does not work for some tracks (e.g.
            # https://soundcloud.com/giovannisarani/mezzo-valzer)
            # and might serve preview URLs (e.g.
            # http://www.soundcloud.com/snbrn/ele)
            format_dict = self._download_json(
                track_base_url + '/streams', track_id,
                'Downloading track url', query=query, fatal=False) or {}

            for key, stream_url in format_dict.items():
                if invalid_url(stream_url):
                    continue
                format_urls.add(stream_url)
                mobj = re.search(r'(http|hls)_([^_]+)_(\d+)_url', key)
                if mobj:
                    protocol, ext, abr = mobj.groups()
                    add_format({
                        'abr': abr,
                        'ext': ext,
                        'url': stream_url,
                    }, protocol)

        if not formats:
            # We fallback to the stream_url in the original info, this
            # cannot be always used, sometimes it can give an HTTP 404 error
            urlh = self._request_webpage(
                HEADRequest(info.get('stream_url') or track_base_url + '/stream'),
                track_id, query=query, fatal=False)
            if urlh:
                stream_url = urlh.geturl()
                if not invalid_url(stream_url):
                    add_format({'url': stream_url}, 'http')

        for f in formats:
            f['vcodec'] = 'none'

        self._sort_formats(formats)

        user = info.get('user') or {}

        thumbnails = []
        artwork_url = info.get('artwork_url')
        thumbnail = artwork_url or user.get('avatar_url')
        if isinstance(thumbnail, compat_str):
            if re.search(self._IMAGE_REPL_RE, thumbnail):
                for image_id, size in self._ARTWORK_MAP.items():
                    i = {
                        'id': image_id,
                        'url': re.sub(self._IMAGE_REPL_RE, '-%s.jpg' % image_id, thumbnail),
                    }
                    if image_id == 'tiny' and not artwork_url:
                        size = 18
                    elif image_id == 'original':
                        i['preference'] = 10
                    if size:
                        i.update({
                            'width': size,
                            'height': size,
                        })
                    thumbnails.append(i)
            else:
                thumbnails = [{'url': thumbnail}]

        def extract_count(key):
            return int_or_none(info.get('%s_count' % key))

        return {
            'id': track_id,
            'uploader': user.get('username'),
            'uploader_id': str_or_none(user.get('id')) or user.get('permalink'),
            'uploader_url': user.get('permalink_url'),
            'timestamp': unified_timestamp(info.get('created_at')),
            'title': title,
            'description': info.get('description'),
            'thumbnails': thumbnails,
            'duration': float_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
            'view_count': extract_count('playback'),
            'like_count': extract_count('favoritings') or extract_count('likes'),
            'comment_count': extract_count('comment'),
            'repost_count': extract_count('reposts'),
            'genre': info.get('genre'),
            'formats': formats
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        track_id = mobj.group('track_id')

        query = {
            'client_id': self._CLIENT_ID,
        }
        if track_id:
            info_json_url = self._API_V2_BASE + 'tracks/' + track_id
            full_title = track_id
            token = mobj.group('secret_token')
            if token:
                query['secret_token'] = token
        else:
            full_title = resolve_title = '%s/%s' % mobj.group('uploader', 'title')
            token = mobj.group('token')
            if token:
                resolve_title += '/%s' % token
            info_json_url = self._resolv_url(self._BASE_URL + resolve_title)

        version = 2
        info = self._download_json(
            info_json_url, full_title, 'Downloading info JSON', query=query, fatal=False)
        if not info:
            info = self._download_json(
                info_json_url.replace(self._API_V2_BASE, self._API_BASE),
                full_title, 'Downloading info JSON', query=query)
            version = 1

        return self._extract_info_dict(info, full_title, token, version)


class SoundcloudPlaylistBaseIE(SoundcloudIE):
    def _extract_track_entries(self, tracks, token=None):
        entries = []
        for track in tracks:
            track_id = str_or_none(track.get('id'))
            url = track.get('permalink_url')
            if not url:
                if not track_id:
                    continue
                url = self._API_V2_BASE + 'tracks/' + track_id
                if token:
                    url += '?secret_token=' + token
            entries.append(self.url_result(
                url, SoundcloudIE.ie_key(), track_id))
        return entries


class SoundcloudSetIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?soundcloud\.com/(?P<uploader>[\w\d-]+)/sets/(?P<slug_title>[\w\d-]+)(?:/(?P<token>[^?/]+))?'
    IE_NAME = 'soundcloud:set'
    _TESTS = [{
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep',
        'info_dict': {
            'id': '2284613',
            'title': 'The Royal Concept EP',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep/token',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        full_title = '%s/sets/%s' % mobj.group('uploader', 'slug_title')
        token = mobj.group('token')
        if token:
            full_title += '/' + token

        info = self._download_json(self._resolv_url(
            self._BASE_URL + full_title), full_title)

        if 'errors' in info:
            msgs = (compat_str(err['error_message']) for err in info['errors'])
            raise ExtractorError('unable to download video webpage: %s' % ','.join(msgs))

        entries = self._extract_track_entries(info['tracks'], token)

        return self.playlist_result(
            entries, str_or_none(info.get('id')), info.get('title'))


class SoundcloudPagedPlaylistBaseIE(SoundcloudPlaylistBaseIE):
    def _extract_playlist(self, base_url, playlist_id, playlist_title):
        COMMON_QUERY = {
            'limit': 2000000000,
            'client_id': self._CLIENT_ID,
            'linked_partitioning': '1',
        }

        query = COMMON_QUERY.copy()
        query['offset'] = 0

        next_href = base_url

        entries = []
        for i in itertools.count():
            response = self._download_json(
                next_href, playlist_id,
                'Downloading track page %s' % (i + 1), query=query)

            collection = response['collection']

            if not isinstance(collection, list):
                collection = []

            # Empty collection may be returned, in this case we proceed
            # straight to next_href

            def resolve_entry(candidates):
                for cand in candidates:
                    if not isinstance(cand, dict):
                        continue
                    permalink_url = url_or_none(cand.get('permalink_url'))
                    if not permalink_url:
                        continue
                    return self.url_result(
                        permalink_url,
                        SoundcloudIE.ie_key() if SoundcloudIE.suitable(permalink_url) else None,
                        str_or_none(cand.get('id')), cand.get('title'))

            for e in collection:
                entry = resolve_entry((e, e.get('track'), e.get('playlist')))
                if entry:
                    entries.append(entry)

            next_href = response.get('next_href')
            if not next_href:
                break

            next_href = response['next_href']
            parsed_next_href = compat_urlparse.urlparse(next_href)
            query = compat_urlparse.parse_qs(parsed_next_href.query)
            query.update(COMMON_QUERY)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': playlist_title,
            'entries': entries,
        }


class SoundcloudUserIE(SoundcloudPagedPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:(?:www|m)\.)?soundcloud\.com/
                            (?P<user>[^/]+)
                            (?:/
                                (?P<rsrc>tracks|albums|sets|reposts|likes|spotlight)
                            )?
                            /?(?:[?#].*)?$
                    '''
    IE_NAME = 'soundcloud:user'
    _TESTS = [{
        'url': 'https://soundcloud.com/soft-cell-official',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (All)',
        },
        'playlist_mincount': 28,
    }, {
        'url': 'https://soundcloud.com/soft-cell-official/tracks',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (Tracks)',
        },
        'playlist_mincount': 27,
    }, {
        'url': 'https://soundcloud.com/soft-cell-official/albums',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (Albums)',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://soundcloud.com/jcv246/sets',
        'info_dict': {
            'id': '12982173',
            'title': 'Jordi / cv (Sets)',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://soundcloud.com/jcv246/reposts',
        'info_dict': {
            'id': '12982173',
            'title': 'Jordi / cv (Reposts)',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://soundcloud.com/clalberg/likes',
        'info_dict': {
            'id': '11817582',
            'title': 'clalberg (Likes)',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://soundcloud.com/grynpyret/spotlight',
        'info_dict': {
            'id': '7098329',
            'title': 'Grynpyret (Spotlight)',
        },
        'playlist_mincount': 1,
    }]

    _BASE_URL_MAP = {
        'all': 'stream/users/%s',
        'tracks': 'users/%s/tracks',
        'albums': 'users/%s/albums',
        'sets': 'users/%s/playlists',
        'reposts': 'stream/users/%s/reposts',
        'likes': 'users/%s/likes',
        'spotlight': 'users/%s/spotlight',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')

        user = self._download_json(
            self._resolv_url(self._BASE_URL + uploader),
            uploader, 'Downloading user info')

        resource = mobj.group('rsrc') or 'all'

        return self._extract_playlist(
            self._API_V2_BASE + self._BASE_URL_MAP[resource] % user['id'],
            str_or_none(user.get('id')),
            '%s (%s)' % (user['username'], resource.capitalize()))


class SoundcloudTrackStationIE(SoundcloudPagedPlaylistBaseIE):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?soundcloud\.com/stations/track/[^/]+/(?P<id>[^/?#&]+)'
    IE_NAME = 'soundcloud:trackstation'
    _TESTS = [{
        'url': 'https://soundcloud.com/stations/track/officialsundial/your-text',
        'info_dict': {
            'id': '286017854',
            'title': 'Track station: your text',
        },
        'playlist_mincount': 47,
    }]

    def _real_extract(self, url):
        track_name = self._match_id(url)

        track = self._download_json(self._resolv_url(url), track_name)
        track_id = self._search_regex(
            r'soundcloud:track-stations:(\d+)', track['id'], 'track id')

        return self._extract_playlist(
            self._API_V2_BASE + 'stations/%s/tracks' % track['id'],
            track_id, 'Track station: %s' % track['title'])


class SoundcloudPlaylistIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://api(?:-v2)?\.soundcloud\.com/playlists/(?P<id>[0-9]+)(?:/?\?secret_token=(?P<token>[^&]+?))?$'
    IE_NAME = 'soundcloud:playlist'
    _TESTS = [{
        'url': 'https://api.soundcloud.com/playlists/4110309',
        'info_dict': {
            'id': '4110309',
            'title': 'TILT Brass - Bowery Poetry Club, August \'03 [Non-Site SCR 02]',
            'description': 're:.*?TILT Brass - Bowery Poetry Club',
        },
        'playlist_count': 6,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

        query = {
            'client_id': self._CLIENT_ID,
        }
        token = mobj.group('token')
        if token:
            query['secret_token'] = token

        data = self._download_json(
            self._API_V2_BASE + 'playlists/' + playlist_id,
            playlist_id, 'Downloading playlist', query=query)

        entries = self._extract_track_entries(data['tracks'], token)

        return self.playlist_result(
            entries, playlist_id, data.get('title'), data.get('description'))


class SoundcloudSearchIE(SearchInfoExtractor, SoundcloudIE):
    IE_NAME = 'soundcloud:search'
    IE_DESC = 'Soundcloud search'
    _MAX_RESULTS = float('inf')
    _TESTS = [{
        'url': 'scsearch15:post-avant jazzcore',
        'info_dict': {
            'title': 'post-avant jazzcore',
        },
        'playlist_count': 15,
    }]

    _SEARCH_KEY = 'scsearch'
    _MAX_RESULTS_PER_PAGE = 200
    _DEFAULT_RESULTS_PER_PAGE = 50

    def _get_collection(self, endpoint, collection_id, **query):
        limit = min(
            query.get('limit', self._DEFAULT_RESULTS_PER_PAGE),
            self._MAX_RESULTS_PER_PAGE)
        query.update({
            'limit': limit,
            'client_id': self._CLIENT_ID,
            'linked_partitioning': 1,
            'offset': 0,
        })
        next_url = update_url_query(self._API_V2_BASE + endpoint, query)

        collected_results = 0

        for i in itertools.count(1):
            response = self._download_json(
                next_url, collection_id, 'Downloading page {0}'.format(i),
                'Unable to download API page')

            collection = response.get('collection', [])
            if not collection:
                break

            collection = list(filter(bool, collection))
            collected_results += len(collection)

            for item in collection:
                yield self.url_result(item['uri'], SoundcloudIE.ie_key())

            if not collection or collected_results >= limit:
                break

            next_url = response.get('next_href')
            if not next_url:
                break

    def _get_n_results(self, query, n):
        tracks = self._get_collection('search/tracks', query, limit=n, q=query)
        return self.playlist_result(tracks, playlist_title=query)
