# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .soundcloud import SoundcloudIE
from ..utils import ExtractorError

import time


class AudiomackIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/song/(?P<id>[\w/-]+)'
    IE_NAME = 'audiomack'
    _TESTS = [
        # hosted on audiomack
        {
            'url': 'http://www.audiomack.com/song/roosh-williams/extraordinary',
            'info_dict':
            {
                'id': '310086',
                'ext': 'mp3',
                'artist': 'Roosh Williams',
                'title': 'Extraordinary'
            }
        },
        # audiomack wrapper around soundcloud song
        {
            'add_ie': ['Soundcloud'],
            'url': 'http://www.audiomack.com/song/xclusiveszone/take-kare',
            'info_dict': {
                'id': '172419696',
                'ext': 'mp3',
                'description': 'md5:1fc3272ed7a635cce5be1568c2822997',
                'title': 'Young Thug ft Lil Wayne - Take Kare',
                'uploader': 'Young Thug World',
                'upload_date': '20141016',
            }
        },
    ]

    @staticmethod
    def create_song_dictionary(api_response, album_url_tag, track_no=0):
        # All keys are the same in audiomack api and InfoExtractor format
        entry = {key: api_response[key] for key in ['title', 'artist', 'id', 'url'] if key in api_response}
        # Fudge values in the face of missing metadata
        if 'id' not in entry:
            entry['id'] = track_no
        if 'title' not in entry:
            entry['title'] = album_url_tag
        return entry

    def _real_extract(self, url):
        # URLs end with [uploader name]/[uploader title]
        # this title is whatever the user types in, and is rarely
        # the proper song title.  Real metadata is in the api response
        album_url_tag = self._match_id(url)

        # Request the extended version of the api for extra fields like artist and title
        api_response = self._download_json(
            'http://www.audiomack.com/api/music/url/song/%s?extended=1&_=%d' % (
                album_url_tag, time.time()),
            album_url_tag)

        # API is inconsistent with errors
        if 'url' not in api_response or not api_response['url'] or 'error' in api_response:
            raise ExtractorError('Invalid url %s', url)

        # Audiomack wraps a lot of soundcloud tracks in their branded wrapper
        # if so, pass the work off to the soundcloud extractor
        if SoundcloudIE.suitable(api_response['url']):
            return {'_type': 'url', 'url': api_response['url'], 'ie_key': 'Soundcloud'}

        return self.create_song_dictionary(api_response, album_url_tag)


class AudiomackAlbumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/album/(?P<id>[\w/-]+)'
    IE_NAME = 'audiomack:album'
    _TESTS = [
        # Standard album playlist
        {
            'url': 'http://www.audiomack.com/album/flytunezcom/tha-tour-part-2-mixtape',
            'playlist_count': 15,
            'info_dict':
            {
                'id': '812251',
                'title': 'Tha Tour: Part 2 (Official Mixtape)'
            }
        },
        # Album playlist ripped from fakeshoredrive with no metadata
        {
            'url': 'http://www.audiomack.com/album/fakeshoredrive/ppp-pistol-p-project',
            'playlist_count': 10
        }
    ]

    def _real_extract(self, url):
        # URLs end with [uploader name]/[uploader title]
        # this title is whatever the user types in, and is rarely
        # the proper song title.  Real metadata is in the api response
        album_url_tag = self._match_id(url)
        result = {'_type': 'playlist', 'entries': []}
        # There is no one endpoint for album metadata - instead it is included/repeated in each song's metadata
        # Therefore we don't know how many songs the album has and must infi-loop until failure
        track_no = 0
        while True:
            # Get song's metadata
            api_response = self._download_json('http://www.audiomack.com/api/music/url/album/%s/%d?extended=1&_=%d'
                                               % (album_url_tag, track_no, time.time()), album_url_tag)

            # Total failure, only occurs when url is totally wrong
            # Won't happen in middle of valid playlist (next case)
            if 'url' not in api_response or 'error' in api_response:
                raise ExtractorError('Invalid url for track %d of album url %s' % (track_no, url))
            # URL is good but song id doesn't exist - usually means end of playlist
            elif not api_response['url']:
                break
            else:
                # Pull out the album metadata and add to result (if it exists)
                for resultkey, apikey in [('id', 'album_id'), ('title', 'album_title')]:
                    if apikey in api_response and resultkey not in result:
                        result[resultkey] = api_response[apikey]
                result['entries'].append(AudiomackIE.create_song_dictionary(api_response, album_url_tag, track_no))
            track_no += 1
        return result
