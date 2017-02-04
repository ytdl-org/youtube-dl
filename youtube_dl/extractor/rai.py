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

    def _extract_from_content_id(self, content_id, base_url):
        media = self._download_json(
            'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-%s.html?json' % content_id,
            content_id, 'Downloading video JSON')

        thumbnails = []
        for image_type in ('image', 'image_medium', 'image_300'):
            thumbnail_url = media.get(image_type)
            if thumbnail_url:
                thumbnails.append({
                    'url': compat_urlparse.urljoin(base_url, thumbnail_url),
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


class RaiTVIE(RaiBaseIE):
    _VALID_URL = r'https?://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it)/dl/(?:[^/]+/)+(?:media|ondemand)/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html'
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
                'thumbnail': r're:^https?://.*\.jpg$',
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
                'thumbnail': r're:^https?://.*\.jpg$',
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
                'thumbnail': r're:^https?://.*\.jpg$',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        return self._extract_from_content_id(video_id, url)


class RaiIE(RaiBaseIE):
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
        },
        {
            # Direct relinker URL
            'url': 'http://www.rai.tv/dl/RaiTV/dirette/PublishingBlock-1912dbbf-3f96-44c3-b4cf-523681fbacbc.html?channel=EuroNews',
            # HDS live stream, MD5 is unstable
            'info_dict': {
                'id': '1912dbbf-3f96-44c3-b4cf-523681fbacbc',
                'ext': 'flv',
                'title': 'EuroNews',
            },
            'skip': 'Geo-restricted to Italy',
        },
        {
            # Embedded content item ID
            'url': 'http://www.tg1.rai.it/dl/tg1/2010/edizioni/ContentSet-9b6e0cba-4bef-4aef-8cf0-9f7f665b7dfb-tg1.html?item=undefined',
            'md5': '84c1135ce960e8822ae63cec34441d63',
            'info_dict': {
                'id': '0960e765-62c8-474a-ac4b-7eb3e2be39c8',
                'ext': 'mp4',
                'title': 'TG1 ore 20:00 del 02/07/2016',
                'upload_date': '20160702',
            },
        },
        {
            'url': 'http://www.rainews.it/dl/rainews/live/ContentItem-3156f2f2-dc70-4953-8e2f-70d7489d4ce9.html',
            # HDS live stream, MD5 is unstable
            'info_dict': {
                'id': '3156f2f2-dc70-4953-8e2f-70d7489d4ce9',
                'ext': 'flv',
                'title': 'La diretta di Rainews24',
            },
        },
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
            webpage, 'iframe', default=None)
        if iframe_url:
            if not iframe_url.startswith('http'):
                iframe_url = compat_urlparse.urljoin(url, iframe_url)
            return self.url_result(iframe_url)

        content_item_id = self._search_regex(
            r'initEdizione\((?P<q1>[\'"])ContentItem-(?P<content_id>[^\'"]+)(?P=q1)',
            webpage, 'content item ID', group='content_id', default=None)
        if content_item_id:
            return self._extract_from_content_id(content_item_id, url)

        relinker_url = compat_urlparse.urljoin(url, self._search_regex(
            r'(?:var\s+videoURL|mediaInfo\.mediaUri)\s*=\s*(?P<q1>[\'"])(?P<url>(https?:)?//mediapolis\.rai\.it/relinker/relinkerServlet\.htm\?cont=\d+)(?P=q1)',
            webpage, 'relinker URL', group='url'))
        formats = self._extract_relinker_formats(relinker_url, video_id)
        self._sort_formats(formats)

        title = self._search_regex(
            r'var\s+videoTitolo\s*=\s*([\'"])(?P<title>[^\'"]+)\1',
            webpage, 'title', group='title', default=None) or self._og_search_title(webpage)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }
