# encoding: utf-8

import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    find_xpath_attr,
    compat_urlparse,
    compat_str,
    compat_urllib_request,

    ExtractorError,
)


class BrightcoveIE(InfoExtractor):
    _VALID_URL = r'https?://.*brightcove\.com/(services|viewer).*\?(?P<query>.*)'
    _FEDERATED_URL_TEMPLATE = 'http://c.brightcove.com/services/viewer/htmlFederated?%s'
    _PLAYLIST_URL_TEMPLATE = 'http://c.brightcove.com/services/json/experience/runtime/?command=get_programming_for_experience&playerKey=%s'

    _TESTS = [
        {
            # From http://www.8tv.cat/8aldia/videos/xavier-sala-i-martin-aquesta-tarda-a-8-al-dia/
            u'url': u'http://c.brightcove.com/services/viewer/htmlFederated?playerID=1654948606001&flashID=myExperience&%40videoPlayer=2371591881001',
            u'file': u'2371591881001.mp4',
            u'md5': u'8eccab865181d29ec2958f32a6a754f5',
            u'note': u'Test Brightcove downloads and detection in GenericIE',
            u'info_dict': {
                u'title': u'Xavier Sala i Martín: “Un banc que no presta és un banc zombi que no serveix per a res”',
                u'uploader': u'8TV',
                u'description': u'md5:a950cc4285c43e44d763d036710cd9cd',
            }
        },
        {
            # From http://medianetwork.oracle.com/video/player/1785452137001
            u'url': u'http://c.brightcove.com/services/viewer/htmlFederated?playerID=1217746023001&flashID=myPlayer&%40videoPlayer=1785452137001',
            u'file': u'1785452137001.flv',
            u'info_dict': {
                u'title': u'JVMLS 2012: Arrays 2.0 - Opportunities and Challenges',
                u'description': u'John Rose speaks at the JVM Language Summit, August 1, 2012.',
                u'uploader': u'Oracle',
            },
        },
        {
            # From http://mashable.com/2013/10/26/thermoelectric-bracelet-lets-you-control-your-body-temperature/
            u'url': u'http://c.brightcove.com/services/viewer/federated_f9?&playerID=1265504713001&publisherID=AQ%7E%7E%2CAAABBzUwv1E%7E%2CxP-xFHVUstiMFlNYfvF4G9yFnNaqCw_9&videoID=2750934548001',
            u'info_dict': {
                u'id': u'2750934548001',
                u'ext': u'mp4',
                u'title': u'This Bracelet Acts as a Personal Thermostat',
                u'description': u'md5:547b78c64f4112766ccf4e151c20b6a0',
                u'uploader': u'Mashable',
            },
        },
    ]

    @classmethod
    def _build_brighcove_url(cls, object_str):
        """
        Build a Brightcove url from a xml string containing
        <object class="BrightcoveExperience">{params}</object>
        """

        # Fix up some stupid HTML, see https://github.com/rg3/youtube-dl/issues/1553
        object_str = re.sub(r'(<param name="[^"]+" value="[^"]+")>',
                            lambda m: m.group(1) + '/>', object_str)
        # Fix up some stupid XML, see https://github.com/rg3/youtube-dl/issues/1608
        object_str = object_str.replace(u'<--', u'<!--')

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
        linkBase = find_xpath_attr(object_doc, './param', 'name', 'linkBaseURL')
        if linkBase is not None:
            params['linkBaseURL'] = linkBase.attrib['value']
        data = compat_urllib_parse.urlencode(params)
        return cls._FEDERATED_URL_TEMPLATE % data

    @classmethod
    def _extract_brightcove_url(cls, webpage):
        """Try to extract the brightcove url from the wepbage, returns None
        if it can't be found
        """
        m_brightcove = re.search(
            r'<object[^>]+?class=([\'"])[^>]*?BrightcoveExperience.*?\1.+?</object>',
            webpage, re.DOTALL)
        if m_brightcove is not None:
            return cls._build_brighcove_url(m_brightcove.group())
        else:
            return None

    def _real_extract(self, url):
        # Change the 'videoId' and others field to '@videoPlayer'
        url = re.sub(r'(?<=[?&])(videoI(d|D)|bctid)', '%40videoPlayer', url)
        # Change bckey (used by bcove.me urls) to playerKey
        url = re.sub(r'(?<=[?&])bckey', 'playerKey', url)
        mobj = re.match(self._VALID_URL, url)
        query_str = mobj.group('query')
        query = compat_urlparse.parse_qs(query_str)

        videoPlayer = query.get('@videoPlayer')
        if videoPlayer:
            return self._get_video_info(videoPlayer[0], query_str, query)
        else:
            player_key = query['playerKey']
            return self._get_playlist_info(player_key[0])

    def _get_video_info(self, video_id, query_str, query):
        request_url = self._FEDERATED_URL_TEMPLATE % query_str
        req = compat_urllib_request.Request(request_url)
        linkBase = query.get('linkBaseURL')
        if linkBase is not None:
            req.add_header('Referer', linkBase[0])
        webpage = self._download_webpage(req, video_id)

        self.report_extraction(video_id)
        info = self._search_regex(r'var experienceJSON = ({.*?});', webpage, 'json')
        info = json.loads(info)['data']
        video_info = info['programmedContent']['videoPlayer']['mediaDTO']

        return self._extract_video_info(video_info)

    def _get_playlist_info(self, player_key):
        playlist_info = self._download_webpage(self._PLAYLIST_URL_TEMPLATE % player_key,
                                               player_key, u'Downloading playlist information')

        json_data = json.loads(playlist_info)
        if 'videoList' not in json_data:
            raise ExtractorError(u'Empty playlist')
        playlist_info = json_data['videoList']
        videos = [self._extract_video_info(video_info) for video_info in playlist_info['mediaCollectionDTO']['videoDTOs']]

        return self.playlist_result(videos, playlist_id=playlist_info['id'],
                                    playlist_title=playlist_info['mediaCollectionDTO']['displayName'])

    def _extract_video_info(self, video_info):
        info = {
            'id': compat_str(video_info['id']),
            'title': video_info['displayName'],
            'description': video_info.get('shortDescription'),
            'thumbnail': video_info.get('videoStillURL') or video_info.get('thumbnailURL'),
            'uploader': video_info.get('publisherName'),
        }

        renditions = video_info.get('renditions')
        if renditions:
            renditions = sorted(renditions, key=lambda r: r['size'])
            info['formats'] = [{
                'url': rend['defaultURL'],
                'height': rend.get('frameHeight'),
                'width': rend.get('frameWidth'),
            } for rend in renditions]
        elif video_info.get('FLVFullLengthURL') is not None:
            info.update({
                'url': video_info['FLVFullLengthURL'],
            })
        else:
            raise ExtractorError(u'Unable to extract video url for %s' % info['id'])
        return info
