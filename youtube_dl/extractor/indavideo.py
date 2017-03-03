# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_age_limit,
    parse_iso8601,
)


class IndavideoIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:https?:)//
                    (?:
                        (?:.+?\.)?indavideo\.hu/(?:player/)?video/|
                        assets\.indavideo\.hu/swf/(?:inda)player\.swf\?.*\b(?:v(?:ID|id))=
                    )
                    (?P<id>[a-zA-Z0-9-_]+)'''
    _TESTS = [{
        'url': 'http://indavideo.hu/player/video/1bdc3c6d80/',
        'md5': 'f79b009c66194acacd40712a6778acfa',
        'info_dict': {
            'id': '1837039',
            'ext': 'mp4',
            'title': 'Cicatánc',
            'description': '',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'cukiajanlo',
            'uploader_id': '83729',
            'timestamp': 1439193826,
            'upload_date': '20150810',
            'duration': 72,
            'age_limit': 0,
            'tags': ['tánc', 'cica', 'cuki', 'cukiajanlo', 'newsroom'],
        }
    }, {
        'url': 'http://indavideo.hu/video/Vicces_cica_1',
        'only_matching': True,
    }, {
        'url': 'http://embed.indavideo.hu/player/video/1bdc3c6d80?autostart=1&hide=1',
        'only_matching': True,
    }, {
        'url': 'http://assets.indavideo.hu/swf/player.swf?v=fe25e500&vID=1bdc3c6d80&autostart=1&hide=1&i=1',
        'only_matching': True,
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

    @staticmethod
    def _extract_urls(webpage):
        return [url for _, url in re.findall(
            r'<(?:iframe[^>]+src|object[^>]+data)=(["\'])(?P<url>(?:https?:)?//(?:(?:.+?\.)?indavideo\.hu/(?:player/)?video/|assets\.indavideo\.hu/swf/(?:inda)?player\.swf\?.*\b(?:v(?:ID|id))=)[a-zA-Z0-9-_]+)(?:\?|&|\1)',
            webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://amfphp.indavideo.hu/SYm0json.php/player.playerHandler.getVideoData/%s' % video_id,
            video_id)['data']

        title = video.get('title')

        filesh = video.get('filesh')

        video_urls = video.get('video_files', [])
        video_file = video.get('video_file')
        if video_file:
            video_urls.append(video_file)
        video_urls = list(set(video_urls))

        video_prefix = video_urls[0].rsplit('/', 1)[0]

        '''
        ### flv files has not filesh in every format to get token
        for flv_file in video.get('flv_files', []):
            flv_url = '%s/%s' % (video_prefix, flv_file)
            if flv_url not in video_urls:
                video_urls.append(flv_url)
        '''

        formats = []
        for video_url in video_urls:
            _height = self._search_regex(
                r'\.(\d{3,4})\.mp4(?:\?|$)', video_url, 'height', default=None)
            _url = video_url
            if filesh:
                if _height in filesh:
                    _url += '&' if '?' in _url else '?'
                    _url += "token=" + filesh.get(_height)
            formats.append({
                'url': _url,
                'height': int_or_none(_height),
            })
        self._sort_formats(formats)

        timestamp = video.get('date')
        if timestamp:
            # upload date is in CEST
            timestamp = parse_iso8601(timestamp + ' +0200', ' ')

        thumbnails = [{
            'url': self._proto_relative_url(thumbnail)
        } for thumbnail in video.get('thumbnails', [])]

        tags = [tag['title'] for tag in video.get('tags') or []]

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
