from __future__ import unicode_literals

import re
import json
import time
import hmac
import binascii
import hashlib


from .subtitles import SubtitlesInfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    xpath_with_ns,
    unsmuggle_url,
)

_x = lambda p: xpath_with_ns(p, {'smil': 'http://www.w3.org/2005/SMIL21/Language'})


class ThePlatformIE(SubtitlesInfoExtractor):
    _VALID_URL = r'''(?x)
        (?:https?://(?:link|player)\.theplatform\.com/[sp]/(?P<provider_id>[^/]+)/
           (?P<config>(?:[^/\?]+/(?:swf|config)|onsite)/select/)?
         |theplatform:)(?P<id>[^/\?&]+)'''

    _TEST = {
        # from http://www.metacafe.com/watch/cb-e9I_cZgTgIPd/blackberrys_big_bold_z30/
        'url': 'http://link.theplatform.com/s/dJ5BDC/e9I_cZgTgIPd/meta.smil?format=smil&Tracking=true&mbr=true',
        'info_dict': {
            'id': 'e9I_cZgTgIPd',
            'ext': 'flv',
            'title': 'Blackberry\'s big, bold Z30',
            'description': 'The Z30 is Blackberry\'s biggest, baddest mobile messaging device yet.',
            'duration': 247,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    @staticmethod
    def _sign_url(url, sig_key, sig_secret, life=600, include_qs=False):
        flags = '10' if include_qs else '00'
        expiration_date = '%x' % (int(time.time()) + life)

        def str_to_hex(str):
            return binascii.b2a_hex(str.encode('ascii')).decode('ascii')

        def hex_to_str(hex):
            return binascii.a2b_hex(hex)

        relative_path = url.split('http://link.theplatform.com/s/')[1].split('?')[0]
        clear_text = hex_to_str(flags + expiration_date + str_to_hex(relative_path))
        checksum = hmac.new(sig_key.encode('ascii'), clear_text, hashlib.sha1).hexdigest()
        sig = flags + expiration_date + checksum + str_to_hex(sig_secret)
        return '%s&sig=%s' % (url, sig)

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        provider_id = mobj.group('provider_id')
        video_id = mobj.group('id')

        if not provider_id:
            provider_id = 'dJ5BDC'

        if mobj.group('config'):
            config_url = url + '&form=json'
            config_url = config_url.replace('swf/', 'config/')
            config_url = config_url.replace('onsite/', 'onsite/config/')
            config = self._download_json(config_url, video_id, 'Downloading config')
            smil_url = config['releaseUrl'] + '&format=SMIL&formats=MPEG4&manifest=f4m'
        else:
            smil_url = ('http://link.theplatform.com/s/{0}/{1}/meta.smil?'
                        'format=smil&mbr=true'.format(provider_id, video_id))

        sig = smuggled_data.get('sig')
        if sig:
            smil_url = self._sign_url(smil_url, sig['key'], sig['secret'])

        meta = self._download_xml(smil_url, video_id)
        try:
            error_msg = next(
                n.attrib['abstract']
                for n in meta.findall(_x('.//smil:ref'))
                if n.attrib.get('title') == 'Geographic Restriction')
        except StopIteration:
            pass
        else:
            raise ExtractorError(error_msg, expected=True)

        info_url = 'http://link.theplatform.com/s/{0}/{1}?format=preview'.format(provider_id, video_id)
        info_json = self._download_webpage(info_url, video_id)
        info = json.loads(info_json)

        subtitles = {}
        captions = info.get('captions')
        if isinstance(captions, list):
            for caption in captions:
                lang, src = caption.get('lang'), caption.get('src')
                if lang and src:
                    subtitles[lang] = src

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        subtitles = self.extract_subtitles(video_id, subtitles)

        head = meta.find(_x('smil:head'))
        body = meta.find(_x('smil:body'))

        f4m_node = body.find(_x('smil:seq//smil:video'))
        if f4m_node is not None and '.f4m' in f4m_node.attrib['src']:
            f4m_url = f4m_node.attrib['src']
            if 'manifest.f4m?' not in f4m_url:
                f4m_url += '?'
            # the parameters are from syfy.com, other sites may use others,
            # they also work for nbc.com
            f4m_url += '&g=UXWGVKRWHFSP&hdcore=3.0.3'
            formats = self._extract_f4m_formats(f4m_url, video_id)
        else:
            formats = []
            switch = body.find(_x('smil:switch'))
            if switch is not None:
                base_url = head.find(_x('smil:meta')).attrib['base']
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
            else:
                switch = body.find(_x('smil:seq//smil:switch'))
                for f in switch.findall(_x('smil:video')):
                    attr = f.attrib
                    vbr = int(attr['system-bitrate']) // 1000
                    ext = determine_ext(attr['src'])
                    if ext == 'once':
                        ext = 'mp4'
                    formats.append({
                        'format_id': compat_str(vbr),
                        'url': attr['src'],
                        'vbr': vbr,
                        'ext': ext,
                    })
            self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['title'],
            'subtitles': subtitles,
            'formats': formats,
            'description': info['description'],
            'thumbnail': info['defaultThumbnailUrl'],
            'duration': info['duration'] // 1000,
        }
