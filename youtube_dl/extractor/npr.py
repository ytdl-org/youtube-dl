from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class NprBaseIE(InfoExtractor):
    def extract_info(self, id):
        json_data = self._download_json(
            'http://api.npr.org/query', id, query={
                'id': id,
                'fields': 'titles,audio,show,multimedia,text',
                'format': 'json',
                'apiKey': 'MDAzMzQ2MjAyMDEyMzk4MTU1MDg3ZmM3MQ010',
            })

        return json_data['list']['story'][0]

    def extract_formats(self, media_info):
        FORMATS_ = {
            'hls': 'm3u8', 'hlsOnDemand': 'm3u8', 'mediastream': 'mp3',
            'mp3': 'mp3', 'mp4': 'mp4', 'wm': 'wm', 'threegp': '3gp'
        }

        formats = []
        for format_id, formats_entry in media_info.get('format', {}).items():
            if not formats_entry:
                continue
            if isinstance(formats_entry, list):
                formats_entry = formats_entry[0]
            format_url = formats_entry.get('$text')
            if not format_url:
                continue
            if format_id == 'smil':
                formats += self._extract_smil_formats(
                    format_url,
                    media_info['id'],
                    fatal=False
                )
                continue
            elif format_id == 'm3u8':
                # Error 404 for some reason
                formats += self._extract_m3u8_formats(
                    format_url,
                    media_info['id'],
                    fatal=False
                )
                continue
            formats.append({
                'url': format_url,
                'format_id': format_id,
                'ext': FORMATS_.get(format_id),
            })
        return formats


class NprPlaylistIE(NprBaseIE):
    _VALID_URL = r'https?://(?:www\.)?npr\.org/(?:sections/\w+/\d+/\d+/\d+/|player/v2/mediaPlayer\.html\?.*\bid=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.npr.org/sections/allsongs/2015/10/21/449974205/new-music-from-beach-house-chairlift-cmj-discoveries-and-more',
        'info_dict': {
            'id': '449974205',
            'title': 'New Music From Beach House, Chairlift, CMJ Discoveries And More'
        },
        'playlist_count': 7,
    }, {
        'url': 'http://www.npr.org/sections/deceptivecadence/2015/10/09/446928052/music-from-the-shadows-ancient-armenian-hymns-and-piano-jazz',
        'info_dict': {
            'id': '446928052',
            'title': "Songs We Love: Tigran Hamasyan, 'Your Mercy is Boundless'"
        },
        'playlist': [{
            'md5': 'df2917b738fdd2358a9f0e7e49fcdf2e',
            'info_dict': {
                'id': '446929930',
                # 'ext': 'mp4',
                'title': 'Your Mercy is Boundless (Bazum en Qo gtutyunqd)',
                'duration': 402,
            },
        }],
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        story = self.extract_info(playlist_id)

        entries = []
        for audio in story.get('audio', []):
            title = audio.get('title', {}).get('$text')
            duration = int_or_none(audio.get('duration', {}).get('$text'))
            entries.append({
                'id': audio['id'],
                'title': title,
                'duration': duration,
                'formats': self.extract_formats(audio),
            })

        playlist_title = story.get('title', {}).get('$text')
        return self.playlist_result(entries, playlist_id, playlist_title)


class NprVideoIE(NprBaseIE):
    _VALID_URL = r'https?://(?:www\.)?npr\.org/event/music/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.npr.org/event/music/533198237/tigers-jaw-tiny-desk-concert',
        'md5': '5b385e0e96c2731261df9a4ed1ff2cba',
        'info_dict': {
            'id': '533201718',
            'display_id': '533198237',
            'title': 'Tigers Jaw: Tiny Desk Concert',
            'ext': 'mp4',
            'width': 624,
            'height': 351,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        story = self.extract_info(display_id)

        video = story.get('multimedia')[0]

        return {
            'url': url,
            'display_id': display_id,
            'title': story.get('title', {}).get('$text'),
            'id': video.get('id'),
            'duration': int_or_none(video.get('duration', {}).get('$text')),
            'formats': self.extract_formats(video),
            'width': int_or_none(video.get('width', {}).get('$text')),
            'height': int_or_none(video.get('height', {}).get('$text')),
        }
