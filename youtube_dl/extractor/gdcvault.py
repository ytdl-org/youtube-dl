from __future__ import unicode_literals

import re
import json
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import unified_strdate


class GDCVaultIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gdcvault\.com/play/(?P<id>\d+)/(?P<name>(\w|-)+)'
    _TESTS = [
        {
            u'url': u'http://www.gdcvault.com/play/1015683/Embracing-the-Dark-Art-of',
            u'md5': u'05763e5edd1a74776999a12b02ee1c4e',
            u'info_dict': {
                u"id": u"1015683",
                u"ext": u"flv",
                u"title": u"Embracing the Dark Art of Mathematical Modeling in AI"
            }
        },
        {
            u'url': u'http://www.gdcvault.com/play/1019721/Doki-Doki-Universe-Sweet-Simple',
            u'md5': u'7ce8388f544c88b7ac11c7ab1b593704',
            u'info_dict': {
                u"id": u"1019721",
                u"ext": u"mp4",
                u"title": u"Doki-Doki Universe: Sweet, Simple and Genuine (GDC Next 10)"
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://www.gdcvault.com/play/' + video_id

        start_page = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        xml_root = self._html_search_regex(r'<iframe src="(?P<xml_root>.*?)player.html.*?".*?</iframe>', start_page, 'xml root')
        xml_name = self._html_search_regex(r'<iframe src=".*?\?xml=(?P<xml_file>.+?\.xml).*?".*?</iframe>', start_page, 'xml filename', None, False)
        if xml_name is None:
            # Fallback to the older format
            xml_name = self._html_search_regex(r'<iframe src=".*?\?xmlURL=xml/(?P<xml_file>.+?\.xml).*?".*?</iframe>', start_page, 'xml filename')

        xml_decription_url = xml_root + 'xml/' + xml_name

        xml_description = self._download_xml(xml_decription_url, video_id)

        video_title = xml_description.find('./metadata/title').text

        video_details = {
            'id': video_id,
            'title': video_title,
        }
        video_formats = []

        mp4_video = xml_description.find('./metadata/mp4video')
        if mp4_video is not None:
            mobj = re.match(r'(?P<root>https?://.*?/).*', mp4_video.text)
            video_root = mobj.group('root')
            formats = xml_description.findall('./metadata/MBRVideos/MBRVideo')
            for format in formats:
                mobj = re.match(r'mp4\:(?P<path>.*)', format.find('streamName').text)
                url = video_root + mobj.group('path')
                vbr = format.find('bitrate').text
                video_formats.append({
                    'url': url,
                    'vbr': int(vbr),
                })
            video_details['formats'] = video_formats
        else:
            # Fallback to flv
            akami_url = xml_description.find('./metadata/akamaiHost').text
            slide_video_path = xml_description.find('./metadata/slideVideo').text
            video_formats.append({
                    'url': 'rtmp://' + akami_url + '/' + slide_video_path,
                    'format_note': 'slide deck video',
                    'quality': -2,
                    'preference': -2,
                    'format_id': 'slides',
                })
            speaker_video_path = xml_description.find('./metadata/speakerVideo').text
            video_formats.append({
                    'url': 'rtmp://' + akami_url + '/' + speaker_video_path,
                    'format_note': 'speaker video',
                    'quality': -1,
                    'preference': -1,
                    'format_id': 'speaker',
                })

        return [{
            'id': video_id,
            'title': video_title,
            'formats': video_formats,
        }]
