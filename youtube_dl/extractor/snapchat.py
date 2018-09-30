# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none, try_get


class SnapchatStoryIE(InfoExtractor):
    _VALID_URL = r'https?://(?:story|play)\.snapchat\.com/(?:s/)?(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://story.snapchat.com/s/m:W7_EDlXWTBiXAEEniNoMPwAAYHNdO123IQ281AWXc-zodAWXc-ziUAHanAA',
        'md5': '3eebf8f327752d100959db3fa0879bfb',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYHNdO123IQ281AWXc-zodAWXc-ziUAHanAA',
            'ext': 'mp4',
            'title': 'Dunn, North Carolina',
            'thumbnail': 'https://s.sc-cdn.net/N_FHqfPfsuaDG2vf33HsmA4ipcDtMBuW5SM3dBiME38=/default/preview_overlay.jpg',
        },
    }

    def _entries(self, story, title, alt_title):
        for snap in story.get('snaps', []):
            media = snap.get('media', {})

            if not media.get('type', '').startswith('VIDEO'):
                continue

            if len(media.keys()) == 0:
                continue

            formats = []

            for key in ('mediaStreamingUrl', 'mediaUrl'):
                if key not in media:
                    continue

                format_info = {'url': media[key], 'format_id': 'direct'}

                if key == 'mediaStreamingUrl':
                    format_info['format_id'] = 'streaming'
                    format_info['ext'] = 'mp4'
                    format_info['protocol'] = 'm3u8'

                formats.append(format_info)

            if len(formats) == 0:
                continue

            info = {
                'id': snap['id'],
                'title': title,
                'alt_title': alt_title,
                'thumbnail': media.get('mediaPreviewUrl'),
                'duration': int_or_none(snap.get('captureTimeSecs')),
                'formats': formats,
            }

            yield info

    def _real_extract(self, url):
        snap_id = self._match_id(url)
        data_url = 'https://storysharing.snapchat.com/v1/fetch/%s' % snap_id
        data = self._download_json(data_url,
                                   snap_id,
                                   query=dict(request_origin='ORIGIN_WEB_PLAYER'))

        story = data['story']
        title = try_get(story, lambda x: x['metadata']['title'], compat_str)
        if not title:
            title = 'Untitled'
        alt_title = try_get(story,
                            lambda x: x['metadata']['subTitles'],
                            compat_str)

        return self.playlist_result(self._entries(story, title, alt_title),
                                    playlist_title=title,
                                    playlist_id=snap_id,
                                    playlist_description=alt_title)


class SnapchatMapIE(InfoExtractor):
    _VALID_URL = r'https?://map\.snapchat\.com/(?:story|ttp)/[0-9a-f]+/snap/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://map.snapchat.com/story/1e8e6ce5c27f8623/snap/q4_OINadScux6p1c6OgxRwAAEs-Al6eIEtvT_AWYnxYFbAWYnxX26AAFRgA/@40.811408,-77.855252,13.00z',
        'md5': '966330c423dcf7d49fa9077c46bbb86d',
        'info_dict': {
            'id': 'q4_OINadScux6p1c6OgxRwAAEs-Al6eIEtvT_AWYnxYFbAWYnxX26AAFRgA',
            'title': 'State College, Pennsylvania',
            'ext': 'mp4',
            'thumbnail': 'https://s.sc-cdn.net/DScgzJV_rSLcJUubC03fcZECpi8KARIFRVtq5rEav2M=/default/preview_overlay.jpg',
        },
    }

    def _real_extract(self, url):
        snap_id = self._match_id(url)
        return self.url_result('https://story.snapchat.com/s/m:%s' % snap_id,
                               ie=SnapchatStoryIE.ie_key())
