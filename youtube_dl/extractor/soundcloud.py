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
    compat_urllib_parse_urlencode,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    KNOWN_EXTENSIONS,
    merge_dicts,
    mimetype2ext,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
)


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
                       |(?:api\.soundcloud\.com/tracks/(?P<track_id>\d+)
                          (?:/?\?secret_token=(?P<secret_token>[^&]+))?)
                       |(?P<player>(?:w|player|p.)\.soundcloud\.com/player/?.*?url=.*)
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

    _CLIENT_ID = 'BeGVhOrGmfboy1LtiHTQF6Ejpt9ULJCI'

    @staticmethod
    def _extract_urls(webpage):
        return [m.group('url') for m in re.finditer(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?://)?(?:w\.)?soundcloud\.com/player.+?)\1',
            webpage)]

    @classmethod
    def _resolv_url(cls, url):
        return 'https://api.soundcloud.com/resolve.json?url=' + url + '&client_id=' + cls._CLIENT_ID

    def _extract_info_dict(self, info, full_title=None, quiet=False, secret_token=None):
        track_id = compat_str(info['id'])
        title = info['title']
        name = full_title or track_id
        if quiet:
            self.report_extraction(name)
        thumbnail = info.get('artwork_url') or info.get('user', {}).get('avatar_url')
        if isinstance(thumbnail, compat_str):
            thumbnail = thumbnail.replace('-large', '-t500x500')
        username = try_get(info, lambda x: x['user']['username'], compat_str)

        def extract_count(key):
            return int_or_none(info.get('%s_count' % key))

        like_count = extract_count('favoritings')
        if like_count is None:
            like_count = extract_count('likes')

        result = {
            'id': track_id,
            'uploader': username,
            'timestamp': unified_timestamp(info.get('created_at')),
            'title': title,
            'description': info.get('description'),
            'thumbnail': thumbnail,
            'duration': float_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
            'view_count': extract_count('playback'),
            'like_count': like_count,
            'comment_count': extract_count('comment'),
            'repost_count': extract_count('reposts'),
            'genre': info.get('genre'),
        }

        format_urls = set()
        formats = []
        query = {'client_id': self._CLIENT_ID}
        if secret_token is not None:
            query['secret_token'] = secret_token
        if info.get('downloadable', False):
            # We can build a direct link to the song
            format_url = update_url_query(
                'https://api.soundcloud.com/tracks/%s/download' % track_id, query)
            format_urls.add(format_url)
            formats.append({
                'format_id': 'download',
                'ext': info.get('original_format', 'mp3'),
                'url': format_url,
                'vcodec': 'none',
                'preference': 10,
            })

        # Old API, does not work for some tracks (e.g.
        # https://soundcloud.com/giovannisarani/mezzo-valzer)
        format_dict = self._download_json(
            'https://api.soundcloud.com/i1/tracks/%s/streams' % track_id,
            track_id, 'Downloading track url', query=query, fatal=False)

        if format_dict:
            for key, stream_url in format_dict.items():
                if stream_url in format_urls:
                    continue
                format_urls.add(stream_url)
                ext, abr = 'mp3', None
                mobj = re.search(r'_([^_]+)_(\d+)_url', key)
                if mobj:
                    ext, abr = mobj.groups()
                    abr = int(abr)
                if key.startswith('http'):
                    stream_formats = [{
                        'format_id': key,
                        'ext': ext,
                        'url': stream_url,
                    }]
                elif key.startswith('rtmp'):
                    # The url doesn't have an rtmp app, we have to extract the playpath
                    url, path = stream_url.split('mp3:', 1)
                    stream_formats = [{
                        'format_id': key,
                        'url': url,
                        'play_path': 'mp3:' + path,
                        'ext': 'flv',
                    }]
                elif key.startswith('hls'):
                    stream_formats = self._extract_m3u8_formats(
                        stream_url, track_id, ext, entry_protocol='m3u8_native',
                        m3u8_id=key, fatal=False)
                else:
                    continue

                if abr:
                    for f in stream_formats:
                        f['abr'] = abr

                formats.extend(stream_formats)

        # New API
        transcodings = try_get(
            info, lambda x: x['media']['transcodings'], list) or []
        for t in transcodings:
            if not isinstance(t, dict):
                continue
            format_url = url_or_none(t.get('url'))
            if not format_url:
                continue
            stream = self._download_json(
                update_url_query(format_url, query), track_id, fatal=False)
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('url'))
            if not stream_url:
                continue
            if stream_url in format_urls:
                continue
            format_urls.add(stream_url)
            protocol = try_get(t, lambda x: x['format']['protocol'], compat_str)
            if protocol != 'hls' and '/hls' in format_url:
                protocol = 'hls'
            ext = None
            preset = str_or_none(t.get('preset'))
            if preset:
                ext = preset.split('_')[0]
                if ext not in KNOWN_EXTENSIONS:
                    mimetype = try_get(
                        t, lambda x: x['format']['mime_type'], compat_str)
                    ext = mimetype2ext(mimetype) or 'mp3'
            format_id_list = []
            if protocol:
                format_id_list.append(protocol)
            format_id_list.append(ext)
            format_id = '_'.join(format_id_list)
            formats.append({
                'url': stream_url,
                'format_id': format_id,
                'ext': ext,
                'protocol': 'm3u8_native' if protocol == 'hls' else 'http',
            })

        if not formats:
            # We fallback to the stream_url in the original info, this
            # cannot be always used, sometimes it can give an HTTP 404 error
            formats.append({
                'format_id': 'fallback',
                'url': update_url_query(info['stream_url'], query),
                'ext': 'mp3',
            })
            self._check_formats(formats, track_id)

        for f in formats:
            f['vcodec'] = 'none'

        self._sort_formats(formats)
        result['formats'] = formats

        return result

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)

        track_id = mobj.group('track_id')
        new_info = {}

        if track_id is not None:
            info_json_url = 'https://api.soundcloud.com/tracks/' + track_id + '.json?client_id=' + self._CLIENT_ID
            full_title = track_id
            token = mobj.group('secret_token')
            if token:
                info_json_url += '&secret_token=' + token
        elif mobj.group('player'):
            query = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            real_url = query['url'][0]
            # If the token is in the query of the original url we have to
            # manually add it
            if 'secret_token' in query:
                real_url += '?secret_token=' + query['secret_token'][0]
            return self.url_result(real_url)
        else:
            # extract uploader (which is in the url)
            uploader = mobj.group('uploader')
            # extract simple title (uploader + slug of song title)
            slug_title = mobj.group('title')
            token = mobj.group('token')
            full_title = resolve_title = '%s/%s' % (uploader, slug_title)
            if token:
                resolve_title += '/%s' % token

            webpage = self._download_webpage(url, full_title, fatal=False)
            if webpage:
                entries = self._parse_json(
                    self._search_regex(
                        r'var\s+c\s*=\s*(\[.+?\])\s*,\s*o\s*=Date\b', webpage,
                        'data', default='[]'), full_title, fatal=False)
                if entries:
                    for e in entries:
                        if not isinstance(e, dict):
                            continue
                        if e.get('id') != 67:
                            continue
                        data = try_get(e, lambda x: x['data'][0], dict)
                        if data:
                            new_info = data
                            break
                info_json_url = self._resolv_url(
                    'https://soundcloud.com/%s' % resolve_title)

        # Contains some additional info missing from new_info
        info = self._download_json(
            info_json_url, full_title, 'Downloading info JSON')

        return self._extract_info_dict(
            merge_dicts(info, new_info), full_title, secret_token=token)


