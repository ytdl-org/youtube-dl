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

    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/([\w\d-]+)(?:[?].*)?$'
    IE_NAME = u'soundcloud'
    _TEST = {
        u'url': u'http://soundcloud.com/ethmusic/lostin-powers-she-so-heavy',
        u'file': u'62986583.mp3',
        u'md5': u'ebef0a451b909710ed1d7787dddbf0d7',
        u'info_dict': {
            u"upload_date": u"20121011", 
            u"description": u"No Downloads untill we record the finished version this weekend, i was too pumped n i had to post it , earl is prolly gonna b hella p.o'd", 
            u"uploader": u"E.T. ExTerrestrial Music", 
            u"title": u"Lostin Powers - She so Heavy (SneakPreview) Adrian Ackers Blueprint 1"
        }
    }

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

    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/sets/([\w\d-]+)(?:[?].*)?$'
    IE_NAME = u'soundcloud:set'
    _TEST = {
        u"url":"https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep",
        u"playlist": [
            {
                u"file":"30510138.mp3",
                u"md5":"f9136bf103901728f29e419d2c70f55d",
                u"info_dict": {
                    u"upload_date": u"20111213",
                    u"description": u"The Royal Concept from Stockholm\r\nFilip / Povel / David / Magnus\r\nwww.royalconceptband.com",
                    u"uploader": u"The Royal Concept",
                    u"title": u"D-D-Dance"
                }
            },
            {
                u"file":"47127625.mp3",
                u"md5":"09b6758a018470570f8fd423c9453dd8",
                u"info_dict": {
                    u"upload_date": u"20120521",
                    u"description": u"The Royal Concept from Stockholm\r\nFilip / Povel / David / Magnus\r\nwww.royalconceptband.com",
                    u"uploader": u"The Royal Concept",
                    u"title": u"The Royal Concept - Gimme Twice"
                }
            },
            {
                u"file":"47127627.mp3",
                u"md5":"154abd4e418cea19c3b901f1e1306d9c",
                u"info_dict": {
                    u"upload_date": u"20120521",
                    u"uploader": u"The Royal Concept",
                    u"title": u"Goldrushed"
                }
            },
            {
                u"file":"47127629.mp3",
                u"md5":"2f5471edc79ad3f33a683153e96a79c1",
                u"info_dict": {
                    u"upload_date": u"20120521",
                    u"description": u"The Royal Concept from Stockholm\r\nFilip / Povel / David / Magnus\r\nwww.royalconceptband.com",
                    u"uploader": u"The Royal Concept",
                    u"title": u"In the End"
                }
            },
            {
                u"file":"47127631.mp3",
                u"md5":"f9ba87aa940af7213f98949254f1c6e2",
                u"info_dict": {
                    u"upload_date": u"20120521",
                    u"description": u"The Royal Concept from Stockholm\r\nFilip / David / Povel / Magnus\r\nwww.theroyalconceptband.com",
                    u"uploader": u"The Royal Concept",
                    u"title": u"Knocked Up"
                }
            },
            {
                u"file":"75206121.mp3",
                u"md5":"f9d1fe9406717e302980c30de4af9353",
                u"info_dict": {
                    u"upload_date": u"20130116",
                    u"description": u"The unreleased track World on Fire premiered on the CW's hit show Arrow (8pm/7pm central).  \r\nAs a gift to our fans we would like to offer you a free download of the track!  ",
                    u"uploader": u"The Royal Concept",
                    u"title": u"World On Fire"
                }
            }
        ]
    }

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
