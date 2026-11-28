# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class PremierOneIE(InfoExtractor):
    _VALID_URL = r'https?://premier\.one/show/(?P<show_id>[0-9]+)(/season/(?P<season_number>\d+))?(/video/(?P<id>[0-9a-f]+))?'
    _TEST = {
        'url': 'https://premier.one/show/3421/season/6/video/b4766f2eeb90cbb5538729061ac3949b',
        'info_dict': {
            'id': 'b4766f2eeb90cbb5538729061ac3949b',
            'ext': 'mp4',
            'title': '32 выпуск',
            'thumbnail': 'https://pic.uma.media/pic/video/06/c2/06c2cb95bb06c03c379d9d20930c5718.jpg',
            'description': 'В этом выпуске шоу «Где логика?» в интеллектуальном поединке сразятся Екатерина Моргунова и Манижа против Ильи Соболева и Зураба Матуа.',
            'timestamp': 1611615378,
            'upload_date': '20210125',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _extract_video(self, video_id):
        video = self._download_json(
            'https://premier.one/uma-api/video/' + video_id,
            video_id, 'Downloading video information ' + video_id,
            headers={
                'Accept': 'application/json',
                'Referer': 'https://premier.one/play/embed/' + video_id + '?controlledFullscreen=true'
            })

        return self._extract_video_info(video)

    def _extract_video_info(self, item):
        video_id = item.get('id')
        info = {
            'id': video_id,
            'title': item.get('title'),
            'description': item.get('description'),
            'thumbnail': item.get('thumbnail_url'),
            'duration': parse_duration(item.get('duration')),
            'timestamp': parse_iso8601(item.get('publication_ts')),
            'comment_count': item.get('comments_count'),
            'season_number': item.get('season'),
            'episode_number': item.get('episode'),
            'url': item.get('video_url'),
            'ext': 'mp4',
        }

        video = self._download_json(
            'https://premier.one/api/play/options/' + video_id + '/?format=json&no_404=true',
            video_id, 'Downloading video ' + info.get('title'),
            headers={
                'Accept': 'application/json',
                'Referer': 'https://premier.one/play/embed/' + video_id + '?controlledFullscreen=true'
            })
        if video.get('video_balancer') and video.get('video_balancer').get('default'):
            formats = []
            m3u8_url = video.get('video_balancer').get('default')
            m3u8_formats = self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                fatal=False)
            formats.extend(m3u8_formats)

            info['formats'] = formats

        return info

    def _extract_show_playlist(self, show_id, season_number):
        seasons = self._download_json(
            'https://premier.one/uma-api/metainfo/tv/' + show_id + '/season/',
            show_id, 'Downloading videos JSON',
            headers={
                'Accept': 'application/json',
                'Referer': 'https://premier.one/show/' + show_id
            })

        entries = []
        for season in seasons:
            if season_number is not None and str(season.get('number')) != season_number:
                continue

            metainfo = self._download_json(
                'https://premier.one/uma-api/metainfo/tv/' + show_id + '/video/?season=' + str(season.get('number')),
                str(season.get('number')), 'Downloading season ' + str(season.get('number')),
                headers={
                    'Accept': 'application/json',
                    'Referer': 'https://premier.one/show/' + show_id + '/season/' + str(season.get('number'))
                })
            while metainfo and len(metainfo.get('results')) > 0:
                for item in metainfo.get('results'):
                    video_id = item.get('id')
                    if not video_id:
                        continue

                    info = self._extract_video_info(item)
                    if info:
                        entries.append(info)

                if metainfo.get('has_next'):
                    metainfo = self._download_json(
                        metainfo.get('next'),
                        str(season.get('number')), 'Downloading metainfo JSON for page ' + str(metainfo.get('page') + 1),
                        headers={
                            'Accept': 'application/json',
                            'Referer': 'https://premier.one/show/' + str(show_id) + '/season/' + str(season.get('number')) + '/video/' + video_id
                        })
                else:
                    metainfo = None

        return self.playlist_result(entries, show_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        if mobj.group('id'):
            return self._extract_video(mobj.group('id'))
        else:
            return self._extract_show_playlist(mobj.group('show_id'), mobj.group('season_number'))
