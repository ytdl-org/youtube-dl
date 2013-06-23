import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_str,

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

    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/([\w\d-]+)'
    IE_NAME = u'soundcloud'

    def report_resolve(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Resolving id' % video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # extract uploader (which is in the url)
        uploader = mobj.group(1)
        # extract simple title (uploader + slug of song title)
        slug_title =  mobj.group(2)
        full_title = '%s/%s' % (uploader, slug_title)

        self.report_resolve(full_title)

        url = 'http://soundcloud.com/%s/%s' % (uploader, slug_title)
        resolv_url = 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        info_json = self._download_webpage(resolv_url, full_title, u'Downloading info JSON')

        info = json.loads(info_json)
        video_id = info['id']
        self.report_extraction(full_title)

        streams_url = 'https://api.sndcdn.com/i1/tracks/' + str(video_id) + '/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        stream_json = self._download_webpage(streams_url, full_title,
                                             u'Downloading stream definitions',
                                             u'unable to download stream definitions')

        streams = json.loads(stream_json)
        mediaURL = streams['http_mp3_128_url']
        upload_date = unified_strdate(info['created_at'])

        return [{
            'id':       info['id'],
            'url':      mediaURL,
            'uploader': info['user']['username'],
            'upload_date': upload_date,
            'title':    info['title'],
            'ext':      u'mp3',
            'description': info['description'],
        }]

class SoundcloudSetIE(InfoExtractor):
    """Information extractor for soundcloud.com sets
       To access the media, the uid of the song and a stream token
       must be extracted from the page source and the script must make
       a request to media.soundcloud.com/crossdomain.xml. Then
       the media can be grabbed by requesting from an url composed
       of the stream token and uid
     """

    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/sets/([\w\d-]+)'
    IE_NAME = u'soundcloud:set'

    def report_resolve(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Resolving id' % video_id)

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
        resolv_url = 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        info_json = self._download_webpage(resolv_url, full_title)

        videos = []
        info = json.loads(info_json)
        if 'errors' in info:
            for err in info['errors']:
                self._downloader.report_error(u'unable to download video webpage: %s' % compat_str(err['error_message']))
            return

        self.report_extraction(full_title)
        for track in info['tracks']:
            video_id = track['id']

            streams_url = 'https://api.sndcdn.com/i1/tracks/' + str(video_id) + '/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
            stream_json = self._download_webpage(streams_url, video_id, u'Downloading track info JSON')

            self.report_extraction(video_id)
            streams = json.loads(stream_json)
            mediaURL = streams['http_mp3_128_url']

            videos.append({
                'id':       video_id,
                'url':      mediaURL,
                'uploader': track['user']['username'],
                'upload_date':  unified_strdate(track['created_at']),
                'title':    track['title'],
                'ext':      u'mp3',
                'description': track['description'],
            })
        return videos
