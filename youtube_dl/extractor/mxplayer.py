from __future__ import unicode_literals

import re
from urllib.parse import urljoin
from .common import InfoExtractor
from ..utils import (
    url_or_none, js_to_json, ExtractorError)


# VALID_STREAMS = ('dash', 'hls', )
VALID_STREAMS = ('dash', )


class MxplayerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mxplayer\.in/movie/(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)'
    # _VALID_URL = r'https?://(?:www\.)?mxplayer\.in/movie/(?P<title>.*)[-](?P<id>.+)$'
    _TEST = {
        'url': 'https://www.mxplayer.in/movie/watch-knock-knock-hindi-dubbed-movie-online-b9fa28df3bfb8758874735bbd7d2655a?watch=true',
        'info_dict': {
            'id': 'b9fa28df3bfb8758874735bbd7d2655a',
            'ext': 'mp4',
            'title': 'Knock Knock Movie | Watch 2015 Knock Knock Full Movie Online- MX Player',
        },
        'params': {
            'skip_download': True,
            'format': 'bestvideo+bestaudio'
        }
    }

    def _get_best_stream_url(self, stream):
        best_stream = list(filter(None, [v for k, v in stream.items()]))
        return best_stream.pop(0) if len(best_stream) else None

    def _get_stream_urls(self, video_dict):
        stream_dict = video_dict.get('stream', {'provider': {}})
        stream_provider = stream_dict.get('provider')

        if not stream_dict[stream_provider]:
            message = 'No stream provider found'
            raise ExtractorError('%s said: %s' % (self.IE_NAME, message), expected=True)

        streams = []
        for stream_name, v in stream_dict[stream_provider].items():
            if stream_name in VALID_STREAMS:
                stream_url = self._get_best_stream_url(v)
                if stream_url is None:
                    continue
                streams.append((stream_name, stream_url))
        return streams

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_slug = mobj.group('slug')

        video_id = video_slug.split('-')[-1]

        webpage = self._download_webpage(url, video_id)

        window_state_json = self._html_search_regex(
            r'(?s)<script>window\.state\s*[:=]\s(\{.+\})\n(\w+).*(</script>).*',
            webpage, 'WindowState')

        source = self._parse_json(js_to_json(window_state_json), video_id)
        if not source:
            message = 'source not found'
            raise ExtractorError('%s said: %s' % (self.IE_NAME, message), expected=True)

        config_dict = source['config']
        video_dict = source['entities'][video_id]
        stream_urls = self._get_stream_urls(video_dict)

        title = self._og_search_title(webpage, fatal=True, default=video_dict['title'])

        formats = []
        headers = {'Referer': url}
        for stream_name, stream_url in stream_urls:
            if stream_name == 'dash':
                format_url = url_or_none(urljoin(config_dict['videoCdnBaseUrl'], stream_url))
                if not format_url:
                    continue
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', headers=headers))

        self._sort_formats(formats)
        info = {
            'id': video_id,
            'ext': 'mpd',
            'title': title,
            'description': video_dict.get('description'),
            'formats': formats
        }

        if video_dict.get('imageInfo'):
            info['thumbnails'] = list(map(lambda i: dict(i, **{
                'url': urljoin(config_dict['imageBaseUrl'], i['url'])
            }), video_dict['imageInfo']))

        if video_dict.get('webUrl'):
            last_part = video_dict['webUrl'].split("/")[-1]
            info['display_id'] = last_part.replace(video_id, "").rstrip("-")

        return info
