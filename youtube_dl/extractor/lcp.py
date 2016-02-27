# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601
)


class LcpIE(InfoExtractor):
    IE_NAME = 'LCP'
    _VALID_URL = r'https?://(?:www\.)?lcp\.fr/(?:[^\/]+/)*(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'http://www.lcp.fr/la-politique-en-video/schwartzenberg-prg-preconise-francois-hollande-de-participer-une-primaire',
        'md5': 'aecf5a330cfc1061445a9af5b2df392d',
        'info_dict': {
            'id': 'd56d03e9',
            'url': 're:http://httpod.scdn.arkena.com/11970/d56d03e9_[0-9]+.mp4',
            'ext': 'mp4',
            'title': 'Schwartzenberg (PRG) préconise à François Hollande de participer à une primaire à gauche',
            'upload_date': '20160226',
            'description': 'Le président du groupe parlementaire radical, républicain, démocrate et progressiste (RRDP) y voit une bonne occasion pour le président de la République de se "relégitimer".',
            'timestamp': 1456488895
        }
    }, {
        'url': 'http://www.lcp.fr/emissions/politique-matin/271085-politique-matin',
        'md5': '6cea4f7d13810464ef8485a924fc3333',
        'info_dict': {
            'id': '327336',
            'url': 're:http://httpod.scdn.arkena.com/11970/327336_[0-9]+.mp4',
            'ext': 'mp4',
            'title': 'Politique Matin - Politique matin',
            'upload_date': '20160225',
            'description': 'Politique Matin - Politique matin',
            'timestamp': 1456391602
        }
    }, {
        'url': 'http://www.lcp.fr/le-direct',
        'info_dict': {
            'title': 'Le direct | LCP Assembl\xe9e nationale',
            'id': 'le-direct',
        },
        'playlist_mincount': 1
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        # Extract the required info of the media files gathered in a dictionary
        media_dict = self.__extract_from_webpage(display_id, webpage)
        # Some web pages embed videos from other platforms like dailymotion, therefore we pass on these URLs
        if not media_dict:
            return self.url_result(url, 'Generic')

        # All videos are part of a playlist, a single video is also put in a playlist
        playlist_files_info = media_dict.get('Playlist')
        if not playlist_files_info:
            return self.url_result(url, 'Generic')

        media_files_info = playlist_files_info[0]
        video_formats = self.__get_video_formats(media_files_info)
        video_thumbnails = self.__get_thumbnails(media_files_info)
        video_timestamp = parse_iso8601(media_files_info.get('MediaInfo', {}).get('PublishDate'))

        title = self._og_search_title(webpage)
        description = self._html_search_regex(self._meta_regex('description'), webpage, 'description', group='content', default=title)

        return {
            'id': media_files_info.get('EntryName'),
            'title': title,
            'formats': video_formats,
            'thumbnails': video_thumbnails,
            'description': description,
            'timestamp': video_timestamp
        }

    def __extract_from_webpage(self, display_id, webpage):
        """Extracts the media info JSON object for the video for the provided web page."""
        embed_url = self.__extract_embed_url(webpage)
        embed_regex = r'(?:[a-zA-Z0-9]+\.)?lcp\.fr/embed/(?P<clip_id>[A-za-z0-9]+)/(?P<player_id>[A-za-z0-9]+)/(?P<skin_name>[^\/]+)'

        clip_id = self._search_regex(embed_regex, embed_url, 'clip id', group='clip_id', default=None)
        player_id = self._search_regex(embed_regex, embed_url, 'player id', group='player_id', default=None)
        skin_name = self._search_regex(embed_regex, embed_url, 'skin name', group='skin_name', default=None)

        # Check whether the matches failed, which might be when dealing with other players (e.g., dailymotion stream)
        if not clip_id or not player_id or not skin_name:
            return None

        return self.__extract_from_player(display_id, clip_id, player_id, skin_name)

    def __extract_embed_url(self, webpage):
        return self._search_regex(
            r'<iframe[^>]+src=(["\'])(?P<url>.+?)\1',
            webpage, 'embed url', group='url')

    def __extract_from_player(self, display_id, clip_id, player_id, skin_name):
        """Extracts the JSON object containing the required media info from the embedded arkena player"""
        arkena_url = 'http://play.arkena.com/config/avp/v1/player/media/{0}/{1}/{2}/?callbackMethod=?'.format(clip_id,
                                                                                                              skin_name,
                                                                                                              player_id)
        arkena_info = self._download_webpage(arkena_url, 'clip_info_' + clip_id)
        arkena_info_regex = r'\?\((?P<json>.*)\);'
        return self._parse_json(self._search_regex(arkena_info_regex, arkena_info, 'json', group='json'),
                                display_id)

    def __get_thumbnails(self, media_files_info):
        thumbnails = []
        media_thumbnail_info = media_files_info.get('MediaInfo', {}).get('Poster')
        if not media_thumbnail_info:
            return None
        for thumbnail in media_thumbnail_info:
            thumbnail_url = thumbnail.get('Url')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(thumbnail.get('Size'))
            })
        return thumbnails

    def __get_video_formats(self, media_files_info):
        formats = []
        media_files = media_files_info.get('MediaFiles')
        if not media_files:
            return None

        formats.extend(self.__get_mp4_video_formats(media_files))
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
