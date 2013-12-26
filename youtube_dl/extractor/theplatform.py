import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    xpath_with_ns,
)

_x = lambda p: xpath_with_ns(p, {'smil': 'http://www.w3.org/2005/SMIL21/Language'})


class ThePlatformIE(InfoExtractor):
    _VALID_URL = r'(?:https?://link\.theplatform\.com/s/[^/]+/|theplatform:)(?P<id>[^/\?]+)'

    _TEST = {
        # from http://www.metacafe.com/watch/cb-e9I_cZgTgIPd/blackberrys_big_bold_z30/
        u'url': u'http://link.theplatform.com/s/dJ5BDC/e9I_cZgTgIPd/meta.smil?format=smil&Tracking=true&mbr=true',
        u'info_dict': {
            u'id': u'e9I_cZgTgIPd',
            u'ext': u'flv',
            u'title': u'Blackberry\'s big, bold Z30',
            u'description': u'The Z30 is Blackberry\'s biggest, baddest mobile messaging device yet.',
            u'duration': 247,
        },
        u'params': {
            # rtmp download
            u'skip_download': True,
        },
    }

    def _get_info(self, video_id):
        smil_url = ('http://link.theplatform.com/s/dJ5BDC/{0}/meta.smil?'
            'format=smil&mbr=true'.format(video_id))
        meta = self._download_xml(smil_url, video_id)

        try:
            error_msg = next(
                n.attrib['abstract']
                for n in meta.findall(_x('.//smil:ref'))
                if n.attrib.get('title') == u'Geographic Restriction')
        except StopIteration:
            pass
        else:
            raise ExtractorError(error_msg, expected=True)

        info_url = 'http://link.theplatform.com/s/dJ5BDC/{0}?format=preview'.format(video_id)
        info_json = self._download_webpage(info_url, video_id)
        info = json.loads(info_json)

        head = meta.find(_x('smil:head'))
        body = meta.find(_x('smil:body'))
        base_url = head.find(_x('smil:meta')).attrib['base']
        switch = body.find(_x('smil:switch'))
        formats = []
        for f in switch.findall(_x('smil:video')):
            attr = f.attrib
            width = int(attr['width'])
            height = int(attr['height'])
            vbr = int(attr['system-bitrate']) // 1000
            format_id = '%dx%d_%dk' % (width, height, vbr)
            formats.append({
                'format_id': format_id,
                'url': base_url,
                'play_path': 'mp4:' + attr['src'],
                'ext': 'flv',
                'width': width,
                'height': height,
                'vbr': vbr,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['title'],
            'formats': formats,
            'description': info['description'],
            'thumbnail': info['defaultThumbnailUrl'],
            'duration': info['duration']//1000,
        }
        
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        return self._get_info(video_id)
