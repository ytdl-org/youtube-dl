import re
import socket
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse_urlparse,
    compat_urllib_request,

    ExtractorError,
)


class CollegeHumorIE(InfoExtractor):
    _WORKING = False
    _VALID_URL = r'^(?:https?://)?(?:www\.)?collegehumor\.com/video/(?P<videoid>[0-9]+)/(?P<shorttitle>.*)$'

    def report_manifest(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Downloading XML manifest' % video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('videoid')

        info = {
            'id': video_id,
            'uploader': None,
            'upload_date': None,
        }

        self.report_extraction(video_id)
        xmlUrl = 'http://www.collegehumor.com/moogaloop/video/' + video_id
        try:
            metaXml = compat_urllib_request.urlopen(xmlUrl).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video info XML: %s' % compat_str(err))

        mdoc = xml.etree.ElementTree.fromstring(metaXml)
        try:
            videoNode = mdoc.findall('./video')[0]
            info['description'] = videoNode.findall('./description')[0].text
            info['title'] = videoNode.findall('./caption')[0].text
            info['thumbnail'] = videoNode.findall('./thumbnail')[0].text
            manifest_url = videoNode.findall('./file')[0].text
        except IndexError:
            raise ExtractorError(u'Invalid metadata XML file')

        manifest_url += '?hdcore=2.10.3'
        self.report_manifest(video_id)
        try:
            manifestXml = compat_urllib_request.urlopen(manifest_url).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video info XML: %s' % compat_str(err))

        adoc = xml.etree.ElementTree.fromstring(manifestXml)
        try:
            media_node = adoc.findall('./{http://ns.adobe.com/f4m/1.0}media')[0]
            node_id = media_node.attrib['url']
            video_id = adoc.findall('./{http://ns.adobe.com/f4m/1.0}id')[0].text
        except IndexError as err:
            raise ExtractorError(u'Invalid manifest file')

        url_pr = compat_urllib_parse_urlparse(manifest_url)
        url = url_pr.scheme + '://' + url_pr.netloc + '/z' + video_id[:-2] + '/' + node_id + 'Seg1-Frag1'

        info['url'] = url
        info['ext'] = 'f4f'
        return [info]
