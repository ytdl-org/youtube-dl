# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
)
import re


class HotStarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hotstar\.com/(?:.+?[/-])?(?P<id>\d{10})'
    _TESTS = [{
        'url': 'http://www.hotstar.com/on-air-with-aib--english-1000076273',
        'info_dict': {
            'id': '1000076273',
            'ext': 'mp4',
            'title': 'On Air With AIB',
            'description': 'md5:c957d8868e9bc793ccb813691cc4c434',
            'timestamp': 1447227000,
            'upload_date': '20151111',
            'duration': 381,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://www.hotstar.com/sports/cricket/rajitha-sizzles-on-debut-with-329/2001477583',
        'only_matching': True,
    }, {
        'url': 'http://www.hotstar.com/1000000515',
        'only_matching': True,
    }]

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata', fatal=True, query=None):
        json_data = super(HotStarIE, self)._download_json(
            url_or_request, video_id, note, fatal=fatal, query=query)
        if json_data['resultCode'] != 'OK':
            if fatal:
                raise ExtractorError(json_data['errorDescription'])
            return None
        return json_data['resultObj']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'http://account.hotstar.com/AVS/besc', video_id, query={
                'action': 'GetAggregatedContentDetails',
                'channel': 'PCTV',
                'contentId': video_id,
            })['contentInfo'][0]
        title = video_data['episodeTitle']

        if video_data.get('encrypted') == 'Y':
            raise ExtractorError('This video is DRM protected.', expected=True)

        formats = []
        for f in ('JIO',):
            format_data = self._download_json(
                'http://getcdn.hotstar.com/AVS/besc',
                video_id, 'Downloading %s JSON metadata' % f,
                fatal=False, query={
                    'action': 'GetCDN',
                    'asJson': 'Y',
                    'channel': f,
                    'id': video_id,
                    'type': 'VOD',
                })
            if format_data:
                format_url = format_data.get('src')
                if not format_url:
                    continue
                ext = determine_ext(format_url)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        m3u8_id='hls', fatal=False))
                elif ext == 'f4m':
                    # produce broken files
                    continue
                else:
                    formats.append({
                        'url': format_url,
                        'width': int_or_none(format_data.get('width')),
                        'height': int_or_none(format_data.get('height')),
                    })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('broadcastDate')),
            'formats': formats,
            'episode': title,
            'episode_number': int_or_none(video_data.get('episodeNumber')),
            'series': video_data.get('contentTitle'),
        }

class HotStarPlaylistIE(HotStarBaseIE):
    IE_NAME = 'hotstar:playlist'
    _VALID_URL = r'https?://(?:www\.)?hotstar\.com/tv/(?P<playlist_title>.+)/(?P<series_id>\d+)/episodes/(?P<playlist_id>\d{1,})'

    _TESTS = [{
        'url': 'http://www.hotstar.com/tv/pow-bandi-yuddh-ke/10999/episodes/10856/9993',
        'info_dict': {
            'id': '10856',
            'title': 'pow-bandi-yuddh-ke',
        },
        'playlist_mincount': 0,
    }, {
        'url': 'http://www.hotstar.com/tv/pow-bandi-yuddh-ke/10999/episodes/10856/9993',
        'only_matching': True,
    }]

    def _extract_url_info(cls, url):
        mobj = re.match(cls._VALID_URL, url)
        return mobj.group('series_id'), mobj.group('playlist_id'), mobj.group('playlist_title')

    def _extract_from_json_url(self, series_id, playlist_title, video ):

        picture_url = video.get('urlPictures');
        thumbnail = ''
        if picture_url:
            thumbnail = 'http://media0-starag.startv.in/r1/thumbs/PCTV/%s/%s/PCTV-%s-hs.jpg' % ( picture_url[-2:], picture_url, picture_url )

        episode_title = video.get('episodeTitle', '')
        episode_title = episode_title.lower().replace(' ', '-')
        url = "http://www.hotstar.com/tv/%s/%s/%s/%s" % (playlist_title, series_id, episode_title, video.get('contentId'))

        info_dict = {
            'id': video.get('contentId'),
            'title': video.get('episodeTitle'),
            'description': video.get('longDescription'),
            'thumbnail' : thumbnail,
            'url' : url,
            '_type' : 'url',
        }
        return info_dict

    def _real_extract(self, url):
        series_id, playlist_id, playlist_title = self._extract_url_info(url)

        collection = self._download_json(
            "http://search.hotstar.com/AVS/besc?action=SearchContents&appVersion=5.0.39&channel=PCTV&moreFilters=series:%s;&query=*&searchOrder=last_broadcast_date+desc,year+asc,title+asc&type=EPISODE" % playlist_id,
            playlist_id
        )

        videos = collection['resultObj']['response']['docs']

        entries = [
            self._extract_from_json_url( series_id, playlist_title, video )
            for video in videos if video.get('contentId')]
        return self.playlist_result(entries, playlist_id, playlist_title)
