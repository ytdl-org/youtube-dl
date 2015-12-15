# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_age_limit,
    parse_iso8601,
)


class IndavideoEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:embed\.)?indavideo\.hu/player/video/|assets\.indavideo\.hu/swf/player\.swf\?.*\b(?:v(?:ID|id))=)(?P<id>[\da-f]+)'
    _TESTS = [{
        'url': 'http://indavideo.hu/player/video/1bdc3c6d80/',
        'md5': 'f79b009c66194acacd40712a6778acfa',
        'info_dict': {
            'id': '1837039',
            'ext': 'mp4',
            'title': 'Cicatánc',
            'description': '',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'cukiajanlo',
            'uploader_id': '83729',
            'timestamp': 1439193826,
            'upload_date': '20150810',
            'duration': 72,
            'age_limit': 0,
            'tags': ['tánc', 'cica', 'cuki', 'cukiajanlo', 'newsroom'],
        },
    }, {
        'url': 'http://embed.indavideo.hu/player/video/1bdc3c6d80?autostart=1&hide=1',
        'only_matching': True,
    }, {
        'url': 'http://assets.indavideo.hu/swf/player.swf?v=fe25e500&vID=1bdc3c6d80&autostart=1&hide=1&i=1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://amfphp.indavideo.hu/SYm0json.php/player.playerHandler.getVideoData/%s' % video_id,
            video_id)['data']

        title = video['title']

        video_urls = video.get('video_files', [])
        video_file = video.get('video_file')
        if video:
            video_urls.append(video_file)
        video_urls = list(set(video_urls))

        video_prefix = video_urls[0].rsplit('/', 1)[0]

        for flv_file in video.get('flv_files', []):
            flv_url = '%s/%s' % (video_prefix, flv_file)
            if flv_url not in video_urls:
                video_urls.append(flv_url)

        formats = [{
            'url': video_url,
            'height': self._search_regex(r'\.(\d{3,4})\.mp4$', video_url, 'height', default=None),
        } for video_url in video_urls]
        self._sort_formats(formats)

        timestamp = video.get('date')
        if timestamp:
            # upload date is in CEST
            timestamp = parse_iso8601(timestamp + ' +0200', ' ')

        thumbnails = [{
            'url': self._proto_relative_url(thumbnail)
        } for thumbnail in video.get('thumbnails', [])]

        tags = [tag['title'] for tag in video.get('tags', [])]

        return {
            'id': video.get('id') or video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnails': thumbnails,
            'uploader': video.get('user_name'),
            'uploader_id': video.get('user_id'),
            'timestamp': timestamp,
            'duration': int_or_none(video.get('length')),
            'age_limit': parse_age_limit(video.get('age_limit')),
            'tags': tags,
            'formats': formats,
        }


class IndavideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?indavideo\.hu/video/(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'http://indavideo.hu/video/Vicces_cica_1',
        'md5': '8c82244ba85d2a2310275b318eb51eac',
        'info_dict': {
            'id': '1335611',
            'display_id': 'Vicces_cica_1',
            'ext': 'mp4',
            'title': 'Vicces cica',
            'description': 'Játszik a tablettel. :D',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'Jet_Pack',
            'uploader_id': '491217',
            'timestamp': 1390821212,
            'upload_date': '20140127',
            'duration': 7,
            'age_limit': 0,
            'tags': ['vicces', 'macska', 'cica', 'ügyes', 'nevetés', 'játszik', 'Cukiság', 'Jet_Pack'],
        },
    }, {
        'url': 'http://index.indavideo.hu/video/2015_0728_beregszasz',
        'only_matching': True,
    }, {
        'url': 'http://auto.indavideo.hu/video/Sajat_utanfutoban_a_kis_tacsko',
        'only_matching': True,
    }, {
        'url': 'http://erotika.indavideo.hu/video/Amator_tini_punci',
        'only_matching': True,
    }, {
        'url': 'http://film.indavideo.hu/video/f_hrom_nagymamm_volt',
        'only_matching': True,
    }, {
        'url': 'http://palyazat.indavideo.hu/video/Embertelen_dal_Dodgem_egyuttes',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        embed_url = self._search_regex(
            r'<link[^>]+rel="video_src"[^>]+href="(.+?)"', webpage, 'embed url')

        return {
            '_type': 'url_transparent',
            'ie_key': 'IndavideoEmbed',
            'url': embed_url,
            'display_id': display_id,
        }
