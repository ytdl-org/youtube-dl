import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)

class BrightcoveIE(InfoExtractor):
    _VALID_URL = r'http://.*brightcove\.com/.*\?(?P<query>.*videoPlayer=(?P<id>\d*).*)'
    _FEDERATED_URL_TEMPLATE = 'http://c.brightcove.com/services/viewer/htmlFederated?%s'
    
    # There is a test for Brigtcove in GenericIE, that way we test both the download
    # and the detection of videos, and we don't have to find an URL that is always valid

    @classmethod
    def _build_brighcove_url(cls, object_str):
        """
        Build a Brightcove url from a xml string containing
        <object class="BrightcoveExperience">{params}</object>
        """
        object_doc = xml.etree.ElementTree.fromstring(object_str)
        assert object_doc.attrib['class'] == u'BrightcoveExperience'
        params = {'flashID': object_doc.attrib['id'],
                  'playerID': object_doc.find('./param[@name="playerID"]').attrib['value'],
                  '@videoPlayer': object_doc.find('./param[@name="@videoPlayer"]').attrib['value'],
                  }
        playerKey = object_doc.find('./param[@name="playerKey"]')
        # Not all pages define this value
        if playerKey is not None:
            params['playerKey'] = playerKey.attrib['value']
        data = compat_urllib_parse.urlencode(params)
        return cls._FEDERATED_URL_TEMPLATE % data

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query = mobj.group('query')
        video_id = mobj.group('id')

        request_url = self._FEDERATED_URL_TEMPLATE % query
        webpage = self._download_webpage(request_url, video_id)

        self.report_extraction(video_id)
        info = self._search_regex(r'var experienceJSON = ({.*?});', webpage, 'json')
        info = json.loads(info)['data']
        video_info = info['programmedContent']['videoPlayer']['mediaDTO']
        renditions = video_info['renditions']
        renditions = sorted(renditions, key=lambda r: r['size'])
        best_format = renditions[-1]
        
        return {'id': video_id,
                'title': video_info['displayName'],
                'url': best_format['defaultURL'], 
                'ext': 'mp4',
                'description': video_info.get('shortDescription'),
                'thumbnail': video_info.get('videoStillURL') or video_info.get('thumbnailURL'),
                'uploader': video_info.get('publisherName'),
                }
