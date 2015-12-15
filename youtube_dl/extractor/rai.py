from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    parse_duration,
    unified_strdate,
)


class RaiIE(InfoExtractor):
    _VALID_URL = r'(?P<url>(?P<host>http://(?:.+?\.)?(?:rai\.it|rai\.tv|rainews\.it))/dl/.+?-(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})(?:-.+?)?\.html)'
    _TESTS = [
        {
            'url': 'http://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-cb27157f-9dd0-4aee-b788-b1f67643a391.html',
            'md5': 'c064c0b2d09c278fb293116ef5d0a32d',
            'info_dict': {
                'id': 'cb27157f-9dd0-4aee-b788-b1f67643a391',
                'ext': 'mp4',
                'title': 'Report del 07/04/2014',
                'description': 'md5:f27c544694cacb46a078db84ec35d2d9',
                'upload_date': '20140407',
                'duration': 6160,
            }
        },
        {
            'url': 'http://www.raisport.rai.it/dl/raiSport/media/rassegna-stampa-04a9f4bd-b563-40cf-82a6-aad3529cb4a9.html',
            'md5': '8bb9c151924ce241b74dd52ef29ceafa',
            'info_dict': {
                'id': '04a9f4bd-b563-40cf-82a6-aad3529cb4a9',
                'ext': 'mp4',
                'title': 'TG PRIMO TEMPO',
                'description': '',
                'upload_date': '20140612',
                'duration': 1758,
            },
            'skip': 'Error 404',
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
            'md5': '35694f062977fe6619943f08ed935730',
            'info_dict': {
                'id': 'b4a49761-e0cc-4b14-8736-2729f6f73132',
                'ext': 'mp4',
                'title': 'Alluvione in Sardegna e dissesto idrogeologico',
                'description': 'Edizione delle ore 20:30 ',
            }
        },
        {
            'url': 'http://www.ilcandidato.rai.it/dl/ray/media/Il-Candidato---Primo-episodio-Le-Primarie-28e5525a-b495-45e8-a7c3-bc48ba45d2b6.html',
            'md5': '02b64456f7cc09f96ff14e7dd489017e',
            'info_dict': {
                'id': '28e5525a-b495-45e8-a7c3-bc48ba45d2b6',
                'ext': 'flv',
                'title': 'Il Candidato - Primo episodio: "Le Primarie"',
                'description': 'Primo appuntamento con "Il candidato" con Filippo Timi, alias Piero Zucca presidente!',
                'uploader': 'RaiTre',
            }
        },
        {
            'url': 'http://www.report.rai.it/dl/Report/puntata/ContentItem-0c7a664b-d0f4-4b2c-8835-3f82e46f433e.html',
            'md5': '037104d2c14132887e5e4cf114569214',
            'info_dict': {
                'id': '0c7a664b-d0f4-4b2c-8835-3f82e46f433e',
                'ext': 'flv',
                'title': 'Il pacco',
                'description': 'md5:4b1afae1364115ce5d78ed83cd2e5b3a',
                'uploader': 'RaiTre',
                'upload_date': '20141221',
            },
        }
    ]

    def _extract_relinker_url(self, webpage):
        return self._proto_relative_url(self._search_regex(
            [r'name="videourl" content="([^"]+)"', r'var\s+videoURL(?:_MP4)?\s*=\s*"([^"]+)"'],
            webpage, 'relinker url', default=None))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')

        webpage = self._download_webpage(url, video_id)

        relinker_url = self._extract_relinker_url(webpage)

        if not relinker_url:
            iframe_url = self._search_regex(
                [r'<iframe[^>]+src="([^"]*/dl/[^"]+\?iframe\b[^"]*)"',
                 r'drawMediaRaiTV\(["\'](.+?)["\']'],
                webpage, 'iframe')
            if not iframe_url.startswith('http'):
                iframe_url = compat_urlparse.urljoin(url, iframe_url)
            webpage = self._download_webpage(
                iframe_url, video_id)
            relinker_url = self._extract_relinker_url(webpage)

        relinker = self._download_json(
            '%s&output=47' % relinker_url, video_id)

        media_url = relinker['video'][0]
        ct = relinker.get('ct')
        if ct == 'f4m':
            formats = self._extract_f4m_formats(
                media_url + '&hdcore=3.7.0&plugin=aasp-3.7.0.39.44', video_id)
        else:
            formats = [{
                'url': media_url,
                'format_id': ct,
            }]

        json_link = self._html_search_meta(
            'jsonlink', webpage, 'JSON link', default=None)
        if json_link:
            media = self._download_json(
                host + json_link, video_id, 'Downloading video JSON')
            title = media.get('name')
            description = media.get('desc')
            thumbnail = media.get('image_300') or media.get('image_medium') or media.get('image')
            duration = parse_duration(media.get('length'))
            uploader = media.get('author')
            upload_date = unified_strdate(media.get('date'))
        else:
            title = (self._search_regex(
                r'var\s+videoTitolo\s*=\s*"(.+?)";',
                webpage, 'title', default=None) or self._og_search_title(webpage)).replace('\\"', '"')
            description = self._og_search_description(webpage)
            thumbnail = self._og_search_thumbnail(webpage)
            duration = None
            uploader = self._html_search_meta('Editore', webpage, 'uploader')
            upload_date = unified_strdate(self._html_search_meta(
                'item-date', webpage, 'upload date', default=None))

        subtitles = self.extract_subtitles(video_id, webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'duration': duration,
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
