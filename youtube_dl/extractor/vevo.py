from __future__ import unicode_literals

import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_HTTPError,
    ExtractorError,
)


class VevoIE(InfoExtractor):
    """
    Accepts urls from vevo.com or in the format 'vevo:{id}'
    (currently used by MTVIE)
    """
    _VALID_URL = r'''(?x)
        (?:https?://www\.vevo\.com/watch/(?:[^/]+/[^/]+/)?|
           https?://cache\.vevo\.com/m/html/embed\.html\?video=|
           https?://videoplayer\.vevo\.com/embed/embedded\?videoId=|
           vevo:)
        (?P<id>[^&?#]+)'''

    _TESTS = [{
        'url': 'http://www.vevo.com/watch/hurts/somebody-to-die-for/GB1101300280',
        "md5": "06bea460acb744eab74a9d7dcb4bfd61",
        'info_dict': {
            'id': 'GB1101300280',
            'ext': 'mp4',
            "upload_date": "20130624",
            "uploader": "Hurts",
            "title": "Somebody to Die For",
            "duration": 230.12,
            "width": 1920,
            "height": 1080,
            # timestamp and upload_date are often incorrect; seem to change randomly
            'timestamp': int,
        }
    }, {
        'note': 'v3 SMIL format',
        'url': 'http://www.vevo.com/watch/cassadee-pope/i-wish-i-could-break-your-heart/USUV71302923',
        'md5': '893ec0e0d4426a1d96c01de8f2bdff58',
        'info_dict': {
            'id': 'USUV71302923',
            'ext': 'mp4',
            'upload_date': '20140219',
            'uploader': 'Cassadee Pope',
            'title': 'I Wish I Could Break Your Heart',
            'duration': 226.101,
            'age_limit': 0,
            'timestamp': int,
        }
    }, {
        'note': 'Age-limited video',
        'url': 'https://www.vevo.com/watch/justin-timberlake/tunnel-vision-explicit/USRV81300282',
        'info_dict': {
            'id': 'USRV81300282',
            'ext': 'mp4',
            'age_limit': 18,
            'title': 'Tunnel Vision (Explicit)',
            'uploader': 'Justin Timberlake',
            'upload_date': 're:2013070[34]',
            'timestamp': int,
        },
        'params': {
            'skip_download': 'true',
        }
    }]
    _SMIL_BASE_URL = 'http://smil.lvl3.vevo.com/'

    def _formats_from_json(self, video_info):
        last_version = {'version': -1}
        for version in video_info['videoVersions']:
            # These are the HTTP downloads, other types are for different manifests
            if version['sourceType'] == 2:
                if version['version'] > last_version['version']:
                    last_version = version
        if last_version['version'] == -1:
            raise ExtractorError('Unable to extract last version of the video')

        renditions = xml.etree.ElementTree.fromstring(last_version['data'])
        formats = []
        # Already sorted from worst to best quality
        for rend in renditions.findall('rendition'):
            attr = rend.attrib
            format_note = '%(videoCodec)s@%(videoBitrate)4sk, %(audioCodec)s@%(audioBitrate)3sk' % attr
            formats.append({
                'url': attr['url'],
                'format_id': attr['name'],
                'format_note': format_note,
                'height': int(attr['frameheight']),
                'width': int(attr['frameWidth']),
            })
        return formats

    def _formats_from_smil(self, smil_xml):
        formats = []
        smil_doc = xml.etree.ElementTree.fromstring(smil_xml.encode('utf-8'))
        els = smil_doc.findall('.//{http://www.w3.org/2001/SMIL20/Language}video')
        for el in els:
            src = el.attrib['src']
            m = re.match(r'''(?xi)
                (?P<ext>[a-z0-9]+):
                (?P<path>
                    [/a-z0-9]+     # The directory and main part of the URL
                    _(?P<cbr>[0-9]+)k
                    _(?P<width>[0-9]+)x(?P<height>[0-9]+)
                    _(?P<vcodec>[a-z0-9]+)
                    _(?P<vbr>[0-9]+)
                    _(?P<acodec>[a-z0-9]+)
                    _(?P<abr>[0-9]+)
                    \.[a-z0-9]+  # File extension
                )''', src)
            if not m:
                continue

            format_url = self._SMIL_BASE_URL + m.group('path')
            formats.append({
                'url': format_url,
                'format_id': 'SMIL_' + m.group('cbr'),
                'vcodec': m.group('vcodec'),
                'acodec': m.group('acodec'),
                'vbr': int(m.group('vbr')),
                'abr': int(m.group('abr')),
                'ext': m.group('ext'),
                'width': int(m.group('width')),
                'height': int(m.group('height')),
            })
        return formats

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        json_url = 'http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc=%s' % video_id
        video_info = self._download_json(json_url, video_id)['video']

        formats = self._formats_from_json(video_info)

        is_explicit = video_info.get('isExplicit')
        if is_explicit is True:
            age_limit = 18
        elif is_explicit is False:
            age_limit = 0
        else:
            age_limit = None

        # Download SMIL
        smil_blocks = sorted((
            f for f in video_info['videoVersions']
            if f['sourceType'] == 13),
            key=lambda f: f['version'])

        smil_url = '%s/Video/V2/VFILE/%s/%sr.smil' % (
            self._SMIL_BASE_URL, video_id, video_id.lower())
        if smil_blocks:
            smil_url_m = self._search_regex(
                r'url="([^"]+)"', smil_blocks[-1]['data'], 'SMIL URL',
                fatal=False)
            if smil_url_m is not None:
                smil_url = smil_url_m

        try:
            smil_xml = self._download_webpage(smil_url, video_id,
                                              'Downloading SMIL info')
            formats.extend(self._formats_from_smil(smil_xml))
        except ExtractorError as ee:
            if not isinstance(ee.cause, compat_HTTPError):
                raise
            self._downloader.report_warning(
                'Cannot download SMIL information, falling back to JSON ..')

        timestamp_ms = int(self._search_regex(
            r'/Date\((\d+)\)/', video_info['launchDate'], 'launch date'))

        return {
            'id': video_id,
            'title': video_info['title'],
            'formats': formats,
            'thumbnail': video_info['imageUrl'],
            'timestamp': timestamp_ms // 1000,
            'uploader': video_info['mainArtists'][0]['artistName'],
            'duration': video_info['duration'],
            'age_limit': age_limit,
        }
