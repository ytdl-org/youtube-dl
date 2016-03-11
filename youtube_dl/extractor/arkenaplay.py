# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601
)
import re


class ArkenaPlayIE(InfoExtractor):
    IE_NAME = 'ArkenaPlay'
    _VALID_URL = r'(?P<shortcut>arkena:(?P<version>[0-9]+):(?P<mediatype>[A-Za-z0-9]+):(?P<mediaId>[^:]+):(?P<widgetsettingId>[A-Za-z0-9]+):(?P<accountId>[A-Za-z0-9]+))|(?:(?P<host>https?://(?:www\.)?play\..*\..*)/embed/(?:avp/v[0-9]+/player/[A-Za-z0-9]+/)?(?P<id>.*)?)'

    _TESTS = [{
        'url': 'http://play.lcp.fr/embed/327336/131064/darkmatter/0',
        'md5': '6cea4f7d13810464ef8485a924fc3333',
        'info_dict': {
            'id': '327336',
            'url': 're:http://httpod.scdn.arkena.com/11970/327336.*',
            'ext': 'mp4',
            'title': '327336',
            'upload_date': '20160225',
            'timestamp': 1456391602
        }
    }, {
        # Shortcut for: https://play.arkena.com/embed/avp/v2/player/media/b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe/1/129411
        'url': 'arkena:2:media:b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe:1:129411',
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
        mobj = re.match(self._VALID_URL, url)
        if mobj.group('shortcut'):
            version = mobj.group('version')
            mediatype = mobj.group('mediatype')
            mediaid = mobj.group('mediaId')
            widgetsettingid = mobj.group('widgetsettingId')
            accountid = mobj.group('accountId')
            display_id = '{0}:{1}:{2}:{3}'.format(mediatype, mediaid, widgetsettingid, accountid)
            media_url = 'https://play.arkena.com/config/avp/v{0}/player/{1}/{2}/{3}/{4}/?callbackMethod=?'.format(
                version, mediatype, mediaid, widgetsettingid, accountid)
        else:
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

        for type_name, video_files_json in media_files.iteritems():
            for video_info in video_files_json:
                video_url = video_info.get('Url')
                if not video_url:
                    continue
                type = video_info.get('Type')
                if type_name in ['Mp4', 'WebM', 'Flash']:
                    bitrate = int_or_none(video_info.get('Bitrate'), scale=1000)
                    ext = None
                    if type == 'video/mp4':
                        ext = 'mp4'
                    elif type == 'video/webm':
                        ext = 'webm'
                    elif type == 'video/x-flv':
                        ext = 'flv'
                    formats.append({
                        'url': video_url,
                        'ext': ext,
                        'tbr': bitrate
                    })
                elif type_name == 'M3u8' and type == 'application/x-mpegURL':
                    formats.extend(self._extract_m3u8_formats(video_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                elif type_name == 'Flash' and type == 'application/hds+xml':
                    formats.extend(self._extract_f4m_formats(video_url, video_id, f4m_id='hds', fatal=False))
                elif type_name == 'Dash' and type == 'application/dash+xml':
                    formats.extend(self._extract_mpd_formats(video_url, video_id, mpd_id='dash', fatal=False))

        self._sort_formats(formats)
        return formats