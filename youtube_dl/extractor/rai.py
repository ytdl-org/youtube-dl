from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    determine_ext,
    parse_duration,
    unified_strdate,
    int_or_none,
    xpath_text,
)


class RaiTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it)/dl/(?:[^/]+/)+media/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html'
    _TESTS = [
        {
            'url': 'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-cb27157f-9dd0-4aee-b788-b1f67643a391.html',
            'md5': '96382709b61dd64a6b88e0f791e6df4c',
            'info_dict': {
                'id': 'cb27157f-9dd0-4aee-b788-b1f67643a391',
                'ext': 'flv',
                'title': 'Report del 07/04/2014',
                'description': 'md5:f27c544694cacb46a078db84ec35d2d9',
                'upload_date': '20140407',
                'duration': 6160,
            }
        },
        {
            'url': 'http://www.raisport.rai.it/dl/raiSport/media/rassegna-stampa-04a9f4bd-b563-40cf-82a6-aad3529cb4a9.html',
            'md5': 'd9751b78eac9710d62c2447b224dea39',
            'info_dict': {
                'id': '04a9f4bd-b563-40cf-82a6-aad3529cb4a9',
                'ext': 'flv',
                'title': 'TG PRIMO TEMPO',
                'upload_date': '20140612',
                'duration': 1758,
            },
        },
        {
            'url': 'http://www.rainews.it/dl/rainews/media/state-of-the-net-Antonella-La-Carpia-regole-virali-7aafdea9-0e5d-49d5-88a6-7e65da67ae13.html',
            'md5': '35cf7c229f22eeef43e48b5cf923bef0',
            'info_dict': {
                'id': '7aafdea9-0e5d-49d5-88a6-7e65da67ae13',
                'ext': 'mp4',
                'title': 'State of the Net, Antonella La Carpia: regole virali',
                'description': 'md5:b0ba04a324126903e3da7763272ae63c',
                'upload_date': '20140613',
            },
            'skip': 'Error 404',
        },
        {
            'url': 'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-b4a49761-e0cc-4b14-8736-2729f6f73132-tg2.html',
            'info_dict': {
                'id': 'b4a49761-e0cc-4b14-8736-2729f6f73132',
                'ext': 'mp4',
                'title': 'Alluvione in Sardegna e dissesto idrogeologico',
                'description': 'Edizione delle ore 20:30 ',
            },
            'skip': 'invalid urls',
        },
        {
            'url': 'http://www.ilcandidato.rai.it/dl/ray/media/Il-Candidato---Primo-episodio-Le-Primarie-28e5525a-b495-45e8-a7c3-bc48ba45d2b6.html',
            'md5': '496ab63e420574447f70d02578333437',
            'info_dict': {
                'id': '28e5525a-b495-45e8-a7c3-bc48ba45d2b6',
                'ext': 'flv',
                'title': 'Il Candidato - Primo episodio: "Le Primarie"',
                'description': 'md5:364b604f7db50594678f483353164fb8',
                'upload_date': '20140923',
                'duration': 386,
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media = self._download_json(
            'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-%s.html?json' % video_id,
            video_id, 'Downloading video JSON')

        thumbnails = []
        for image_type in ('image', 'image_medium', 'image_300'):
            thumbnail_url = media.get(image_type)
            if thumbnail_url:
                thumbnails.append({
                    'url': thumbnail_url,
                })

        subtitles = []
        formats = []
        media_type = media['type']
        if 'Audio' in media_type:
            formats.append({
                'format_id': media.get('formatoAudio'),
                'url': media['audioUrl'],
                'ext': media.get('formatoAudio'),
            })
        elif 'Video' in media_type:
            def fix_xml(xml):
                return xml.replace(' tag elementi', '').replace('>/', '</')

            relinker = self._download_xml(
                media['mediaUri'] + '&output=43',
                video_id, transform_source=fix_xml)

            has_subtitle = False

            for element in relinker.findall('element'):
                media_url = xpath_text(element, 'url')
                ext = determine_ext(media_url)
                content_type = xpath_text(element, 'content-type')
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        media_url, video_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls', fatal=False))
                elif ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        media_url + '?hdcore=3.7.0&plugin=aasp-3.7.0.39.44',
                        video_id, f4m_id='hds', fatal=False))
                elif ext == 'stl':
                    has_subtitle = True
                elif content_type.startswith('video/'):
                    bitrate = int_or_none(xpath_text(element, 'bitrate'))
                    formats.append({
                        'url': media_url,
                        'tbr': bitrate if bitrate > 0 else None,
                        'format_id': 'http-%d' % bitrate if bitrate > 0 else 'http',
                    })
                elif content_type.startswith('image/'):
                    thumbnails.append({
                        'url': media_url,
                    })

            self._sort_formats(formats)

            if has_subtitle:
                webpage = self._download_webpage(url, video_id)
                subtitles = self._get_subtitles(video_id, webpage)
        else:
            raise ExtractorError('not a media file')

        return {
            'id': video_id,
            'title': media['name'],
            'description': media.get('desc'),
            'thumbnails': thumbnails,
            'uploader': media.get('author'),
            'upload_date': unified_strdate(media.get('date')),
            'duration': parse_duration(media.get('length')),
            'formats': formats,
            'subtitles': subtitles,
        }

    def _get_subtitles(self, video_id, webpage):
        subtitles = {}
        m = re.search(r'<meta name="closedcaption" content="(?P<captions>[^"]+)"', webpage)
        if m:
            captions = m.group('captions')
            STL_EXT = '.stl'
            SRT_EXT = '.srt'
            if captions.endswith(STL_EXT):
                captions = captions[:-len(STL_EXT)] + SRT_EXT
            subtitles['it'] = [{
                'ext': 'srt',
                'url': 'http://www.rai.tv%s' % compat_urllib_parse.quote(captions),
            }]
        return subtitles


class RaiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it)/dl/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html'
    _TESTS = [
        {
            'url': 'http://www.report.rai.it/dl/Report/puntata/ContentItem-0c7a664b-d0f4-4b2c-8835-3f82e46f433e.html',
            'md5': 'e0e7a8a131e249d1aa0ebf270d1d8db7',
            'info_dict': {
                'id': '59d69d28-6bb6-409d-a4b5-ed44096560af',
                'ext': 'flv',
                'title': 'Il pacco',
                'description': 'md5:4b1afae1364115ce5d78ed83cd2e5b3a',
                'upload_date': '20141221',
            },
        }
    ]

    @classmethod
    def suitable(cls, url):
        return False if RaiTVIE.suitable(url) else super(RaiIE, cls).suitable(url)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        iframe_url = self._search_regex(
            [r'<iframe[^>]+src="([^"]*/dl/[^"]+\?iframe\b[^"]*)"',
             r'drawMediaRaiTV\(["\'](.+?)["\']'],
            webpage, 'iframe')
        if not iframe_url.startswith('http'):
            iframe_url = compat_urlparse.urljoin(url, iframe_url)
        return self.url_result(iframe_url)
