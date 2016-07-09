# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    int_or_none,
    parse_duration,
    parse_iso8601,
    xpath_text,
)


class MDRIE(InfoExtractor):
    IE_DESC = 'MDR.DE and KiKA'
    _VALID_URL = r'https?://(?:www\.)?(?:mdr|kika)\.de/(?:.*)/[a-z]+-?(?P<id>\d+)(?:_.+?)?\.html'

    _TESTS = [{
        # MDR regularly deletes its videos
        'url': 'http://www.mdr.de/fakt/video189002.html',
        'only_matching': True,
    }, {
        # audio
        'url': 'http://www.mdr.de/kultur/audio1312272_zc-15948bad_zs-86171fdd.html',
        'md5': '64c4ee50f0a791deb9479cd7bbe9d2fa',
        'info_dict': {
            'id': '1312272',
            'ext': 'mp3',
            'title': 'Feuilleton vom 30. Oktober 2015',
            'duration': 250,
            'uploader': 'MITTELDEUTSCHER RUNDFUNK',
        },
    }, {
        'url': 'http://www.kika.de/baumhaus/videos/video19636.html',
        'md5': '4930515e36b06c111213e80d1e4aad0e',
        'info_dict': {
            'id': '19636',
            'ext': 'mp4',
            'title': 'Baumhaus vom 30. Oktober 2015',
            'duration': 134,
            'uploader': 'KIKA',
        },
    }, {
        'url': 'http://www.kika.de/sendungen/einzelsendungen/weihnachtsprogramm/videos/video8182.html',
        'md5': '5fe9c4dd7d71e3b238f04b8fdd588357',
        'info_dict': {
            'id': '8182',
            'ext': 'mp4',
            'title': 'Beutolomäus und der geheime Weihnachtswunsch',
            'description': 'md5:b69d32d7b2c55cbe86945ab309d39bbd',
            'timestamp': 1450950000,
            'upload_date': '20151224',
            'duration': 4628,
            'uploader': 'KIKA',
        },
    }, {
        'url': 'http://www.kika.de/baumhaus/sendungen/video19636_zc-fea7f8a0_zs-4bf89c60.html',
        'only_matching': True,
    }, {
        'url': 'http://www.kika.de/sendungen/einzelsendungen/weihnachtsprogramm/einzelsendung2534.html',
        'only_matching': True,
    }, {
        'url': 'http://www.mdr.de/mediathek/mdr-videos/a/video-1334.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        data_url = self._search_regex(
            r'(?:dataURL|playerXml(?:["\'])?)\s*:\s*(["\'])(?P<url>.+/(?:video|audio)-?[0-9]+-avCustom\.xml)\1',
            webpage, 'data url', group='url').replace('\/', '/')

        doc = self._download_xml(
            compat_urlparse.urljoin(url, data_url), video_id)

        title = xpath_text(doc, ['./title', './broadcast/broadcastName'], 'title', fatal=True)

        formats = []
        processed_urls = []
        for asset in doc.findall('./assets/asset'):
            for source in (
                    'progressiveDownload',
                    'dynamicHttpStreamingRedirector',
                    'adaptiveHttpStreamingRedirector'):
                url_el = asset.find('./%sUrl' % source)
                if url_el is None:
                    continue

                video_url = url_el.text
                if video_url in processed_urls:
                    continue

                processed_urls.append(video_url)

                vbr = int_or_none(xpath_text(asset, './bitrateVideo', 'vbr'), 1000)
                abr = int_or_none(xpath_text(asset, './bitrateAudio', 'abr'), 1000)

                ext = determine_ext(url_el.text)
                if ext == 'm3u8':
                    url_formats = self._extract_m3u8_formats(
                        video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        preference=0, m3u8_id='HLS', fatal=False)
                elif ext == 'f4m':
                    url_formats = self._extract_f4m_formats(
                        video_url + '?hdcore=3.7.0&plugin=aasp-3.7.0.39.44', video_id,
                        preference=0, f4m_id='HDS', fatal=False)
                else:
                    media_type = xpath_text(asset, './mediaType', 'media type', default='MP4')
                    vbr = int_or_none(xpath_text(asset, './bitrateVideo', 'vbr'), 1000)
                    abr = int_or_none(xpath_text(asset, './bitrateAudio', 'abr'), 1000)
                    filesize = int_or_none(xpath_text(asset, './fileSize', 'file size'))

                    f = {
                        'url': video_url,
                        'format_id': '%s-%d' % (media_type, vbr or abr),
                        'filesize': filesize,
                        'abr': abr,
                        'preference': 1,
                    }

                    if vbr:
                        width = int_or_none(xpath_text(asset, './frameWidth', 'width'))
                        height = int_or_none(xpath_text(asset, './frameHeight', 'height'))
                        f.update({
                            'vbr': vbr,
                            'width': width,
                            'height': height,
                        })

                    url_formats = [f]

                if not url_formats:
                    continue

                if not vbr:
                    for f in url_formats:
                        abr = f.get('tbr') or abr
                        if 'tbr' in f:
                            del f['tbr']
                        f.update({
                            'abr': abr,
                            'vcodec': 'none',
                        })

                formats.extend(url_formats)

        self._sort_formats(formats)

        description = xpath_text(doc, './broadcast/broadcastDescription', 'description')
        timestamp = parse_iso8601(
            xpath_text(
                doc, [
                    './broadcast/broadcastDate',
                    './broadcast/broadcastStartDate',
                    './broadcast/broadcastEndDate'],
                'timestamp', default=None))
        duration = parse_duration(xpath_text(doc, './duration', 'duration'))
        uploader = xpath_text(doc, './rights', 'uploader')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'duration': duration,
            'uploader': uploader,
            'formats': formats,
        }
