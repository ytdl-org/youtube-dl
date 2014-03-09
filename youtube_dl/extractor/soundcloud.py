# encoding: utf-8
from __future__ import unicode_literals

import json
import re
import itertools

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urlparse,
    compat_urllib_parse,

    ExtractorError,
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

    _VALID_URL = r'''^(?:https?://)?
                    (?:(?:(?:www\.|m\.)?soundcloud\.com/
                            (?P<uploader>[\w\d-]+)/
                            (?!sets/)(?P<title>[\w\d-]+)/?
                            (?P<token>[^?]+?)?(?:[?].*)?$)
                       |(?:api\.soundcloud\.com/tracks/(?P<track_id>\d+))
                       |(?P<player>(?:w|player|p.)\.soundcloud\.com/player/?.*?url=.*)
                    )
                    '''
    IE_NAME = 'soundcloud'
    _TESTS = [
        {
            'url': 'http://soundcloud.com/ethmusic/lostin-powers-she-so-heavy',
            'file': '62986583.mp3',
            'md5': 'ebef0a451b909710ed1d7787dddbf0d7',
            'info_dict': {
                "upload_date": "20121011",
                "description": "No Downloads untill we record the finished version this weekend, i was too pumped n i had to post it , earl is prolly gonna b hella p.o'd",
                "uploader": "E.T. ExTerrestrial Music",
                "title": "Lostin Powers - She so Heavy (SneakPreview) Adrian Ackers Blueprint 1"
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
            },
        },
        # downloadable song
        {
            'url': 'https://soundcloud.com/simgretina/just-your-problem-baby-1',
            'md5': '56a8b69568acaa967b4c49f9d1d52d19',
            'info_dict': {
                'id': '105614606',
                'ext': 'wav',
                'title': 'Just Your Problem Baby (Acapella)',
                'description': 'Vocals',
                'uploader': 'Sim Gretina',
                'upload_date': '20130815',
            },
        },
    ]

    _CLIENT_ID = 'b45b1aa10f1ac2941910a7f0d10f8e28'
    _IPHONE_CLIENT_ID = '376f225bf427445fc4bfb6b99b72e0bf'

    @classmethod
    def suitable(cls, url):
        return re.match(cls._VALID_URL, url, flags=re.VERBOSE) is not None

    def report_resolve(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Resolving id' % video_id)

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
        }
        if info.get('downloadable', False):
            # We can build a direct link to the song
            format_url = (
                'https://api.soundcloud.com/tracks/{0}/download?client_id={1}'.format(
                    track_id, self._CLIENT_ID))
            result['formats'] = [{
                'format_id': 'download',
                'ext': info.get('original_format', 'mp3'),
                'url': format_url,
                'vcodec': 'none',
            }]
        else:
            # We have to retrieve the url
            streams_url = ('http://api.soundcloud.com/i1/tracks/{0}/streams?'
                'client_id={1}&secret_token={2}'.format(track_id, self._IPHONE_CLIENT_ID, secret_token))
            stream_json = self._download_webpage(
                streams_url,
                track_id, 'Downloading track url')

            formats = []
            format_dict = json.loads(stream_json)
            for key, stream_url in format_dict.items():
                if key.startswith(u'http'):
                    formats.append({
                        'format_id': key,
                        'ext': ext,
                        'url': stream_url,
                        'vcodec': 'none',
                    })
                elif key.startswith(u'rtmp'):
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
            raise ExtractorError(u'Invalid URL: %s' % url)

        track_id = mobj.group('track_id')
        token = None
        if track_id is not None:
            info_json_url = 'http://api.soundcloud.com/tracks/' + track_id + '.json?client_id=' + self._CLIENT_ID
            full_title = track_id
        elif mobj.group('player'):
            query = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            return self.url_result(query['url'][0], ie='Soundcloud')
        else:
            # extract uploader (which is in the url)
            uploader = mobj.group('uploader')
            # extract simple title (uploader + slug of song title)
            slug_title =  mobj.group('title')
            token = mobj.group('token')
            full_title = resolve_title = '%s/%s' % (uploader, slug_title)
            if token:
                resolve_title += '/%s' % token
    
            self.report_resolve(full_title)
    
            url = 'http://soundcloud.com/%s' % resolve_title
            info_json_url = self._resolv_url(url)
        info_json = self._download_webpage(info_json_url, full_title, 'Downloading info JSON')

        info = json.loads(info_json)
        return self._extract_info_dict(info, full_title, secret_token=token)

class SoundcloudSetIE(SoundcloudIE):
    _VALID_URL = r'https?://(?:www\.)?soundcloud\.com/([\w\d-]+)/sets/([\w\d-]+)'
    IE_NAME = 'soundcloud:set'
    # it's in tests/test_playlists.py
    _TESTS = []

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # extract uploader (which is in the url)
        uploader = mobj.group(1)
        # extract simple title (uploader + slug of song title)
        slug_title =  mobj.group(2)
        full_title = '%s/sets/%s' % (uploader, slug_title)

        self.report_resolve(full_title)

        url = 'http://soundcloud.com/%s/sets/%s' % (uploader, slug_title)
        resolv_url = self._resolv_url(url)
        info_json = self._download_webpage(resolv_url, full_title)

        info = json.loads(info_json)
        if 'errors' in info:
            for err in info['errors']:
                self._downloader.report_error(u'unable to download video webpage: %s' % compat_str(err['error_message']))
            return

        self.report_extraction(full_title)
        return {'_type': 'playlist',
                'entries': [self._extract_info_dict(track) for track in info['tracks']],
                'id': info['id'],
                'title': info['title'],
                }


class SoundcloudUserIE(SoundcloudIE):
    _VALID_URL = r'https?://(www\.)?soundcloud\.com/(?P<user>[^/]+)(/?(tracks/)?)?(\?.*)?$'
    IE_NAME = 'soundcloud:user'

    # it's in tests/test_playlists.py
    _TESTS = []

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')

        url = 'http://soundcloud.com/%s/' % uploader
        resolv_url = self._resolv_url(url)
        user_json = self._download_webpage(resolv_url, uploader,
            'Downloading user info')
        user = json.loads(user_json)

        tracks = []
        for i in itertools.count():
            data = compat_urllib_parse.urlencode({'offset': i*50,
                                                  'client_id': self._CLIENT_ID,
                                                  })
            tracks_url = 'http://api.soundcloud.com/users/%s/tracks.json?' % user['id'] + data
            response = self._download_webpage(tracks_url, uploader, 
                'Downloading tracks page %s' % (i+1))
            new_tracks = json.loads(response)
            tracks.extend(self._extract_info_dict(track, quiet=True) for track in new_tracks)
            if len(new_tracks) < 50:
                break

        return {
            '_type': 'playlist',
            'id': compat_str(user['id']),
            'title': user['username'],
            'entries': tracks,
        }
