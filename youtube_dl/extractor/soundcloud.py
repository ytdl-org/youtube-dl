# encoding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urlparse,
    compat_urllib_parse,

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
                            (?!sets/|likes/?(?:$|[?#]))
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
            },
        },
    ]

    _CLIENT_ID = 'b45b1aa10f1ac2941910a7f0d10f8e28'
    _IPHONE_CLIENT_ID = '376f225bf427445fc4bfb6b99b72e0bf'

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

        thumbnail = info['artwork_url']
        if thumbnail is not None:
            thumbnail = thumbnail.replace('-large', '-t500x500')
        ext = 'mp3'
        result = {
            'id': track_id,
            'uploader': info['user']['username'],
            'upload_date': unified_strdate(info['created_at']),
            'title': info['title'],
            'description': info['description'],
            'thumbnail': thumbnail,
            'duration': int_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
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
                    'ext': ext,
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

            self._sort_formats(formats)
            result['formats'] = formats

        return result

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)

        track_id = mobj.group('track_id')
        token = None
        if track_id is not None:
            info_json_url = 'http://api.soundcloud.com/tracks/' + track_id + '.json?client_id=' + self._CLIENT_ID
            full_title = track_id
            token = mobj.group('secret_token')
            if token:
                info_json_url += "&secret_token=" + token
        elif mobj.group('player'):
            query = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            return self.url_result(query['url'][0])
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


class SoundcloudSetIE(SoundcloudIE):
    _VALID_URL = r'https?://(?:www\.)?soundcloud\.com/(?P<uploader>[\w\d-]+)/sets/(?P<slug_title>[\w\d-]+)(?:/(?P<token>[^?/]+))?'
    IE_NAME = 'soundcloud:set'
    _TESTS = [{
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep',
        'info_dict': {
            'title': 'The Royal Concept EP',
        },
        'playlist_mincount': 6,
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
            for err in info['errors']:
                self._downloader.report_error('unable to download video webpage: %s' % compat_str(err['error_message']))
            return

        return {
            '_type': 'playlist',
            'entries': [self._extract_info_dict(track, secret_token=token) for track in info['tracks']],
            'id': info['id'],
            'title': info['title'],
        }


class SoundcloudUserIE(SoundcloudIE):
    _VALID_URL = r'https?://(www\.)?soundcloud\.com/(?P<user>[^/]+)/?((?P<rsrc>tracks|likes)/?)?(\?.*)?$'
    IE_NAME = 'soundcloud:user'
    _TESTS = [{
        'url': 'https://soundcloud.com/the-concept-band',
        'info_dict': {
            'id': '9615865',
            'title': 'The Royal Concept',
        },
        'playlist_mincount': 12
    }, {
        'url': 'https://soundcloud.com/the-concept-band/likes',
        'info_dict': {
            'id': '9615865',
            'title': 'The Royal Concept',
        },
        'playlist_mincount': 1,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')
        resource = mobj.group('rsrc')
        if resource is None:
            resource = 'tracks'
        elif resource == 'likes':
            resource = 'favorites'

        url = 'http://soundcloud.com/%s/' % uploader
        resolv_url = self._resolv_url(url)
        user = self._download_json(
            resolv_url, uploader, 'Downloading user info')
        base_url = 'http://api.soundcloud.com/users/%s/%s.json?' % (uploader, resource)

        entries = []
        for i in itertools.count():
            data = compat_urllib_parse.urlencode({
                'offset': i * 50,
                'limit': 50,
                'client_id': self._CLIENT_ID,
            })
            new_entries = self._download_json(
                base_url + data, uploader, 'Downloading track page %s' % (i + 1))
            if len(new_entries) == 0:
                self.to_screen('%s: End page received' % uploader)
                break
            entries.extend(self._extract_info_dict(e, quiet=True) for e in new_entries)

        return {
            '_type': 'playlist',
            'id': compat_str(user['id']),
            'title': user['username'],
            'entries': entries,
        }


class SoundcloudPlaylistIE(SoundcloudIE):
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

        data = compat_urllib_parse.urlencode(data_dict)
        data = self._download_json(
            base_url + data, playlist_id, 'Downloading playlist')

        entries = [
            self._extract_info_dict(t, quiet=True, secret_token=token)
            for t in data['tracks']]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'entries': entries,
        }
