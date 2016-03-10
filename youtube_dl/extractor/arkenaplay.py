# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601
)


class ArkenaPlayIE(InfoExtractor):
    IE_NAME = 'ArkenaPlay'
    _VALID_URL = r'(?P<host>https?://(?:www\.)?play\..*\..*)/embed/.*(?P<id>\d+)?/.*'

    _TESTS = [{
        'url': 'http://play.lcp.fr/embed/327336/131064/darkmatter/0',
        'md5': '7d857b1af491ec0f6c2610e52df1ff82',
        'info_dict': {
            'id': '327336',
            'url': 're:http://httpod.scdn.arkena.com/11970/327336.*',
            'ext': 'mp4',
            'title': '327336',
            'upload_date': '20160225',
            'timestamp': 1456391602
        }
    }, {
        'url': 'https://play.arkena.com/embed/avp/v2/player/media/b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe/1/129411',
        'md5': 'b96f2f71b359a8ecd05ce4e1daa72365',
        'info_dict': {
            'id': 'b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe',
            'url': 'http://88e04ec095b07cd1aa3ea588be47e870.httpcache0.90034-httpcache0.dna.qbrick.com/90034-httpcache0/4bf759a1-00090034/bbb_sunflower_2160p_60fps_normal_720p.mp4',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'description': 'Royalty free test video',
            'upload_date': '20150528',
            'timestamp': 1432816365
        }
    }]

    def _real_extract(self, url):
        display_id = self._search_regex(self._VALID_URL, url, 'host_name', group='id')
        webpage = self._download_webpage(url, display_id)

        media_url_regex = '"(?P<mediainfo>(?P<host>.*)/(c|C)onfig/.*\?callbackMethod=\?)"'
        media_url = self._html_search_regex(media_url_regex, webpage, 'arkena_media_info_url')
        hostname = self._html_search_regex(media_url_regex, webpage, 'arkena_media_host', group='host')
        if not hostname:
            hostname = self._search_regex(self._VALID_URL, url, 'host_name', group='host')
            media_url = hostname + media_url

        # Extract the required info of the media files gathered in a dictionary
        arkena_info = self._download_webpage(media_url, 'arkena_info_')
        arkena_info_regex = r'\?\((?P<json>.*)\);'
        media_dict = self._parse_json(self._search_regex(arkena_info_regex, arkena_info, 'json', group='json'),
                                      display_id)

        # All videos are part of a playlist, a single video is also put in a playlist
        playlist_items = media_dict.get('Playlist', [])
        if len(playlist_items) == 0:
            return self.url_result(url, 'Generic')
        elif len(playlist_items) == 1:
            arkena_media_info = playlist_items[0]
            return self.__extract_from_playlistentry(arkena_media_info)
        else:
            entries_info = []
            for arkena_playlist_item in playlist_items:
                entries_info.append(self.__extract_from_playlistentry(arkena_playlist_item))
            return {
                'id': display_id,
                'entries': entries_info
            }

    def __extract_from_playlistentry(self, arkena_playlistentry_info):
        media_info = arkena_playlistentry_info.get('MediaInfo', {})
        thumbnails = self.__get_thumbnails(media_info)
        title = media_info.get('Title')
        description = media_info.get('Description')
        video_id = media_info.get('VideoId')
        timestamp = parse_iso8601(media_info.get('PublishDate'))
        formats = self.__get_video_formats(arkena_playlistentry_info, video_id)
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': description,
            'timestamp': timestamp
        }

    def __get_thumbnails(self, arkena_mediainfo):
        thumbnails = []
        thumbnails_info = arkena_mediainfo.get('Poster')
        if not thumbnails_info:
            return None
        for thumbnail in thumbnails_info:
            thumbnail_url = thumbnail.get('Url')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(thumbnail.get('Size'))
            })
        return thumbnails

    def __get_video_formats(self, media_files_info, video_id):
        formats = []
        media_files = media_files_info.get('MediaFiles')
        if not media_files:
            return None

        formats.extend(self.__get_mp4_video_formats(media_files))
        formats.extend(self.__get_m3u8_video_formats(media_files, video_id))
        formats.extend(self.__get_flash_video_formats(media_files, video_id))
        # TODO <DASH (mpd) formats>
        self._sort_formats(formats)
        return formats

    def __get_mp4_video_formats(self, media_files_json):
        formats = []
        mp4_files_json = media_files_json.get('Mp4')
        if not mp4_files_json:
            return None
        for video_info in mp4_files_json:
            bitrate = int_or_none(video_info.get('Bitrate'), scale=1000)  # Scale bitrate to KBit/s
            video_url = video_info.get('Url')
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'tbr': bitrate
            })
        return formats

    def __get_m3u8_video_formats(self, media_files_json, video_id):
        formats = []
        m3u8_files_json = media_files_json.get('M3u8')
        if not m3u8_files_json:
            return None
        for video_info in m3u8_files_json:
            video_url = video_info.get('Url')
            if not video_url:
                continue
            formats.extend(self._extract_m3u8_formats(video_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
        return formats

    def __get_flash_video_formats(self, media_files_json, video_id):
        formats = []
        flash_files_json = media_files_json.get('Flash')
        if not flash_files_json:
            return None
        for video_info in flash_files_json:
            video_url = video_info.get('Url')
            if not video_url:
                continue
            video_type = video_info.get('Type')
            if video_type == 'application/hds+xml':
                formats.extend(self._extract_f4m_formats(video_url, video_id, f4m_id='hds', fatal=False))
            elif video_type == 'video/x-flv':
                formats.append({
                    'url': video_url,
                    'ext': 'flv'
                })
        return formats
