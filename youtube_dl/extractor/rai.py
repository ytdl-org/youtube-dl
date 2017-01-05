# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    determine_ext,
    find_xpath_attr,
    fix_xml_ampersands,
    int_or_none,
    parse_duration,
    unified_strdate,
    update_url_query,
    xpath_text,
)


class RaiBaseIE(InfoExtractor):
    def _extract_relinker_formats(self, relinker_url, video_id):
        formats = []

        for platform in ('mon', 'flash', 'native'):
            relinker = self._download_xml(
                relinker_url, video_id,
                note='Downloading XML metadata for platform %s' % platform,
                transform_source=fix_xml_ampersands,
                query={'output': 45, 'pl': platform},
                headers=self.geo_verification_headers())

            media_url = find_xpath_attr(relinker, './url', 'type', 'content').text
            if media_url == 'http://download.rai.it/video_no_available.mp4':
                self.raise_geo_restricted()

            ext = determine_ext(media_url)
            if (ext == 'm3u8' and platform != 'mon') or (ext == 'f4m' and platform != 'flash'):
                continue

            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif ext == 'f4m':
                manifest_url = update_url_query(
                    media_url.replace('manifest#live_hds.f4m', 'manifest.f4m'),
                    {'hdcore': '3.7.0', 'plugin': 'aasp-3.7.0.39.44'})
                formats.extend(self._extract_f4m_formats(
                    manifest_url, video_id, f4m_id='hds', fatal=False))
            else:
                bitrate = int_or_none(xpath_text(relinker, 'bitrate'))
                formats.append({
                    'url': media_url,
                    'tbr': bitrate if bitrate > 0 else None,
                    'format_id': 'http-%d' % bitrate if bitrate > 0 else 'http',
                })

        return formats


class RaiPlayIE(RaiBaseIE):
    _VALID_URL = r'https?://(?:www\.)?raiplay\.it/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})\.html'
    _TESTS = [{
        'url': 'http://www.raiplay.it/video/2016/10/La-Casa-Bianca-e06118bb-59a9-4636-b914-498e4cfd2c66.html?source=twitter',
        'md5': '340aa3b7afb54bfd14a8c11786450d76',
        'info_dict': {
            'id': 'e06118bb-59a9-4636-b914-498e4cfd2c66',
            'ext': 'mp4',
            'title': 'La Casa Bianca',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 're:^Rai.+',
            'description': 're:^[A-Za-z]+'
        }
    }, {
        'url': 'http://www.raiplay.it/video/2016/11/gazebotraindesi-efebe701-969c-4593-92f3-285f0d1ce750.html?',
        'md5': 'ed4da3d70ccf8129a33ab16b34d20ab8',
        'info_dict': {
            'id': 'efebe701-969c-4593-92f3-285f0d1ce750',
            'ext': 'mp4',
            'title': '#gazebotraindesi',
            'thumbnail': 're:^https?://.*\.png$',
            'uploader': 're:^Rai.+',
            'description': 're:^[A-Za-z]+'
        }
    }, {
        'url': 'http://www.raiplay.it/video/2014/04/Report-del-07042014-cb27157f-9dd0-4aee-b788-b1f67643a391.html',
        'md5': '8970abf8caf8aef4696e7b1f2adfc696',
        'info_dict': {
            'id': 'cb27157f-9dd0-4aee-b788-b1f67643a391',
            'ext': 'mp4',
            'title': 'Report del 07/04/2014',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 're:^Rai.+',
            'description': 're:^[A-Za-z]+'
        }
    }]
    _RESOLUTION = '600x400'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        canonical_url = self._og_search_url(webpage)

        media = self._download_json('%s?json' % canonical_url,
                                    video_id, 'Downloading video JSON')

        thumbnails = []
        if 'images' in media:
            for _, value in media.get('images').items():
                if value:
                    thumbnails.append({
                        'url': value.replace('[RESOLUTION]', self._RESOLUTION)
                    })

        formats = None
        duration = None
        if 'video' in media:
            formats
            video = media.get('video')
            duration = parse_duration(video.get('duration')),
            formats = self._extract_relinker_formats(video.get('contentUrl'), video_id)
            self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'uploader': media.get('channel'),
            'duration': duration,
            'thumbnails': thumbnails,
            'formats': formats
        }


class RaiIE(RaiBaseIE):
    _VALID_URL = r'https?://.+\.(?:rai|rainews)\.it/dl/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})\.html'
    _TESTS = [{
        'url': 'http://www.raisport.rai.it/dl/raiSport/media/rassegna-stampa-04a9f4bd-b563-40cf-82a6-aad3529cb4a9.html',
        'info_dict': {
            'id': '04a9f4bd-b563-40cf-82a6-aad3529cb4a9',
            'ext': 'flv',
            'title': 'TG PRIMO TEMPO',
            'upload_date': '20140612',
            'duration': 1758,
            'thumbnail': 're:^https?://.*\.jpg$'
        }
    }, {
        'url': 'http://www.rainews.it/dl/rainews/media/Weekend-al-cinema-da-Hollywood-arriva-il-thriller-di-Tate-Taylor-La-ragazza-del-treno-1632c009-c843-4836-bb65-80c33084a64b.html',
        'info_dict': {
            'id': '1632c009-c843-4836-bb65-80c33084a64b',
            'ext': 'flv',
            'title': 'Weekend al cinema, da Hollywood arriva il thriller di Tate Taylor \"La ragazza del treno\" ',
            'upload_date': '20161103',
            'thumbnail': 're:^https?://.*\.png$',
            'description': 're:^[A-Za-z]+'
        }
    }, {
        'url': 'http://www.rai.it/dl/RaiTV/programmi/media/ContentItem-efb17665-691c-45d5-a60c-5301333cbb0c.html',
        'md5': '11959b4e44fa74de47011b5799490adf',
        'info_dict': {
            'id': 'efb17665-691c-45d5-a60c-5301333cbb0c',
            'ext': 'mp4',
            'title': 'TG1 ore 20:00 del 03/11/2016',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20161103',
            'description': 're:^[A-Za-z]+'
        }
    }]

    def _real_extract(self, url):
        content_id = self._match_id(url)

        media = self._download_json(
            'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-%s.html?json' % content_id,
            content_id, 'Downloading video JSON')

        thumbnails = []
        for image_type in ('image', 'image_medium', 'image_300'):
            thumbnail_url = media.get(image_type)
            if thumbnail_url:
                thumbnails.append({
                    'url': compat_urlparse.urljoin(url, thumbnail_url),
                })

        formats = []
        media_type = media['type']
        if 'Audio' in media_type:
            formats.append({
                'format_id': media.get('formatoAudio'),
                'url': media['audioUrl'],
                'ext': media.get('formatoAudio'),
            })
        elif 'Video' in media_type:
            formats.extend(self._extract_relinker_formats(media['mediaUri'], content_id))
            self._sort_formats(formats)
        else:
            raise ExtractorError('not a media file')

        subtitles = {}
        captions = media.get('subtitlesUrl')
        if captions:
            STL_EXT = '.stl'
            SRT_EXT = '.srt'
            if captions.endswith(STL_EXT):
                captions = captions[:-len(STL_EXT)] + SRT_EXT
            subtitles['it'] = [{
                'ext': 'srt',
                'url': captions,
            }]

        return {
            'id': content_id,
            'title': media['name'],
            'description': media.get('desc'),
            'thumbnails': thumbnails,
            'uploader': media.get('author'),
            'upload_date': unified_strdate(media.get('date')),
            'duration': parse_duration(media.get('length')),
            'formats': formats,
            'subtitles': subtitles,
        }
