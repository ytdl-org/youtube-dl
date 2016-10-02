# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

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
    int_or_none,
    unified_strdate,
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
                            (?P<uploader>[\w\d-]+)/
                            (?!(?:tracks|sets(?:/.+?)?|reposts|likes|spotlight)/?(?:$|[?#]))
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
                'upload_date': '20121011',
                'description': 'No Downloads untill we record the finished version this weekend, i was too pumped n i had to post it , earl is prolly gonna b hella p.o\'d',
                'uploader': 'E.T. ExTerrestrial Music',
                'title': 'Lostin Powers - She so Heavy (SneakPreview) Adrian Ackers Blueprint 1',
                'duration': 143,
                'license': 'all-rights-reserved',
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
                'upload_date': '20120521',
                'duration': 227,
                'license': 'all-rights-reserved',
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
                'uploader': 'jaimeMF',
                'description': 'test chars:  \"\'/\\ä↭',
                'upload_date': '20131209',
                'duration': 9,
                'license': 'all-rights-reserved',
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
                'uploader': 'jaimeMF',
                'description': 'test chars:  \"\'/\\ä↭',
                'upload_date': '20131209',
                'duration': 9,
                'license': 'all-rights-reserved',
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
                'upload_date': '20140109',
                'duration': 17,
                'license': 'cc-by-sa',
            },
        },
    ]

    _CLIENT_ID = '02gUJC0hH2ct1EGOcYXQIzRFU91c72Ea'
    _IPHONE_CLIENT_ID = '376f225bf427445fc4bfb6b99b72e0bf'

    @staticmethod
    def _extract_urls(webpage):
        return [m.group('url') for m in re.finditer(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?://)?(?:w\.)?soundcloud\.com/player.+?)\1',
            webpage)]

    def report_resolve(self, video_id):
        """Report information extraction."""
        self.to_screen('%s: Resolving id' % video_id)

    @classmethod
    def _resolv_url(cls, url):
        return 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=' + cls._CLIENT_ID

    def _extract_info_dict(self, info, full_title=None, quiet=False, secret_token=None):
        track_id = compat_str(info['id'])
        name = full_title or track_id
        if quiet:
            self.report_extraction(name)
        thumbnail = info.get('artwork_url')
        if isinstance(thumbnail, compat_str):
            thumbnail = thumbnail.replace('-large', '-t500x500')
        ext = 'mp3'
        result = {
            'id': track_id,
            'uploader': info.get('user', {}).get('username'),
            'upload_date': unified_strdate(info.get('created_at')),
            'title': info['title'],
            'description': info.get('description'),
            'thumbnail': thumbnail,
            'duration': int_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
        }
        formats = []
        if info.get('downloadable', False):
            # We can build a direct link to the song
            format_url = (
                'https://api.soundcloud.com/tracks/{0}/download?client_id={1}'.format(
                    track_id, self._CLIENT_ID))
            formats.append({
                'format_id': 'download',
                'ext': info.get('original_format', 'mp3'),
                'url': format_url,
                'vcodec': 'none',
                'preference': 10,
            })

        # We have to retrieve the url
        streams_url = ('http://api.soundcloud.com/i1/tracks/{0}/streams?'
                       'client_id={1}&secret_token={2}'.format(track_id, self._IPHONE_CLIENT_ID, secret_token))
        format_dict = self._download_json(
            streams_url,
            track_id, 'Downloading track url')

        for key, stream_url in format_dict.items():
            if key.startswith('http'):
                formats.append({
                    'format_id': key,
                    'ext': ext,
                    'url': stream_url,
                    'vcodec': 'none',
                })
            elif key.startswith('rtmp'):
                # The url doesn't have an rtmp app, we have to extract the playpath
                url, path = stream_url.split('mp3:', 1)
                formats.append({
                    'format_id': key,
                    'url': url,
                    'play_path': 'mp3:' + path,
                    'ext': 'flv',
                    'vcodec': 'none',
                })

            if not formats:
                # We fallback to the stream_url in the original info, this
                # cannot be always used, sometimes it can give an HTTP 404 error
                formats.append({
                    'format_id': 'fallback',
                    'url': info['stream_url'] + '?client_id=' + self._CLIENT_ID,
                    'ext': ext,
                    'vcodec': 'none',
                })

            for f in formats:
                if f['format_id'].startswith('http'):
                    f['protocol'] = 'http'
                if f['format_id'].startswith('rtmp'):
                    f['protocol'] = 'rtmp'

        self._check_formats(formats, track_id)
        self._sort_formats(formats)
        result['formats'] = formats

        return result

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)

        track_id = mobj.group('track_id')

        if track_id is not None:
            info_json_url = 'http://api.soundcloud.com/tracks/' + track_id + '.json?client_id=' + self._CLIENT_ID
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

            self.report_resolve(full_title)

            url = 'http://soundcloud.com/%s' % resolve_title
            info_json_url = self._resolv_url(url)
        info = self._download_json(info_json_url, full_title, 'Downloading info JSON')

        return self._extract_info_dict(info, full_title, secret_token=token)


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
        'playlist_mincount': 6,
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
        url = 'http://soundcloud.com/%s/sets/%s' % (uploader, slug_title)

        token = mobj.group('token')
        if token:
            full_title += '/' + token
            url += '/' + token

        self.report_resolve(full_title)

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


class SoundcloudUserIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:(?:www|m)\.)?soundcloud\.com/
                            (?P<user>[^/]+)
                            (?:/
                                (?P<rsrc>tracks|sets|reposts|likes|spotlight)
                            )?
                            /?(?:[?#].*)?$
                    '''
    IE_NAME = 'soundcloud:user'
    _TESTS = [{
        'url': 'https://soundcloud.com/the-akashic-chronicler',
        'info_dict': {
            'id': '114582580',
            'title': 'The Akashic Chronicler (All)',
        },
        'playlist_mincount': 74,
    }, {
        'url': 'https://soundcloud.com/the-akashic-chronicler/tracks',
        'info_dict': {
            'id': '114582580',
            'title': 'The Akashic Chronicler (Tracks)',
        },
        'playlist_mincount': 37,
    }, {
        'url': 'https://soundcloud.com/the-akashic-chronicler/sets',
        'info_dict': {
            'id': '114582580',
            'title': 'The Akashic Chronicler (Playlists)',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://soundcloud.com/the-akashic-chronicler/reposts',
        'info_dict': {
            'id': '114582580',
            'title': 'The Akashic Chronicler (Reposts)',
        },
        'playlist_mincount': 7,
    }, {
        'url': 'https://soundcloud.com/the-akashic-chronicler/likes',
        'info_dict': {
            'id': '114582580',
            'title': 'The Akashic Chronicler (Likes)',
        },
        'playlist_mincount': 321,
    }, {
        'url': 'https://soundcloud.com/grynpyret/spotlight',
        'info_dict': {
            'id': '7098329',
            'title': 'GRYNPYRET (Spotlight)',
        },
        'playlist_mincount': 1,
    }]

    _API_BASE = 'https://api.soundcloud.com'
    _API_V2_BASE = 'https://api-v2.soundcloud.com'

    _BASE_URL_MAP = {
        'all': '%s/profile/soundcloud:users:%%s' % _API_V2_BASE,
        'tracks': '%s/users/%%s/tracks' % _API_BASE,
        'sets': '%s/users/%%s/playlists' % _API_V2_BASE,
        'reposts': '%s/profile/soundcloud:users:%%s/reposts' % _API_V2_BASE,
        'likes': '%s/users/%%s/likes' % _API_V2_BASE,
        'spotlight': '%s/users/%%s/spotlight' % _API_V2_BASE,
    }

    _TITLE_MAP = {
        'all': 'All',
        'tracks': 'Tracks',
        'sets': 'Playlists',
        'reposts': 'Reposts',
        'likes': 'Likes',
        'spotlight': 'Spotlight',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')

        url = 'http://soundcloud.com/%s/' % uploader
        resolv_url = self._resolv_url(url)
        user = self._download_json(
            resolv_url, uploader, 'Downloading user info')

        resource = mobj.group('rsrc') or 'all'
        base_url = self._BASE_URL_MAP[resource] % user['id']

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
                next_href, uploader, 'Downloading track page %s' % (i + 1))

            collection = response['collection']
            if not collection:
                break

            def resolve_permalink_url(candidates):
                for cand in candidates:
                    if isinstance(cand, dict):
                        permalink_url = cand.get('permalink_url')
                        entry_id = self._extract_id(cand)
                        if permalink_url and permalink_url.startswith('http'):
                            return permalink_url, entry_id

            for e in collection:
                permalink_url, entry_id = resolve_permalink_url((e, e.get('track'), e.get('playlist')))
                if permalink_url:
                    entries.append(self.url_result(permalink_url, video_id=entry_id))

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
            'id': compat_str(user['id']),
            'title': '%s (%s)' % (user['username'], self._TITLE_MAP[resource]),
            'entries': entries,
        }


class SoundcloudPlaylistIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://api\.soundcloud\.com/playlists/(?P<id>[0-9]+)(?:/?\?secret_token=(?P<token>[^&]+?))?$'
    IE_NAME = 'soundcloud:playlist'
    _TESTS = [{
        'url': 'http://api.soundcloud.com/playlists/4110309',
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
