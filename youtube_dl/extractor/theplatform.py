# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import time
import hmac
import binascii
import hashlib


from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    xpath_with_ns,
    unsmuggle_url,
    int_or_none,
    url_basename,
    float_or_none,
)

default_ns = 'http://www.w3.org/2005/SMIL21/Language'
_x = lambda p: xpath_with_ns(p, {'smil': default_ns})


class ThePlatformBaseIE(InfoExtractor):
    def _extract_theplatform_smil(self, smil_url, video_id, note='Downloading SMIL data'):
        meta = self._download_xml(smil_url, video_id, note=note)
        try:
            error_msg = next(
                n.attrib['abstract']
                for n in meta.findall(_x('.//smil:ref'))
                if n.attrib.get('title') == 'Geographic Restriction' or n.attrib.get('title') == 'Expired')
        except StopIteration:
            pass
        else:
            raise ExtractorError(error_msg, expected=True)

        formats = self._parse_smil_formats(
            meta, smil_url, video_id, namespace=default_ns,
            # the parameters are from syfy.com, other sites may use others,
            # they also work for nbc.com
            f4m_params={'g': 'UXWGVKRWHFSP', 'hdcore': '3.0.3'},
            transform_rtmp_url=lambda streamer, src: (streamer, 'mp4:' + src))

        for _format in formats:
            ext = determine_ext(_format['url'])
            if ext == 'once':
                _format['ext'] = 'mp4'

        self._sort_formats(formats)

        subtitles = self._parse_smil_subtitles(meta, default_ns)

        return formats, subtitles

    def get_metadata(self, path, video_id):
        info_url = 'http://link.theplatform.com/s/%s?format=preview' % path
        info = self._download_json(info_url, video_id)

        subtitles = {}
        captions = info.get('captions')
        if isinstance(captions, list):
            for caption in captions:
                lang, src, mime = caption.get('lang', 'en'), caption.get('src'), caption.get('type')
                subtitles[lang] = [{
                    'ext': 'srt' if mime == 'text/srt' else 'ttml',
                    'url': src,
                }]

        return {
            'title': info['title'],
            'subtitles': subtitles,
            'description': info['description'],
            'thumbnail': info['defaultThumbnailUrl'],
            'duration': int_or_none(info.get('duration'), 1000),
        }


