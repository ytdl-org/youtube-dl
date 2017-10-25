from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class IGNIE(InfoExtractor):
    """
    Extractor for some of the IGN sites, like www.ign.com, es.ign.com de.ign.com.
    Some videos of it.ign.com are also supported
    """

    _VALID_URL = r'https?://.+?\.ign\.com/(?:[^/]+/)?(?P<type>videos|show_videos|articles|feature|(?:[^/]+/\d+/video))(/.+)?/(?P<name_or_id>.+)'
    IE_NAME = 'ign.com'

    _API_URL_TEMPLATE = 'http://apis.ign.com/video/v3/videos/%s'
    _EMBED_RE = r'<iframe[^>]+?["\']((?:https?:)?//.+?\.ign\.com.+?/embed.+?)["\']'

    _TESTS = [
        {
            'url': 'http://www.ign.com/videos/2013/06/05/the-last-of-us-review',
            'md5': 'febda82c4bafecd2d44b6e1a18a595f8',
            'info_dict': {
                'id': '8f862beef863986b2785559b9e1aa599',
                'ext': 'mp4',
                'title': 'The Last of Us Review',
                'description': 'md5:c8946d4260a4d43a00d5ae8ed998870c',
                'timestamp': 1370440800,
                'upload_date': '20130605',
                'uploader_id': 'cberidon@ign.com',
            }
        },
        {
            'url': 'http://me.ign.com/en/feature/15775/100-little-things-in-gta-5-that-will-blow-your-mind',
            'info_dict': {
                'id': '100-little-things-in-gta-5-that-will-blow-your-mind',
            },
            'playlist': [
                {
                    'info_dict': {
                        'id': '5ebbd138523268b93c9141af17bec937',
                        'ext': 'mp4',
                        'title': 'GTA 5 Video Review',
                        'description': 'Rockstar drops the mic on this generation of games. Watch our review of the masterly Grand Theft Auto V.',
                        'timestamp': 1379339880,
                        'upload_date': '20130916',
                        'uploader_id': 'danieljkrupa@gmail.com',
                    },
                },
                {
                    'info_dict': {
                        'id': '638672ee848ae4ff108df2a296418ee2',
                        'ext': 'mp4',
                        'title': '26 Twisted Moments from GTA 5 in Slow Motion',
                        'description': 'The twisted beauty of GTA 5 in stunning slow motion.',
                        'timestamp': 1386878820,
                        'upload_date': '20131212',
                        'uploader_id': 'togilvie@ign.com',
                    },
                },
            ],
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ign.com/articles/2014/08/15/rewind-theater-wild-trailer-gamescom-2014?watch',
            'md5': '618fedb9c901fd086f6f093564ef8558',
            'info_dict': {
                'id': '078fdd005f6d3c02f63d795faa1b984f',
                'ext': 'mp4',
                'title': 'Rewind Theater - Wild Trailer Gamescom 2014',
                'description': 'Brian and Jared explore Michel Ancel\'s captivating new preview.',
                'timestamp': 1408047180,
                'upload_date': '20140814',
                'uploader_id': 'jamesduggan1990@gmail.com',
            },
        },
        {
            'url': 'http://me.ign.com/en/videos/112203/video/how-hitman-aims-to-be-different-than-every-other-s',
            'only_matching': True,
        },
        {
            'url': 'http://me.ign.com/ar/angry-birds-2/106533/video/lrd-ldyy-lwl-lfylm-angry-birds',
            'only_matching': True,
        },
        {
            # videoId pattern
            'url': 'http://www.ign.com/articles/2017/06/08/new-ducktales-short-donalds-birthday-doesnt-go-as-planned',
            'only_matching': True,
        },
    ]

    def _find_video_id(self, webpage):
        res_id = [
            r'"video_id"\s*:\s*"(.*?)"',
            r'class="hero-poster[^"]*?"[^>]*id="(.+?)"',
            r'data-video-id="(.+?)"',
            r'<object id="vid_(.+?)"',
            r'<meta name="og:image" content=".*/(.+?)-(.+?)/.+.jpg"',
            r'videoId&quot;\s*:\s*&quot;(.+?)&quot;',
            r'videoId["\']\s*:\s*["\']([^"\']+?)["\']',
        ]
        return self._search_regex(res_id, webpage, 'video id', default=None)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name_or_id = mobj.group('name_or_id')
        page_type = mobj.group('type')
        webpage = self._download_webpage(url, name_or_id)
        if page_type != 'video':
            multiple_urls = re.findall(
                r'<param name="flashvars"[^>]*value="[^"]*?url=(https?://www\.ign\.com/videos/.*?)["&]',
                webpage)
            if multiple_urls:
                entries = [self.url_result(u, ie='IGN') for u in multiple_urls]
                return {
                    '_type': 'playlist',
                    'id': name_or_id,
                    'entries': entries,
                }

        video_id = self._find_video_id(webpage)
        if not video_id:
            return self.url_result(self._search_regex(
                self._EMBED_RE, webpage, 'embed url'))
        return self._get_video_info(video_id)

    def _get_video_info(self, video_id):
        api_data = self._download_json(
            self._API_URL_TEMPLATE % video_id, video_id)

        formats = []
        m3u8_url = api_data['refs'].get('m3uUrl')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))
        f4m_url = api_data['refs'].get('f4mUrl')
        if f4m_url:
            formats.extend(self._extract_f4m_formats(
                f4m_url, video_id, f4m_id='hds', fatal=False))
        for asset in api_data['assets']:
            formats.append({
                'url': asset['url'],
                'tbr': asset.get('actual_bitrate_kbps'),
                'fps': asset.get('frame_rate'),
                'height': int_or_none(asset.get('height')),
                'width': int_or_none(asset.get('width')),
            })
        self._sort_formats(formats)

        thumbnails = [{
            'url': thumbnail['url']
        } for thumbnail in api_data.get('thumbnails', [])]

        metadata = api_data['metadata']

        return {
            'id': api_data.get('videoId') or video_id,
            'title': metadata.get('longTitle') or metadata.get('name') or metadata.get['title'],
            'description': metadata.get('description'),
            'timestamp': parse_iso8601(metadata.get('publishDate')),
            'duration': int_or_none(metadata.get('duration')),
            'display_id': metadata.get('slug') or video_id,
            'uploader_id': metadata.get('creator'),
            'thumbnails': thumbnails,
            'formats': formats,
        }


