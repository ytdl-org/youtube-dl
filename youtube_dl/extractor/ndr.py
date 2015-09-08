# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


preferences = {'xl': 4, 'l': 3, 'm': 2, 's': 1, 'xs': 0,}


class NDRBaseIE(InfoExtractor):

    def extract_video_info(self, playlist, video_id):
        formats = []
        streamType = playlist.get('config').get('streamType')
        if streamType == 'httpVideo':
            for key, f in playlist.items():
                if key != 'config':
                    src = f['src']
                    if '.f4m' in src:
                        formats.extend(self._extract_f4m_formats(src, video_id))
                    elif '.m3u8' in src:
                        formats.extend(self._extract_m3u8_formats(src, video_id, fatal=False))
                    else:
                        quality = f.get('quality')
                        formats.append({
                            'url': src,
                            'format_id': quality,
                            'preference': preferences.get(quality),
                        })
        elif streamType == 'httpAudio':
            for key, f in playlist.items():
                if key != 'config':
                    formats.append({
                        'url': f['src'],
                        'format_id': 'mp3',
                        'vcodec': 'none',
                    })
        else:
            raise ExtractorError('No media links available for %s' % video_id)

        self._sort_formats(formats)

        config = playlist.get('config')

        title = config['title']
        duration = int_or_none(config.get('duration'))
        thumbnails = [{
            'id': thumbnail.get('quality'),
            'url': thumbnail.get('src'),
            'preference': preferences.get(thumbnail.get('quality'))
        } for thumbnail in config.get('poster').values()]

        return {
            'id': video_id,
            'title': title,
            'thumbnails': thumbnails,
            'duration': duration,
            'formats': formats,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_data = self._download_json('http://www.ndr.de/%s-ppjson.json' % video_id, video_id, fatal=False)

        if not json_data:
            webpage = self._download_webpage(url, video_id)
            embed_url = self._html_search_regex(r'<iframe[^>]+id="pp_\w+"[^>]+src="(/.*)"', webpage, 'embed url', None, False)
            if not embed_url:
                embed_url = self._html_search_meta('embedURL', webpage, fatal=False)
            if embed_url:
                if embed_url.startswith('/'):
                    return self.url_result('http://www.ndr.de%s' % embed_url, 'NDREmbed')
                else:
                    return self.url_result(embed_url, 'NDREmbed')
            raise ExtractorError('No media links available for %s' % video_id)

        return self.extract_video_info(json_data['playlist'], video_id)


class NDRIE(NDRBaseIE):
    IE_NAME = 'ndr'
    IE_DESC = 'NDR.de - Mediathek'
    _VALID_URL = r'https?://www\.ndr\.de/.+?,(?P<id>\w+)\.html'

    _TESTS = [
        {
            'url': 'http://www.ndr.de/fernsehen/sendungen/nordmagazin/Kartoffeltage-in-der-Lewitz,nordmagazin25866.html',
            'md5': '5bc5f5b92c82c0f8b26cddca34f8bb2c',
            'note': 'Video file',
            'info_dict': {
                'id': 'nordmagazin25866',
                'ext': 'mp4',
                'title': 'Kartoffeltage in der Lewitz',
                'duration': 166,
            },
            'skip': '404 Not found',
        },
        {
            'url': 'http://www.ndr.de/fernsehen/Party-Poette-und-Parade,hafengeburtstag988.html',
            'md5': 'dadc003c55ae12a5d2f6bd436cd73f59',
            'info_dict': {
                'id': 'hafengeburtstag988',
                'ext': 'mp4',
                'title': 'Party, Pötte und Parade',
                'duration': 3498,
            },
        },
        {
            'url': 'http://www.ndr.de/info/La-Valette-entgeht-der-Hinrichtung,audio51535.html',
            'md5': 'bb3cd38e24fbcc866d13b50ca59307b8',
            'note': 'Audio file',
            'info_dict': {
                'id': 'audio51535',
                'ext': 'mp3',
                'title': 'La Valette entgeht der Hinrichtung',
                'duration': 884,
            }
        }
    ]


class NJoyIE(NDRBaseIE):
    IE_NAME = 'N-JOY'
    _VALID_URL = r'https?://www\.n-joy\.de/.+?,(?P<id>\w+)\.html'

    _TEST = {
        'url': 'http://www.n-joy.de/entertainment/comedy/comedy_contest/Benaissa-beim-NDR-Comedy-Contest,comedycontest2480.html',
        'md5': 'cb63be60cd6f9dd75218803146d8dc67',
        'info_dict': {
            'id': 'comedycontest2480',
            'ext': 'mp4',
            'title': 'Benaissa beim NDR Comedy Contest',
            'duration': 654,
        }
    }


class NDREmbedBaseIE(NDRBaseIE):

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json('http://www.ndr.de/%s-ppjson.json' % video_id, video_id, fatal=False)
        if not json_data:
            raise ExtractorError('No media links available for %s' % video_id)
        return self.extract_video_info(json_data['playlist'], video_id)


class NDREmbedIE(NDREmbedBaseIE):
    IE_NAME = 'ndr:embed'
    _VALID_URL = r'https?://www\.ndr\.de/(?:[^/]+/)+(?P<id>[a-z0-9]+)-(?:player|externalPlayer)\.html'

    _TEST = {
        'url': 'http://www.ndr.de/fernsehen/sendungen/ndr_aktuell/ndraktuell28488-player.html',
        'md5': 'cb63be60cd6f9dd75218803146d8dc67',
        'info_dict': {
            'id': 'ndraktuell28488',
            'ext': 'mp4',
            'title': 'Norddeutschland begrüßt Flüchtlinge',
            'duration': 132,
        }
    }


class NJoyEmbedIE(NDREmbedBaseIE):
    IE_NAME = 'N-JOY:embed'
    _VALID_URL = r'https?://www\.n-joy\.de/(?:[^/]+/)+(?P<id>[a-z0-9]+)-(?:player|externalPlayer)\.html'

    _TEST = {
        'url': 'http://www.n-joy.de/entertainment/film/portraet374-player_image-832d9b79-fa8a-4026-92e2-e0fd99deb2f9_theme-n-joy.html',
        'md5': 'cb63be60cd6f9dd75218803146d8dc67',
        'info_dict': {
            'id': 'portraet374',
            'ext': 'mp4',
            'title': 'Viviane Andereggen - "Schuld um Schuld"',
            'duration': 129,
        }
    }