class ThePlatformIE(ThePlatformBaseIE):
    _VALID_URL = r'''(?x)
        (?:https?://(?:link|player)\.theplatform\.com/[sp]/(?P<provider_id>[^/]+)/
           (?:(?P<media>(?:[^/]+/)+select/media/)|(?P<config>(?:[^/\?]+/(?:swf|config)|onsite)/select/))?
         |theplatform:)(?P<id>[^/\?&]+)'''

    _TESTS = [{
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
    }, {
        # from http://www.cnet.com/videos/tesla-model-s-a-second-step-towards-a-cleaner-motoring-future/
        'url': 'http://link.theplatform.com/s/kYEXFC/22d_qsQ6MIRT',
        'info_dict': {
            'id': '22d_qsQ6MIRT',
            'ext': 'flv',
            'description': 'md5:ac330c9258c04f9d7512cf26b9595409',
            'title': 'Tesla Model S: A second step towards a cleaner motoring future',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'https://player.theplatform.com/p/D6x-PC/pulse_preview/embed/select/media/yMBg9E8KFxZD',
        'info_dict': {
            'id': 'yMBg9E8KFxZD',
            'ext': 'mp4',
            'description': 'md5:644ad9188d655b742f942bf2e06b002d',
            'title': 'HIGHLIGHTS: USA bag first ever series Cup win',
        }
    }, {
        'url': 'http://player.theplatform.com/p/NnzsPC/widget/select/media/4Y0TlYUr_ZT7',
        'only_matching': True,
    }, {
        'url': 'http://player.theplatform.com/p/2E2eJC/nbcNewsOffsite?guid=tdy_or_siri_150701',
        'md5': '734f3790fb5fc4903da391beeebc4836',
        'info_dict': {
            'id': 'tdy_or_siri_150701',
            'ext': 'mp4',
            'title': 'iPhone Siri’s sassy response to a math question has people talking',
            'description': 'md5:a565d1deadd5086f3331d57298ec6333',
            'duration': 83.0,
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1435752600,
            'upload_date': '20150701',
            'categories': ['Today/Shows/Orange Room', 'Today/Sections/Money', 'Today/Topics/Tech', "Today/Topics/Editor's picks"],
        },
    }]

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

        path = provider_id
        if mobj.group('media'):
            path += '/media'
        path += '/' + video_id

        qs_dict = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        if 'guid' in qs_dict:
            webpage = self._download_webpage(url, video_id)
            scripts = re.findall(r'<script[^>]+src="([^"]+)"', webpage)
            feed_id = None
            # feed id usually locates in the last script.
            # Seems there's no pattern for the interested script filename, so
            # I try one by one
            for script in reversed(scripts):
                feed_script = self._download_webpage(script, video_id, 'Downloading feed script')
                feed_id = self._search_regex(r'defaultFeedId\s*:\s*"([^"]+)"', feed_script, 'default feed id', default=None)
                if feed_id is not None:
                    break
            if feed_id is None:
                raise ExtractorError('Unable to find feed id')
            return self.url_result('http://feed.theplatform.com/f/%s/%s?byGuid=%s' % (
                provider_id, feed_id, qs_dict['guid'][0]))

        if smuggled_data.get('force_smil_url', False):
            smil_url = url
        elif mobj.group('config'):
            config_url = url + '&form=json'
            config_url = config_url.replace('swf/', 'config/')
            config_url = config_url.replace('onsite/', 'onsite/config/')
            config = self._download_json(config_url, video_id, 'Downloading config')
            if 'releaseUrl' in config:
                release_url = config['releaseUrl']
            else:
                release_url = 'http://link.theplatform.com/s/%s?mbr=true' % path
            smil_url = release_url + '&format=SMIL&formats=MPEG4&manifest=f4m'
        else:
            smil_url = 'http://link.theplatform.com/s/%s/meta.smil?format=smil&mbr=true' % path

        sig = smuggled_data.get('sig')
        if sig:
            smil_url = self._sign_url(smil_url, sig['key'], sig['secret'])

        formats, subtitles = self._extract_theplatform_smil(smil_url, video_id)

        ret = self.get_metadata(path, video_id)
        combined_subtitles = self._merge_subtitles(ret.get('subtitles', {}), subtitles)
        ret.update({
            'id': video_id,
            'formats': formats,
            'subtitles': combined_subtitles,
        })

        return ret


class ThePlatformFeedIE(ThePlatformBaseIE):
    _URL_TEMPLATE = '%s//feed.theplatform.com/f/%s/%s?form=json&byGuid=%s'
    _VALID_URL = r'https?://feed\.theplatform\.com/f/(?P<provider_id>[^/]+)/(?P<feed_id>[^?/]+)\?(?:[^&]+&)*byGuid=(?P<id>[a-zA-Z0-9_]+)'
    _TEST = {
        # From http://player.theplatform.com/p/7wvmTC/MSNBCEmbeddedOffSite?guid=n_hardball_5biden_140207
        'url': 'http://feed.theplatform.com/f/7wvmTC/msnbc_video-p-test?form=json&pretty=true&range=-40&byGuid=n_hardball_5biden_140207',
        'md5': '22d2b84f058d3586efcd99e57d59d314',
        'info_dict': {
            'id': 'n_hardball_5biden_140207',
            'ext': 'mp4',
            'title': 'The Biden factor: will Joe run in 2016?',
            'description': 'Could Vice President Joe Biden be preparing a 2016 campaign? Mark Halperin and Sam Stein weigh in.',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20140208',
            'timestamp': 1391824260,
            'duration': 467.0,
            'categories': ['MSNBC/Issues/Democrats', 'MSNBC/Issues/Elections/Election 2016'],
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        provider_id = mobj.group('provider_id')
        feed_id = mobj.group('feed_id')

        real_url = self._URL_TEMPLATE % (self.http_scheme(), provider_id, feed_id, video_id)
        feed = self._download_json(real_url, video_id)
        entry = feed['entries'][0]

        formats = []
        subtitles = {}
        first_video_id = None
        duration = None
        for item in entry['media$content']:
            smil_url = item['plfile$url'] + '&format=SMIL&Tracking=true&Embedded=true&formats=MPEG4,F4M'
            cur_video_id = url_basename(smil_url)
            if first_video_id is None:
                first_video_id = cur_video_id
                duration = float_or_none(item.get('plfile$duration'))
            cur_formats, cur_subtitles = self._extract_theplatform_smil(smil_url, video_id, 'Downloading SMIL data for %s' % cur_video_id)
            formats.extend(cur_formats)
            subtitles = self._merge_subtitles(subtitles, cur_subtitles)

        self._sort_formats(formats)

        thumbnails = [{
            'url': thumbnail['plfile$url'],
            'width': int_or_none(thumbnail.get('plfile$width')),
            'height': int_or_none(thumbnail.get('plfile$height')),
        } for thumbnail in entry.get('media$thumbnails', [])]

        timestamp = int_or_none(entry.get('media$availableDate'), scale=1000)
        categories = [item['media$name'] for item in entry.get('media$categories', [])]

        ret = self.get_metadata('%s/%s' % (provider_id, first_video_id), video_id)
        subtitles = self._merge_subtitles(subtitles, ret['subtitles'])
        ret.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'duration': duration,
            'timestamp': timestamp,
            'categories': categories,
        })

        return ret
