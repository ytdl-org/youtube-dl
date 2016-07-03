from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    ExtractorError,
    find_xpath_attr,
    fix_xml_ampersands,
    int_or_none,
    parse_duration,
    unified_strdate,
    update_url_query,
    xpath_text,
)


class RaiTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it)/dl/(?:[^/]+/)+media/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html'
    _TESTS = [
        {
            'url': 'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-cb27157f-9dd0-4aee-b788-b1f67643a391.html',
            'md5': '8970abf8caf8aef4696e7b1f2adfc696',
            'info_dict': {
                'id': 'cb27157f-9dd0-4aee-b788-b1f67643a391',
                'ext': 'mp4',
                'title': 'Report del 07/04/2014',
                'description': 'md5:f27c544694cacb46a078db84ec35d2d9',
                'upload_date': '20140407',
                'duration': 6160,
                'thumbnail': 're:^https?://.*\.jpg$',
            }
        },
        {
            # no m3u8 stream
            'url': 'http://www.raisport.rai.it/dl/raiSport/media/rassegna-stampa-04a9f4bd-b563-40cf-82a6-aad3529cb4a9.html',
            # HDS download, MD5 is unstable
            'info_dict': {
                'id': '04a9f4bd-b563-40cf-82a6-aad3529cb4a9',
                'ext': 'flv',
                'title': 'TG PRIMO TEMPO',
                'upload_date': '20140612',
                'duration': 1758,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'skip': 'Geo-restricted to Italy',
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
            'md5': 'e57493e1cb8bc7c564663f363b171847',
            'info_dict': {
                'id': '28e5525a-b495-45e8-a7c3-bc48ba45d2b6',
                'ext': 'mp4',
                'title': 'Il Candidato - Primo episodio: "Le Primarie"',
                'description': 'md5:364b604f7db50594678f483353164fb8',
                'upload_date': '20140923',
                'duration': 386,
                'thumbnail': 're:^https?://.*\.jpg$',
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
            for platform in ('mon', 'flash', 'native'):
                headers = {}
                # TODO: rename --cn-verification-proxy
                cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
                if cn_verification_proxy:
                    headers['Ytdl-request-proxy'] = cn_verification_proxy

                relinker = self._download_xml(
                    media['mediaUri'], video_id,
                    note='Downloading XML metadata for platform %s' % platform,
                    transform_source=fix_xml_ampersands,
                    query={'output': 45, 'pl': platform}, headers=headers)

                media_url = find_xpath_attr(relinker, './url', 'type', 'content').text
                if media_url == 'http://download.rai.it/video_no_available.mp4':
                    self.raise_geo_restricted()

                ext = determine_ext(media_url)
                if (platform == 'mon' and ext != 'm3u8') or (platform == 'flash' and ext != 'f4m'):
                    continue

                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        media_url, video_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls', fatal=False))
                elif ext == 'f4m':
                    manifest_url = update_url_query(
                        media_url, {'hdcore': '3.7.0', 'plugin': 'aasp-3.7.0.39.44'})
                    formats.extend(self._extract_f4m_formats(
                        manifest_url, video_id, f4m_id='hds', fatal=False))
                else:
                    bitrate = int_or_none(xpath_text(relinker, 'bitrate'))
                    formats.append({
                        'url': media_url,
                        'tbr': bitrate if bitrate > 0 else None,
                        'format_id': 'http-%d' % bitrate if bitrate > 0 else 'http',
                    })

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


class RaiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it)/dl/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html'
    _TESTS = [
        {
            'url': 'http://www.report.rai.it/dl/Report/puntata/ContentItem-0c7a664b-d0f4-4b2c-8835-3f82e46f433e.html',
            'md5': '2dd727e61114e1ee9c47f0da6914e178',
            'info_dict': {
                'id': '59d69d28-6bb6-409d-a4b5-ed44096560af',
                'ext': 'mp4',
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
