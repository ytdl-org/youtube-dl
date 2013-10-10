import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    compat_urllib_parse,
    determine_ext,
    unified_strdate,
)


class NHLIE(InfoExtractor):
    IE_NAME = u'nhl.com'
    _VALID_URL = r'https?://video(?P<team>\.[^.]*)?\.nhl\.com/videocenter/console\?.*?(?<=[?&])id=(?P<id>\d+)'

    _TEST = {
        u'url': u'http://video.canucks.nhl.com/videocenter/console?catid=6?id=453614',
        u'file': u'453614.mp4',
        u'info_dict': {
            u'title': u'Quick clip: Weise 4-3 goal vs Flames',
            u'description': u'Dale Weise scores his first of the season to put the Canucks up 4-3.',
            u'duration': 18,
            u'upload_date': u'20131006',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        json_url = 'http://video.nhl.com/videocenter/servlets/playlist?ids=%s&format=json' % video_id
        info_json = self._download_webpage(json_url, video_id,
            u'Downloading info json')
        info_json = info_json.replace('\\\'', '\'')
        info = json.loads(info_json)[0]

        initial_video_url = info['publishPoint']
        data = compat_urllib_parse.urlencode({
            'type': 'fvod',
            'path': initial_video_url.replace('.mp4', '_sd.mp4'),
        })
        path_url = 'http://video.nhl.com/videocenter/servlets/encryptvideopath?' + data
        path_response = self._download_webpage(path_url, video_id,
            u'Downloading final video url')
        path_doc = xml.etree.ElementTree.fromstring(path_response)
        video_url = path_doc.find('path').text

        join = compat_urlparse.urljoin
        return {
            'id': video_id,
            'title': info['name'],
            'url': video_url,
            'ext': determine_ext(video_url),
            'description': info['description'],
            'duration': int(info['duration']),
            'thumbnail': join(join(video_url, '/u/'), info['bigImage']),
            'upload_date': unified_strdate(info['releaseDate'].split('.')[0]),
        }
