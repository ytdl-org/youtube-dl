# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    remove_end,
)


class NFLIE(InfoExtractor):
    IE_NAME = 'nfl.com'
    _VALID_URL = r'''(?x)
                    https?://
                        (?P<host>
                            (?:www\.)?
                            (?:
                                (?:
                                    nfl|
                                    buffalobills|
                                    miamidolphins|
                                    patriots|
                                    newyorkjets|
                                    baltimoreravens|
                                    bengals|
                                    clevelandbrowns|
                                    steelers|
                                    houstontexans|
                                    colts|
                                    jaguars|
                                    titansonline|
                                    denverbroncos|
                                    kcchiefs|
                                    raiders|
                                    chargers|
                                    dallascowboys|
                                    giants|
                                    philadelphiaeagles|
                                    redskins|
                                    chicagobears|
                                    detroitlions|
                                    packers|
                                    vikings|
                                    atlantafalcons|
                                    panthers|
                                    neworleanssaints|
                                    buccaneers|
                                    azcardinals|
                                    stlouisrams|
                                    49ers|
                                    seahawks
                                )\.com|
                                .+?\.clubs\.nfl\.com
                            )
                        )/
                        (?:.+?/)*
                        (?P<id>[^/#?&]+)
                    '''
    _TESTS = [{
        'url': 'http://www.nfl.com/videos/nfl-game-highlights/0ap3000000398478/Week-3-Redskins-vs-Eagles-highlights',
        'md5': '394ef771ddcd1354f665b471d78ec4c6',
        'info_dict': {
            'id': '0ap3000000398478',
            'ext': 'mp4',
            'title': 'Week 3: Redskins vs. Eagles highlights',
            'description': 'md5:56323bfb0ac4ee5ab24bd05fdf3bf478',
            'upload_date': '20140921',
            'timestamp': 1411337580,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://prod.www.steelers.clubs.nfl.com/video-and-audio/videos/LIVE_Post_Game_vs_Browns/9d72f26a-9e2b-4718-84d3-09fb4046c266',
        'md5': 'cf85bdb4bc49f6e9d3816d130c78279c',
        'info_dict': {
            'id': '9d72f26a-9e2b-4718-84d3-09fb4046c266',
            'ext': 'mp4',
            'title': 'LIVE: Post Game vs. Browns',
            'description': 'md5:6a97f7e5ebeb4c0e69a418a89e0636e8',
            'upload_date': '20131229',
            'timestamp': 1388354455,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'http://www.nfl.com/news/story/0ap3000000467586/article/patriots-seahawks-involved-in-lategame-skirmish',
        'info_dict': {
            'id': '0ap3000000467607',
            'ext': 'mp4',
            'title': 'Frustrations flare on the field',
            'description': 'Emotions ran high at the end of the Super Bowl on both sides of the ball after a dramatic finish.',
            'timestamp': 1422850320,
            'upload_date': '20150202',
        },
    }, {
        'url': 'http://www.patriots.com/video/2015/09/18/10-days-gillette',
        'md5': '4c319e2f625ffd0b481b4382c6fc124c',
        'info_dict': {
            'id': 'n-238346',
            'ext': 'mp4',
            'title': '10 Days at Gillette',
            'description': 'md5:8cd9cd48fac16de596eadc0b24add951',
            'timestamp': 1442618809,
            'upload_date': '20150918',
        },
    }, {
        'url': 'http://www.nfl.com/videos/nfl-network-top-ten/09000d5d810a6bd4/Top-10-Gutsiest-Performances-Jack-Youngblood',
        'only_matching': True,
    }, {
        'url': 'http://www.buffalobills.com/video/videos/Rex_Ryan_Show_World_Wide_Rex/b1dcfab2-3190-4bb1-bfc0-d6e603d6601a',
        'only_matching': True,
    }]

    @staticmethod
    def prepend_host(host, url):
        if not url.startswith('http'):
            if not url.startswith('/'):
                url = '/%s' % url
            url = 'http://{0:}{1:}'.format(host, url)
        return url

    @staticmethod
    def format_from_stream(stream, protocol, host, path_prefix='',
                           preference=0, note=None):
        url = '{protocol:}://{host:}/{prefix:}{path:}'.format(
            protocol=protocol,
            host=host,
            prefix=path_prefix,
            path=stream.get('path'),
        )
        return {
            'url': url,
            'vbr': int_or_none(stream.get('rate', 0), 1000),
            'preference': preference,
            'format_note': note,
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, host = mobj.group('id'), mobj.group('host')

        webpage = self._download_webpage(url, video_id)

        config_url = NFLIE.prepend_host(host, self._search_regex(
            r'(?:(?:config|configURL)\s*:\s*|<nflcs:avplayer[^>]+data-config\s*=\s*)(["\'])(?P<config>.+?)\1',
            webpage, 'config URL', default='static/content/static/config/video/config.json',
            group='config'))
        # For articles, the id in the url is not the video id
        video_id = self._search_regex(
            r'(?:<nflcs:avplayer[^>]+data-contentId\s*=\s*|contentId\s*:\s*)(["\'])(?P<id>.+?)\1',
            webpage, 'video id', default=video_id, group='id')
        config = self._download_json(config_url, video_id, 'Downloading player config')
        url_template = NFLIE.prepend_host(
            host, '{contentURLTemplate:}'.format(**config))
        video_data = self._download_json(
            url_template.format(id=video_id), video_id)

        formats = []
        cdn_data = video_data.get('cdnData', {})
        streams = cdn_data.get('bitrateInfo', [])
        if cdn_data.get('format') == 'EXTERNAL_HTTP_STREAM':
            parts = compat_urllib_parse_urlparse(cdn_data.get('uri'))
            protocol, host = parts.scheme, parts.netloc
            for stream in streams:
                formats.append(
                    NFLIE.format_from_stream(stream, protocol, host))
        else:
            cdns = config.get('cdns')
            if not cdns:
                raise ExtractorError('Failed to get CDN data', expected=True)

            for name, cdn in cdns.items():
                # LimeLight streams don't seem to work
                if cdn.get('name') == 'LIMELIGHT':
                    continue

                protocol = cdn.get('protocol')
                host = remove_end(cdn.get('host', ''), '/')
                if not (protocol and host):
                    continue

                prefix = cdn.get('pathprefix', '')
                if prefix and not prefix.endswith('/'):
                    prefix = '%s/' % prefix

                preference = 0
                if protocol == 'rtmp':
                    preference = -2
                elif 'prog' in name.lower():
                    preference = 1

                for stream in streams:
                    formats.append(
                        NFLIE.format_from_stream(stream, protocol, host,
                                                 prefix, preference, name))

        self._sort_formats(formats)

        thumbnail = None
        for q in ('xl', 'l', 'm', 's', 'xs'):
            thumbnail = video_data.get('imagePaths', {}).get(q)
            if thumbnail:
                break

        return {
            'id': video_id,
            'title': video_data.get('headline'),
            'formats': formats,
            'description': video_data.get('caption'),
            'duration': video_data.get('duration'),
            'thumbnail': thumbnail,
            'timestamp': int_or_none(video_data.get('posted'), 1000),
        }
