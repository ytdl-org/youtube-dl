from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    int_or_none,
    qualities,
    urlencode_postdata,
    xpath_text,
)


class NFBIE(InfoExtractor):
    IE_NAME = 'nfb'
    IE_DESC = 'National Film Board of Canada'
    _VALID_URL = r'https?://(?:www\.)?(?:nfb|onf)\.ca/film/(?P<id>[\da-z_-]+)'

    _TEST = {
        'url': 'https://www.nfb.ca/film/qallunaat_why_white_people_are_funny',
        'info_dict': {
            'id': 'qallunaat_why_white_people_are_funny',
            'ext': 'flv',
            'title': 'Qallunaat! Why White People Are Funny ',
            'description': 'md5:6b8e32dde3abf91e58857b174916620c',
            'duration': 3128,
            'creator': 'Mark Sandiford',
            'uploader': 'Mark Sandiford',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        config = self._download_xml(
            'https://www.nfb.ca/film/%s/player_config' % video_id,
            video_id, 'Downloading player config XML',
            data=urlencode_postdata({'getConfig': 'true'}),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-NFB-Referer': 'http://www.nfb.ca/medias/flash/NFBVideoPlayer.swf'
            })

        title, description, thumbnail, duration, uploader, author = [None] * 6
        thumbnails, formats = [[]] * 2
        subtitles = {}

        for media in config.findall('./player/stream/media'):
            if media.get('type') == 'posterImage':
                quality_key = qualities(('low', 'high'))
                thumbnails = []
                for asset in media.findall('assets/asset'):
                    asset_url = xpath_text(asset, 'default/url', default=None)
                    if not asset_url:
                        continue
                    quality = asset.get('quality')
                    thumbnails.append({
                        'url': asset_url,
                        'id': quality,
                        'preference': quality_key(quality),
                    })
            elif media.get('type') == 'video':
                title = xpath_text(media, 'title', fatal=True)
                for asset in media.findall('assets/asset'):
                    quality = asset.get('quality')
                    height = int_or_none(self._search_regex(
                        r'^(\d+)[pP]$', quality or '', 'height', default=None))
                    for node in asset:
                        streamer = xpath_text(node, 'streamerURI', default=None)
                        if not streamer:
                            continue
                        play_path = xpath_text(node, 'url', default=None)
                        if not play_path:
                            continue
                        formats.append({
                            'url': streamer,
                            'app': streamer.split('/', 3)[3],
                            'play_path': play_path,
                            'rtmp_live': False,
                            'ext': 'flv',
                            'format_id': '%s-%s' % (node.tag, quality) if quality else node.tag,
                            'height': height,
                        })
                self._sort_formats(formats)
                description = clean_html(xpath_text(media, 'description'))
                uploader = xpath_text(media, 'author')
                duration = int_or_none(media.get('duration'))
                for subtitle in media.findall('./subtitles/subtitle'):
                    subtitle_url = xpath_text(subtitle, 'url', default=None)
                    if not subtitle_url:
                        continue
                    lang = xpath_text(subtitle, 'lang', default='en')
                    subtitles.setdefault(lang, []).append({
                        'url': subtitle_url,
                        'ext': (subtitle.get('format') or determine_ext(subtitle_url)).lower(),
                    })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'duration': duration,
            'creator': uploader,
            'uploader': uploader,
            'formats': formats,
            'subtitles': subtitles,
        }
