from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)
from ..compat import compat_HTTPError
import re
from .bbccouk import BBCCoUkIE

class BBCNewsIE(BBCCoUkIE):
    IE_NAME = 'bbc.com'
    IE_DESC = 'BBC news'
    _VALID_URL = r'https?://(?:www\.)?(?:bbc\.co\.uk|bbc\.com)/news/(?P<id>[^/]+)'

    mediaselector_url = 'http://open.live.bbc.co.uk/mediaselector/4/mtis/stream/%s'

    _TESTS = [{
        'url': 'http://www.bbc.com/news/world-europe-32668511',
        'info_dict': {
            'id': 'world-europe-32668511',
            'title': 'Russia stages massive WW2 parade despite Western boycott',
        },
        'playlist_count': 2,
    },{
        'url': 'http://www.bbc.com/news/business-28299555',
        'info_dict': {
            'id': 'business-28299555',
            'title': 'Farnborough Airshow: Video highlights',
        },
        'playlist_count': 9,
    },{
        'url': 'http://www.bbc.com/news/world-europe-32041533',
        'note': 'Video',
        'info_dict': {
            'id': 'p02mprgb',
            'ext': 'mp4',
            'title': 'Aerial footage showed the site of the crash in the Alps - courtesy BFM TV',
            'description': 'Germanwings plane crash site in aerial video - Aerial footage showed the site of the crash in the Alps - courtesy BFM TV',
            'duration': 47,
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _duration_str2int(self, str):
        if not str:
            return None
        ret = re.match(r'^\d+$', str)
        if ret:
            return int(ret.group(0))
        ret = re.match(r'PT((?P<h>\d+)H)?((?P<m>\d+)M)?(?P<s>\d+)S$', str)
        if ret:
            total=int(ret.group('s'))
            if ret.group('m'):
                total+=(int(ret.group('m'))*60)
            if ret.group('h'):
                total+=(int(ret.group('h'))*3600)
            return total
        return None

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self._download_webpage(url, list_id)

        list_title = self._html_search_regex(r'<title>(.*?)(?:\s*-\s*BBC News)?</title>', webpage, 'list title')

        pubdate = self._html_search_regex(r'"datePublished":\s*"(\d+-\d+-\d+)', webpage, 'date', default=None)
        if pubdate:
           pubdate = pubdate.replace('-','')

        ret = []
        # works with bbc.com/news/something-something-123456 articles
        matches = re.findall(r"data-media-meta='({[^']+})'", webpage)
        if not matches:
           # stubbornly generic extractor for {json with "image":{allvideoshavethis},etc}
           # in http://www.bbc.com/news/video_and_audio/international
           matches = re.findall(r"({[^{}]+image\":{[^}]+}[^}]+})", webpage)
        if not matches:
           raise ExtractorError('No video found', expected=True)

        for ent in matches:
            jent = self._parse_json(ent,list_id)

            programme_id = jent.get('externalId',None)
            xml_url = jent.get('href', None)

            title = jent['caption']
            duration = self._duration_str2int(jent.get('duration',None))
            description = list_title + ' - ' + jent.get('caption','')
            thumbnail = None
            if jent.has_key('image'):
               thumbnail=jent['image'].get('href',None)

            if programme_id:
               formats, subtitles = self._download_media_selector(programme_id)
            elif xml_url:
               # Cheap fallback
               # http://playlists.bbc.co.uk/news/(list_id)[ABC..]/playlist.sxml
               xml = self._download_webpage(xml_url, programme_id, 'Downloading playlist.sxml for externalId (fallback)')
               programme_id = self._search_regex(r'<mediator [^>]*identifier="(.+?)"', xml, 'playlist.sxml (externalId fallback)')
               formats, subtitles = self._download_media_selector(programme_id)
            else:
               raise ExtractorError('data-media-meta entry has no externalId or href value.')
               
            self._sort_formats(formats)

            ret.append( {
                'id': programme_id,
                'uploader': 'BBC News',
                'upload_date': pubdate,
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'duration': duration,
                'formats': formats,
                'subtitles': subtitles,
            } )

        if len(ret) > 0:
           return self.playlist_result(ret, list_id, list_title)
        raise ExtractorError('No video found', expected=True)
