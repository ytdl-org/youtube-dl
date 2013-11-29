import json
import re

from .common import InfoExtractor


class PodomaticIE(InfoExtractor):
    IE_NAME = 'podomatic'
    _VALID_URL = r'^(?P<proto>https?)://(?P<channel>[^.]+)\.podomatic\.com/entry/(?P<id>[^?]+)'

    _TEST = {
        u"url": u"http://scienceteachingtips.podomatic.com/entry/2009-01-02T16_03_35-08_00",
        u"file": u"2009-01-02T16_03_35-08_00.mp3",
        u"md5": u"84bb855fcf3429e6bf72460e1eed782d",
        u"info_dict": {
            u"uploader": u"Science Teaching Tips",
            u"uploader_id": u"scienceteachingtips",
            u"title": u"64.  When the Moon Hits Your Eye",
            u"duration": 446,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        channel = mobj.group('channel')

        json_url = (('%s://%s.podomatic.com/entry/embed_params/%s' +
                     '?permalink=true&rtmp=0') %
                    (mobj.group('proto'), channel, video_id))
        data_json = self._download_webpage(
            json_url, video_id, note=u'Downloading video info')
        data = json.loads(data_json)

        video_url = data['downloadLink']
        uploader = data['podcast']
        title = data['title']
        thumbnail = data['imageLocation']
        duration = int(data['length'] / 1000.0)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'uploader': uploader,
            'uploader_id': channel,
            'thumbnail': thumbnail,
            'duration': duration,
        }
