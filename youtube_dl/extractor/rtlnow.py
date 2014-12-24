# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    unified_strdate,
    int_or_none,
)


class RTLnowIE(InfoExtractor):
    """Information Extractor for RTL NOW, RTL2 NOW, RTL NITRO, SUPER RTL NOW, VOX NOW and n-tv NOW"""
    _VALID_URL = r'''(?x)
                        (?:https?://)?
                        (?P<url>
                            (?P<domain>
                                rtl-now\.rtl\.de|
                                rtl2now\.rtl2\.de|
                                (?:www\.)?voxnow\.de|
                                (?:www\.)?rtlnitronow\.de|
                                (?:www\.)?superrtlnow\.de|
                                (?:www\.)?n-tvnow\.de)
                            /+[a-zA-Z0-9-]+/[a-zA-Z0-9-]+\.php\?
                            (?:container_id|film_id)=(?P<video_id>[0-9]+)&
                            player=1(?:&season=[0-9]+)?(?:&.*)?
                        )'''

    _TESTS = [
        {
            'url': 'http://rtl-now.rtl.de/ahornallee/folge-1.php?film_id=90419&player=1&season=1',
            'info_dict': {
                'id': '90419',
                'ext': 'flv',
                'title': 'Ahornallee - Folge 1 - Der Einzug',
                'description': 'md5:ce843b6b5901d9a7f7d04d1bbcdb12de',
                'upload_date': '20070416',
                'duration': 1685,
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Only works from Germany',
        },
        {
            'url': 'http://rtl2now.rtl2.de/aerger-im-revier/episode-15-teil-1.php?film_id=69756&player=1&season=2&index=5',
            'info_dict': {
                'id': '69756',
                'ext': 'flv',
                'title': 'Ärger im Revier - Ein junger Ladendieb, ein handfester Streit u.a.',
                'description': 'md5:3fb247005ed21a935ffc82b7dfa70cf0',
                'thumbnail': 'http://autoimg.static-fra.de/rtl2now/219850/1500x1500/image2.jpg',
                'upload_date': '20120519',
                'duration': 1245,
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Only works from Germany',
        },
        {
            'url': 'http://www.voxnow.de/voxtours/suedafrika-reporter-ii.php?film_id=13883&player=1&season=17',
            'info_dict': {
                'id': '13883',
                'ext': 'flv',
                'title': 'Voxtours - Südafrika-Reporter II',
                'description': 'md5:de7f8d56be6fd4fed10f10f57786db00',
                'upload_date': '20090627',
                'duration': 1800,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://superrtlnow.de/medicopter-117/angst.php?film_id=99205&player=1',
            'info_dict': {
                'id': '99205',
                'ext': 'flv',
                'title': 'Medicopter 117 - Angst!',
                'description': 're:^Im Therapiezentrum \'Sonnalm\' kommen durch eine Unachtsamkeit die für die B.handlung mit Phobikern gehaltenen Voglespinnen frei\. Eine Ausreißerin',
                'thumbnail': 'http://autoimg.static-fra.de/superrtlnow/287529/1500x1500/image2.jpg',
                'upload_date': '20080928',
                'duration': 2691,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.n-tvnow.de/deluxe-alles-was-spass-macht/thema-ua-luxushotel-fuer-vierbeiner.php?container_id=153819&player=1&season=0',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_page_url = 'http://%s/' % mobj.group('domain')
        video_id = mobj.group('video_id')

        webpage = self._download_webpage('http://' + mobj.group('url'), video_id)

        mobj = re.search(r'(?s)<div style="margin-left: 20px; font-size: 13px;">(.*?)<div id="playerteaser">', webpage)
        if mobj:
            raise ExtractorError(clean_html(mobj.group(1)), expected=True)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        upload_date = unified_strdate(self._html_search_meta('uploadDate', webpage, 'upload date'))

        mobj = re.search(r'<meta itemprop="duration" content="PT(?P<seconds>\d+)S" />', webpage)
        duration = int(mobj.group('seconds')) if mobj else None

        playerdata_url = self._html_search_regex(
            r"'playerdata': '(?P<playerdata_url>[^']+)'", webpage, 'playerdata_url')

        playerdata = self._download_xml(playerdata_url, video_id, 'Downloading player data XML')

        videoinfo = playerdata.find('./playlist/videoinfo')

        formats = []
        for filename in videoinfo.findall('filename'):
            mobj = re.search(r'(?P<url>rtmpe://(?:[^/]+/){2})(?P<play_path>.+)', filename.text)
            if mobj:
                fmt = {
                    'url': mobj.group('url'),
                    'play_path': 'mp4:' + mobj.group('play_path'),
                    'page_url': video_page_url,
                    'player_url': video_page_url + 'includes/vodplayer.swf',
                }
            else:
                fmt = {
                    'url': filename.text,
                }
            fmt.update({
                'width': int_or_none(filename.get('width')),
                'height': int_or_none(filename.get('height')),
                'vbr': int_or_none(filename.get('bitrate')),
                'ext': 'flv',
            })
            formats.append(fmt)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
        }