class SoundcloudPlaylistBaseIE(SoundcloudIE):
    @staticmethod
    def _extract_id(e):
        return compat_str(e['id']) if e.get('id') else None

    def _extract_track_entries(self, tracks):
        return [
            self.url_result(
                track['permalink_url'], SoundcloudIE.ie_key(),
                video_id=self._extract_id(track))
            for track in tracks if track.get('permalink_url')]


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

        # extract uploader (which is in the url)
        uploader = mobj.group('uploader')
        # extract simple title (uploader + slug of song title)
        slug_title = mobj.group('slug_title')
        full_title = '%s/sets/%s' % (uploader, slug_title)
        url = 'https://soundcloud.com/%s/sets/%s' % (uploader, slug_title)

        token = mobj.group('token')
        if token:
            full_title += '/' + token
            url += '/' + token

        resolv_url = self._resolv_url(url)
        info = self._download_json(resolv_url, full_title)

        if 'errors' in info:
            msgs = (compat_str(err['error_message']) for err in info['errors'])
            raise ExtractorError('unable to download video webpage: %s' % ','.join(msgs))

        entries = self._extract_track_entries(info['tracks'])

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': '%s' % info['id'],
            'title': info['title'],
        }


class SoundcloudPagedPlaylistBaseIE(SoundcloudPlaylistBaseIE):
    _API_V2_BASE = 'https://api-v2.soundcloud.com'

    def _extract_playlist(self, base_url, playlist_id, playlist_title):
        COMMON_QUERY = {
            'limit': 50,
            'client_id': self._CLIENT_ID,
            'linked_partitioning': '1',
        }

        query = COMMON_QUERY.copy()
        query['offset'] = 0

        next_href = base_url + '?' + compat_urllib_parse_urlencode(query)

        entries = []
        for i in itertools.count():
            response = self._download_json(
                next_href, playlist_id, 'Downloading track page %s' % (i + 1))

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
                        ie=SoundcloudIE.ie_key() if SoundcloudIE.suitable(permalink_url) else None,
                        video_id=self._extract_id(cand),
                        video_title=cand.get('title'))

            for e in collection:
                entry = resolve_entry((e, e.get('track'), e.get('playlist')))
                if entry:
                    entries.append(entry)

            next_href = response.get('next_href')
            if not next_href:
                break

            parsed_next_href = compat_urlparse.urlparse(response['next_href'])
            qs = compat_urlparse.parse_qs(parsed_next_href.query)
            qs.update(COMMON_QUERY)
            next_href = compat_urlparse.urlunparse(
                parsed_next_href._replace(query=compat_urllib_parse_urlencode(qs, True)))

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
            'title': 'Jordi / cv (Playlists)',
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
        'all': '%s/stream/users/%%s' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
        'tracks': '%s/users/%%s/tracks' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
        'albums': '%s/users/%%s/albums' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
        'sets': '%s/users/%%s/playlists' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
        'reposts': '%s/stream/users/%%s/reposts' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
        'likes': '%s/users/%%s/likes' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
        'spotlight': '%s/users/%%s/spotlight' % SoundcloudPagedPlaylistBaseIE._API_V2_BASE,
    }

    _TITLE_MAP = {
        'all': 'All',
        'tracks': 'Tracks',
        'albums': 'Albums',
        'sets': 'Playlists',
        'reposts': 'Reposts',
        'likes': 'Likes',
        'spotlight': 'Spotlight',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')

        url = 'https://soundcloud.com/%s/' % uploader
        resolv_url = self._resolv_url(url)
        user = self._download_json(
            resolv_url, uploader, 'Downloading user info')

        resource = mobj.group('rsrc') or 'all'

        return self._extract_playlist(
            self._BASE_URL_MAP[resource] % user['id'], compat_str(user['id']),
            '%s (%s)' % (user['username'], self._TITLE_MAP[resource]))


class SoundcloudTrackStationIE(SoundcloudPagedPlaylistBaseIE):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?soundcloud\.com/stations/track/[^/]+/(?P<id>[^/?#&]+)'
    IE_NAME = 'soundcloud:trackstation'
    _TESTS = [{
        'url': 'https://soundcloud.com/stations/track/officialsundial/your-text',
        'info_dict': {
            'id': '286017854',
            'title': 'Track station: your-text',
        },
        'playlist_mincount': 47,
    }]

    def _real_extract(self, url):
        track_name = self._match_id(url)

        webpage = self._download_webpage(url, track_name)

        track_id = self._search_regex(
            r'soundcloud:track-stations:(\d+)', webpage, 'track id')

        return self._extract_playlist(
            '%s/stations/soundcloud:track-stations:%s/tracks'
            % (self._API_V2_BASE, track_id),
            track_id, 'Track station: %s' % track_name)


class SoundcloudPlaylistIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://api\.soundcloud\.com/playlists/(?P<id>[0-9]+)(?:/?\?secret_token=(?P<token>[^&]+?))?$'
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
        base_url = '%s//api.soundcloud.com/playlists/%s.json?' % (self.http_scheme(), playlist_id)

        data_dict = {
            'client_id': self._CLIENT_ID,
        }
        token = mobj.group('token')

        if token:
            data_dict['secret_token'] = token

        data = compat_urllib_parse_urlencode(data_dict)
        data = self._download_json(
            base_url + data, playlist_id, 'Downloading playlist')

        entries = self._extract_track_entries(data['tracks'])

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'entries': entries,
        }


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
    _API_V2_BASE = 'https://api-v2.soundcloud.com'

    def _get_collection(self, endpoint, collection_id, **query):
        limit = min(
            query.get('limit', self._DEFAULT_RESULTS_PER_PAGE),
            self._MAX_RESULTS_PER_PAGE)
        query['limit'] = limit
        query['client_id'] = self._CLIENT_ID
        query['linked_partitioning'] = '1'
        query['offset'] = 0
        data = compat_urllib_parse_urlencode(query)
        next_url = '{0}{1}?{2}'.format(self._API_V2_BASE, endpoint, data)

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
        tracks = self._get_collection('/search/tracks', query, limit=n, q=query)
        return self.playlist_result(tracks, playlist_title=query)
