from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
    int_or_none,
)


class NBABaseIE(InfoExtractor):
    def _get_formats(self, video_id):
        base_url = 'http://nba.cdn.turner.com/nba/big%s' % video_id
        return [{
            'url': base_url + '_nba_android_high.mp4',
            'width': 480,
            'height': 320,
            'format_id': '320p',
        },{
            'url': base_url + '_640x360_664b.mp4',
            'width': 640,
            'height': 360,
            'format_id': '360p',
        },{
            'url': base_url + '_768x432_1404.mp4',
            'width': 768,
            'height': 432,
            'format_id': '432p',
        },{
            'url': base_url + '_1280x720.mp4',
            'width': 1280,
            'height': 720,
            'format_id': '720p',
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        ret = self._extract_metadata(webpage, video_id)
        ret['id'] = video_id.rpartition('/')[2]
        ret['formats'] = self._get_formats(video_id)
        return ret


class NBAIE(NBABaseIE):
    IE_NAME = 'nba'
    _VALID_URL = r'https?://(?:www\.)?nba\.com/(?:nba/)?video(?P<id>/[^?]*?)/?(?:/index\.html)?(?:\?.*)?$'
    _TESTS = [{
        'url': 'http://www.nba.com/video/games/nets/2012/12/04/0021200253-okc-bkn-recap.nba/index.html',
        'md5': '9d902940d2a127af3f7f9d2f3dc79c96',
        'info_dict': {
            'id': '0021200253-okc-bkn-recap.nba',
            'ext': 'mp4',
            'title': 'Thunder vs. Nets',
            'description': 'Kevin Durant scores 32 points and dishes out six assists as the Thunder beat the Nets in Brooklyn.',
            'duration': 181,
            'timestamp': 1354680189,
            'upload_date': '20121205',
        },
    }, {
        'url': 'http://www.nba.com/video/games/hornets/2014/12/05/0021400276-nyk-cha-play5.nba/',
        'only_matching': True,
    }]

    def _extract_metadata(self, webpage, video_id):
        return {
            'title': self._html_search_meta('name', webpage),
            'description': self._html_search_meta('description', webpage),
            'duration': parse_duration(self._html_search_meta('duration', webpage)),
            'thumbnail': self._html_search_meta('thumbnailUrl', webpage),
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage))
        }

class NBAWatchIE(NBABaseIE):
    IE_NAME = 'nba:watch'
    _VALID_URL = r'https?://watch.nba\.com/(?:nba/)?video(?P<id>/[^?]*?)/?(?:/index\.html)?(?:\?.*)?$'
    _TESTS = [{
        'url': 'http://watch.nba.com/nba/video/channels/playoffs/2015/05/20/0041400301-cle-atl-recap.nba',
        'md5': 'b2b39b81cf28615ae0c3360a3f9668c4',
        'info_dict': {
            'id': '0041400301-cle-atl-recap.nba',
            'ext': 'mp4',
            'title': 'Hawks vs. Cavaliers Game 1',
            'description': 'md5:8094c3498d35a9bd6b1a8c396a071b4d',
            'duration': 228,
            'timestamp': 1432094400,
            'upload_date': '20150520',
        }
    }]

    def _extract_metadata(self, webpage, video_id):
        program_id = self._search_regex(r'var\s+programId\s*=\s*(\d+);', webpage, 'program id')
        metadata = self._download_json(
            'http://smbsolr.cdnak.neulion.com/solr_nbav6/nba/nba/mlt/?wt=json&fl=name,description,image,runtime,releaseDate&q=sequence%3A' + program_id, video_id)['match']['docs'][0]
        return {
            'title': metadata['name'],
            'description': metadata.get('description'),
            'duration': int_or_none(metadata.get('runtime')),
            'thumbnail': metadata.get('image'),
            'timestamp': parse_iso8601(metadata.get('releaseDate'))
        }
