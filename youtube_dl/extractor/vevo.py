import re
import json
import xml.etree.ElementTree
import datetime

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
)


class VevoIE(InfoExtractor):
    """
    Accepts urls from vevo.com or in the format 'vevo:{id}'
    (currently used by MTVIE)
    """
    _VALID_URL = r'((http://www.vevo.com/watch/.*?/.*?/)|(vevo:))(?P<id>.*?)(\?|$)'
    _TEST = {
        u'url': u'http://www.vevo.com/watch/hurts/somebody-to-die-for/GB1101300280',
        u'file': u'GB1101300280.mp4',
        u'info_dict': {
            u"upload_date": u"20130624",
            u"uploader": u"Hurts",
            u"title": u"Somebody to Die For",
            u'duration': 230,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        json_url = 'http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc=%s' % video_id
        info_json = self._download_webpage(json_url, video_id, u'Downloading json info')

        self.report_extraction(video_id)
        video_info = json.loads(info_json)['video']
        last_version = {'version': -1}
        for version in video_info['videoVersions']:
            # These are the HTTP downloads, other types are for different manifests
            if version['sourceType'] == 2:
                if version['version'] > last_version['version']:
                    last_version = version
        if last_version['version'] == -1:
            raise ExtractorError(u'Unable to extract last version of the video')

        renditions = xml.etree.ElementTree.fromstring(last_version['data'])
        formats = []
        # Already sorted from worst to best quality
        for rend in renditions.findall('rendition'):
            attr = rend.attrib
            f_url = attr['url']
            formats.append({
                'url': f_url,
                'ext': determine_ext(f_url),
                'height': int(attr['frameheight']),
                'width': int(attr['frameWidth']),
            })

        date_epoch = int(self._search_regex(
            r'/Date\((\d+)\)/', video_info['launchDate'], u'launch date'))/1000
        upload_date = datetime.datetime.fromtimestamp(date_epoch)
        info = {
            'id': video_id,
            'title': video_info['title'],
            'formats': formats,
            'thumbnail': video_info['imageUrl'],
            'upload_date': upload_date.strftime('%Y%m%d'),
            'uploader': video_info['mainArtists'][0]['artistName'],
            'duration': video_info['duration'],
        }

        # TODO: Remove when #980 has been merged
        info.update(formats[-1])

        return info
