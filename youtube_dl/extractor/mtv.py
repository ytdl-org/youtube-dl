import re
import socket
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_request,

    ExtractorError,
)


class MTVIE(InfoExtractor):
    _VALID_URL = r'^(?P<proto>https?://)?(?:www\.)?mtv\.com/videos/[^/]+/(?P<videoid>[0-9]+)/[^/]+$'
    _WORKING = False

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        if not mobj.group('proto'):
            url = 'http://' + url
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)

        # Some videos come from Vevo.com
        m_vevo = re.search(r'isVevoVideo = true;.*?vevoVideoId = "(.*?)";',
                           webpage, re.DOTALL)
        if m_vevo:
            vevo_id = m_vevo.group(1);
            self.to_screen(u'Vevo video detected: %s' % vevo_id)
            return self.url_result('vevo:%s' % vevo_id, ie='Vevo')

        #song_name = self._html_search_regex(r'<meta name="mtv_vt" content="([^"]+)"/>',
        #    webpage, u'song name', fatal=False)

        video_title = self._html_search_regex(r'<meta name="mtv_an" content="([^"]+)"/>',
            webpage, u'title')

        mtvn_uri = self._html_search_regex(r'<meta name="mtvn_uri" content="([^"]+)"/>',
            webpage, u'mtvn_uri', fatal=False)

        content_id = self._search_regex(r'MTVN.Player.defaultPlaylistId = ([0-9]+);',
            webpage, u'content id', fatal=False)

        videogen_url = 'http://www.mtv.com/player/includes/mediaGen.jhtml?uri=' + mtvn_uri + '&id=' + content_id + '&vid=' + video_id + '&ref=www.mtvn.com&viewUri=' + mtvn_uri
        self.report_extraction(video_id)
        request = compat_urllib_request.Request(videogen_url)
        try:
            metadataXml = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video metadata: %s' % compat_str(err))

        mdoc = xml.etree.ElementTree.fromstring(metadataXml)
        renditions = mdoc.findall('.//rendition')

        # For now, always pick the highest quality.
        rendition = renditions[-1]

        try:
            _,_,ext = rendition.attrib['type'].partition('/')
            format = ext + '-' + rendition.attrib['width'] + 'x' + rendition.attrib['height'] + '_' + rendition.attrib['bitrate']
            video_url = rendition.find('./src').text
        except KeyError:
            raise ExtractorError('Invalid rendition field.')

        info = {
            'id': video_id,
            'url': video_url,
            'upload_date': None,
            'title': video_title,
            'ext': ext,
            'format': format,
        }

        return [info]