class OneUPIE(IGNIE):
    _VALID_URL = r'https?://gamevideos\.1up\.com/(?P<type>video)/id/(?P<name_or_id>.+)\.html'
    IE_NAME = '1up.com'

    _TESTS = [{
        'url': 'http://gamevideos.1up.com/video/id/34976.html',
        'md5': 'c9cc69e07acb675c31a16719f909e347',
        'info_dict': {
            'id': '34976',
            'ext': 'mp4',
            'title': 'Sniper Elite V2 - Trailer',
            'description': 'md5:bf0516c5ee32a3217aa703e9b1bc7826',
            'timestamp': 1313099220,
            'upload_date': '20110811',
            'uploader_id': 'IGN',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        result = super(OneUPIE, self)._real_extract(url)
        result['id'] = mobj.group('name_or_id')
        return result


class PCMagIE(IGNIE):
    _VALID_URL = r'https?://(?:www\.)?pcmag\.com/(?P<type>videos|article2)(/.+)?/(?P<name_or_id>.+)'
    IE_NAME = 'pcmag'

    _EMBED_RE = r'iframe\.setAttribute\("src",\s*__util.objToUrlString\("http://widgets\.ign\.com/video/embed/content\.html?[^"]*url=([^"]+)["&]'

    _TESTS = [{
        'url': 'http://www.pcmag.com/videos/2015/01/06/010615-whats-new-now-is-gogo-snooping-on-your-data',
        'md5': '212d6154fd0361a2781075f1febbe9ad',
        'info_dict': {
            'id': 'ee10d774b508c9b8ec07e763b9125b91',
            'ext': 'mp4',
            'title': '010615_What\'s New Now: Is GoGo Snooping on Your Data?',
            'description': 'md5:a7071ae64d2f68cc821c729d4ded6bb3',
            'timestamp': 1420571160,
            'upload_date': '20150106',
            'uploader_id': 'cozzipix@gmail.com',
        }
    }, {
        'url': 'http://www.pcmag.com/article2/0,2817,2470156,00.asp',
        'md5': '94130c1ca07ba0adb6088350681f16c1',
        'info_dict': {
            'id': '042e560ba94823d43afcb12ddf7142ca',
            'ext': 'mp4',
            'title': 'HTC\'s Weird New Re Camera - What\'s New Now',
            'description': 'md5:53433c45df96d2ea5d0fda18be2ca908',
            'timestamp': 1412953920,
            'upload_date': '20141010',
            'uploader_id': 'chris_snyder@pcmag.com',
        }
    }]
