from __future__ import unicode_literals

import re

from .common import InfoExtractor


class IGNIE(InfoExtractor):
    """
    Extractor for some of the IGN sites, like www.ign.com, es.ign.com de.ign.com.
    Some videos of it.ign.com are also supported
    """

    _VALID_URL = r'https?://.+?\.ign\.com/(?P<type>videos|show_videos|articles|(?:[^/]*/feature))(/.+)?/(?P<name_or_id>.+)'
    IE_NAME = 'ign.com'

    _CONFIG_URL_TEMPLATE = 'http://www.ign.com/videos/configs/id/%s.config'
    _DESCRIPTION_RE = [
        r'<span class="page-object-description">(.+?)</span>',
        r'id="my_show_video">.*?<p>(.*?)</p>',
        r'<meta name="description" content="(.*?)"',
    ]

    _TESTS = [
        {
            'url': 'http://www.ign.com/videos/2013/06/05/the-last-of-us-review',
            'md5': 'eac8bdc1890980122c3b66f14bdd02e9',
            'info_dict': {
                'id': '8f862beef863986b2785559b9e1aa599',
                'ext': 'mp4',
                'title': 'The Last of Us Review',
                'description': 'md5:c8946d4260a4d43a00d5ae8ed998870c',
            }
        },
        {
            'url': 'http://me.ign.com/en/feature/15775/100-little-things-in-gta-5-that-will-blow-your-mind',
            'playlist': [
                {
                    'info_dict': {
                        'id': '5ebbd138523268b93c9141af17bec937',
                        'ext': 'mp4',
                        'title': 'GTA 5 Video Review',
                        'description': 'Rockstar drops the mic on this generation of games. Watch our review of the masterly Grand Theft Auto V.',
                    },
                },
                {
                    'info_dict': {
                        'id': '638672ee848ae4ff108df2a296418ee2',
                        'ext': 'mp4',
                        'title': '26 Twisted Moments from GTA 5 in Slow Motion',
                        'description': 'The twisted beauty of GTA 5 in stunning slow motion.',
                    },
                },
            ],
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ign.com/articles/2014/08/15/rewind-theater-wild-trailer-gamescom-2014?watch',
            'md5': '4e9a0bda1e5eebd31ddcf86ec0b9b3c7',
            'info_dict': {
                'id': '078fdd005f6d3c02f63d795faa1b984f',
                'ext': 'mp4',
                'title': 'Rewind Theater - Wild Trailer Gamescom 2014',
                'description': (
                    'Giant skeletons, bloody hunts, and captivating'
                    ' natural beauty take our breath away.'
                ),
            },
        },
    ]

    def _find_video_id(self, webpage):
        res_id = [
            r'"video_id"\s*:\s*"(.*?)"',
            r'data-video-id="(.+?)"',
            r'<object id="vid_(.+?)"',
            r'<meta name="og:image" content=".*/(.+?)-(.+?)/.+.jpg"',
            r'class="hero-poster[^"]*?"[^>]*id="(.+?)"',
        ]
        return self._search_regex(res_id, webpage, 'video id')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name_or_id = mobj.group('name_or_id')
        page_type = mobj.group('type')
        webpage = self._download_webpage(url, name_or_id)
        if page_type != 'video':
            multiple_urls = re.findall(
                '<param name="flashvars"[^>]*value="[^"]*?url=(https?://www\.ign\.com/videos/.*?)["&]',
                webpage)
            if multiple_urls:
                entries = [self.url_result(u, ie='IGN') for u in multiple_urls]
                return {
                    '_type': 'playlist',
                    'id': name_or_id,
                    'entries': entries,
                }

        video_id = self._find_video_id(webpage)
        result = self._get_video_info(video_id)
        description = self._html_search_regex(self._DESCRIPTION_RE,
                                              webpage, 'video description', flags=re.DOTALL)
        result['description'] = description
        return result

    def _get_video_info(self, video_id):
        config_url = self._CONFIG_URL_TEMPLATE % video_id
        config = self._download_json(config_url, video_id)
        media = config['playlist']['media']

        return {
            'id': media['metadata']['videoId'],
            'url': media['url'],
            'title': media['metadata']['title'],
            'thumbnail': media['poster'][0]['url'].replace('{size}', 'grande'),
        }


class OneUPIE(IGNIE):
    _VALID_URL = r'https?://gamevideos\.1up\.com/(?P<type>video)/id/(?P<name_or_id>.+)\.html'
    IE_NAME = '1up.com'

    _DESCRIPTION_RE = r'<div id="vid_summary">(.+?)</div>'

    _TESTS = [{
        'url': 'http://gamevideos.1up.com/video/id/34976.html',
        'md5': '68a54ce4ebc772e4b71e3123d413163d',
        'info_dict': {
            'id': '34976',
            'ext': 'mp4',
            'title': 'Sniper Elite V2 - Trailer',
            'description': 'md5:5d289b722f5a6d940ca3136e9dae89cf',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        result = super(OneUPIE, self)._real_extract(url)
        result['id'] = mobj.group('name_or_id')
        return result
