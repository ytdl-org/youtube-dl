import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    find_xpath_attr,
    compat_urlparse,
)

class BrightcoveIE(InfoExtractor):
    _VALID_URL = r'https?://.*brightcove\.com/(services|viewer).*\?(?P<query>.*)'
    _FEDERATED_URL_TEMPLATE = 'http://c.brightcove.com/services/viewer/htmlFederated?%s'
    _PLAYLIST_URL_TEMPLATE = 'http://c.brightcove.com/services/json/experience/runtime/?command=get_programming_for_experience&playerKey=%s'
    
    # There is a test for Brigtcove in GenericIE, that way we test both the download
    # and the detection of videos, and we don't have to find an URL that is always valid

    @classmethod
    def _build_brighcove_url(cls, object_str):
        """
        Build a Brightcove url from a xml string containing
        <object class="BrightcoveExperience">{params}</object>
        """
        object_doc = xml.etree.ElementTree.fromstring(object_str)
        assert u'BrightcoveExperience' in object_doc.attrib['class']
        params = {'flashID': object_doc.attrib['id'],
                  'playerID': find_xpath_attr(object_doc, './param', 'name', 'playerID').attrib['value'],
                  }
        playerKey = find_xpath_attr(object_doc, './param', 'name', 'playerKey')
        # Not all pages define this value
        if playerKey is not None:
            params['playerKey'] = playerKey.attrib['value']
        videoPlayer = find_xpath_attr(object_doc, './param', 'name', '@videoPlayer')
        if videoPlayer is not None:
            params['@videoPlayer'] = videoPlayer.attrib['value']
        data = compat_urllib_parse.urlencode(params)
        return cls._FEDERATED_URL_TEMPLATE % data

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_str = mobj.group('query')
        query = compat_urlparse.parse_qs(query_str)

        videoPlayer = query.get('@videoPlayer')
        if videoPlayer:
            return self._get_video_info(videoPlayer[0], query_str)
        else:
            player_key = query['playerKey']
            return self._get_playlist_info(player_key[0])

    def _get_video_info(self, video_id, query):
        request_url = self._FEDERATED_URL_TEMPLATE % query
        webpage = self._download_webpage(request_url, video_id)

        self.report_extraction(video_id)
        info = self._search_regex(r'var experienceJSON = ({.*?});', webpage, 'json')
        info = json.loads(info)['data']
        video_info = info['programmedContent']['videoPlayer']['mediaDTO']

        return self._extract_video_info(video_info)

    def _get_playlist_info(self, player_key):
        playlist_info = self._download_webpage(self._PLAYLIST_URL_TEMPLATE % player_key,
                                               player_key, u'Downloading playlist information')

        playlist_info = json.loads(playlist_info)['videoList']
        videos = [self._extract_video_info(video_info) for video_info in playlist_info['mediaCollectionDTO']['videoDTOs']]

        return self.playlist_result(videos, playlist_id=playlist_info['id'],
                                    playlist_title=playlist_info['mediaCollectionDTO']['displayName'])

    def _extract_video_info(self, video_info):
        renditions = video_info['renditions']
        renditions = sorted(renditions, key=lambda r: r['size'])
        best_format = renditions[-1]

        return {'id': video_info['id'],
                'title': video_info['displayName'],
                'url': best_format['defaultURL'], 
                'ext': 'mp4',
                'description': video_info.get('shortDescription'),
                'thumbnail': video_info.get('videoStillURL') or video_info.get('thumbnailURL'),
                'uploader': video_info.get('publisherName'),
                }
