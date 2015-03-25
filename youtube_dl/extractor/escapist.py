from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    js_to_json,
    parse_duration,
)


class EscapistIE(InfoExtractor):
    _VALID_URL = r'https?://?(www\.)?escapistmagazine\.com/videos/view/[^/?#]+/(?P<id>[0-9]+)-[^/?#]*(?:$|[?#])'
    _TEST = {
        'url': 'http://www.escapistmagazine.com/videos/view/the-escapist-presents/6618-Breaking-Down-Baldurs-Gate',
        'md5': 'ab3a706c681efca53f0a35f1415cf0d1',
        'info_dict': {
            'id': '6618',
            'ext': 'mp4',
            'description': "Baldur's Gate: Original, Modded or Enhanced Edition? I'll break down what you can expect from the new Baldur's Gate: Enhanced Edition.",
            'uploader_id': 'the-escapist-presents',
            'uploader': 'The Escapist Presents',
            'title': "Breaking Down Baldur's Gate",
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 264,
        }
    }

    def _real_extract(self, url):
        def _gen_useragent(id):
            base_ua = 'Mozilla/5.0 ({0}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{1}.0.{2}.{3} Safari/537.36'

            os = [
                'Windows NT 6.3; WOW64',
                'Windows NT 6.2; WOW64',
                'Windows NT 6.1; WOW64',
                'Windows NT 5.1',
                'X11; Linux x86_64',
                'X11; Linux i686',
                'Macintosh; Intel Mac OS X 10_9_3',
                'Macintosh; Intel Mac OS X 10_6_8'
            ]

            return base_ua.format(os[id % len(os)], (id % 10) + 30, id % 3000, id % 100)

        video_id = self._match_id(url)
        user_agent = _gen_useragent(int(video_id))
        webpage_req = compat_urllib_request.Request(url)
        webpage_req.add_header('User-Agent', user_agent)
        webpage = self._download_webpage(webpage_req, video_id)

        uploader_id = self._html_search_regex(
            r"<h1\s+class='headline'>\s*<a\s+href='/videos/view/(.*?)'",
            webpage, 'uploader ID', fatal=False)
        uploader = self._html_search_regex(
            r"<h1\s+class='headline'>(.*?)</a>",
            webpage, 'uploader', fatal=False)
        description = self._html_search_meta('description', webpage)
        duration = parse_duration(self._html_search_meta('duration', webpage))

        raw_title = self._html_search_meta('title', webpage, fatal=True)
        title = raw_title.partition(' : ')[2]

        config_url = compat_urllib_parse.unquote(self._html_search_regex(
            r'''(?x)
            (?:
                <param\s+name="flashvars".*?\s+value="config=|
                flashvars=&quot;config=
            )
            (https?://[^"&]+)
            ''',
            webpage, 'config URL'))

        formats = []
        ad_formats = []

        def _add_format(name, cfg_url, user_agent, quality):
            cfg_req = compat_urllib_request.Request(cfg_url)
            cfg_req.add_header('User-Agent', user_agent)
            config = self._download_json(
                cfg_req, video_id,
                'Downloading ' + name + ' configuration',
                'Unable to download ' + name + ' configuration',
                transform_source=js_to_json)

            playlist = config['playlist']
            for p in playlist:
                if p.get('eventCategory') == 'Video':
                    ar = formats
                elif p.get('eventCategory') == 'Video Postroll':
                    ar = ad_formats
                else:
                    continue

                ar.append({
                    'url': p['url'],
                    'format_id': name,
                    'quality': quality,
                    'http_headers': {
                        'User-Agent': user_agent,
                    },
                })

        _add_format('normal', config_url, user_agent, quality=0)
        hq_url = (config_url +
                  ('&hq=1' if '?' in config_url else config_url + '?hq=1'))
        try:
            _add_format('hq', hq_url, user_agent, quality=1)
        except ExtractorError:
            pass  # That's fine, we'll just use normal quality
        self._sort_formats(formats)

        if '/escapist/sales-marketing/' in formats[-1]['url']:
            raise ExtractorError('This IP address has been blocked by The Escapist', expected=True)

        res = {
            'id': video_id,
            'formats': formats,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': description,
            'duration': duration,
        }

        if self._downloader.params.get('include_ads') and ad_formats:
            self._sort_formats(ad_formats)
            ad_res = {
                'id': '%s-ad' % video_id,
                'title': '%s (Postroll)' % title,
                'formats': ad_formats,
            }
            return {
                '_type': 'playlist',
                'entries': [res, ad_res],
                'title': title,
                'id': video_id,
            }

        return res
