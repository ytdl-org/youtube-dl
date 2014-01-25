# encoding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    ExtractorError,
)


class RTLnowIE(InfoExtractor):
    """Information Extractor for RTL NOW, RTL2 NOW, RTL NITRO, SUPER RTL NOW, VOX NOW and n-tv NOW"""
    _VALID_URL = r'(?:http://)?(?P<url>(?P<domain>rtl-now\.rtl\.de|rtl2now\.rtl2\.de|(?:www\.)?voxnow\.de|(?:www\.)?rtlnitronow\.de|(?:www\.)?superrtlnow\.de|(?:www\.)?n-tvnow\.de)/+[a-zA-Z0-9-]+/[a-zA-Z0-9-]+\.php\?(?:container_id|film_id)=(?P<video_id>[0-9]+)&player=1(?:&season=[0-9]+)?(?:&.*)?)'
    _TESTS = [{
        'url': 'http://rtl-now.rtl.de/ahornallee/folge-1.php?film_id=90419&player=1&season=1',
        'file': '90419.flv',
        'info_dict': {
            'upload_date': '20070416',
            'title': 'Ahornallee - Folge 1 - Der Einzug',
            'description': 'Folge 1 - Der Einzug',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Only works from Germany',
    },
    {
        'url': 'http://rtl2now.rtl2.de/aerger-im-revier/episode-15-teil-1.php?film_id=69756&player=1&season=2&index=5',
        'file': '69756.flv',
        'info_dict': {
            'upload_date': '20120519',
            'title': 'Ärger im Revier - Ein junger Ladendieb, ein handfester Streit...',
            'description': 'Ärger im Revier - Ein junger Ladendieb, ein handfester Streit u.a.',
            'thumbnail': 'http://autoimg.static-fra.de/rtl2now/219850/1500x1500/image2.jpg',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Only works from Germany',
    },
    {
        'url': 'http://www.voxnow.de/voxtours/suedafrika-reporter-ii.php?film_id=13883&player=1&season=17',
        'file': '13883.flv',
        'info_dict': {
            'upload_date': '20090627',
            'title': 'Voxtours - Südafrika-Reporter II',
            'description': 'Südafrika-Reporter II',
        },
        'params': {
            'skip_download': True,
        },
    },
    {
        'url': 'http://superrtlnow.de/medicopter-117/angst.php?film_id=99205&player=1',
        'file': '99205.flv',
        'info_dict': {
            'upload_date': '20080928', 
            'title': 'Medicopter 117 - Angst!',
            'description': 'Angst!',
            'thumbnail': 'http://autoimg.static-fra.de/superrtlnow/287529/1500x1500/image2.jpg'
        },
        'params': {
            'skip_download': True,
        },
    },
    {
        'url': 'http://www.n-tvnow.de/top-gear/episode-1-2013-01-01-00-00-00.php?film_id=124903&player=1&season=10',
        'file': '124903.flv',
        'info_dict': {
            'upload_date': '20130101',
            'title': 'Top Gear vom 01.01.2013',
            'description': 'Episode 1',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Only works from Germany',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        webpage_url = 'http://' + mobj.group('url')
        video_page_url = 'http://' + mobj.group('domain') + '/'
        video_id = mobj.group('video_id')

        webpage = self._download_webpage(webpage_url, video_id)

        note_m = re.search(r'''(?sx)
            <div[ ]style="margin-left:[ ]20px;[ ]font-size:[ ]13px;">(.*?)
            <div[ ]id="playerteaser">''', webpage)
        if note_m:
            msg = clean_html(note_m.group(1))
            raise ExtractorError(msg)

        video_title = self._html_search_regex(
            r'<title>(?P<title>[^<]+?)( \| [^<]*)?</title>',
            webpage, 'title')
        playerdata_url = self._html_search_regex(
            r'\'playerdata\': \'(?P<playerdata_url>[^\']+)\'',
            webpage, 'playerdata_url')

        playerdata = self._download_webpage(playerdata_url, video_id)
        mobj = re.search(r'<title><!\[CDATA\[(?P<description>.+?)(?:\s+- (?:Sendung )?vom (?P<upload_date_d>[0-9]{2})\.(?P<upload_date_m>[0-9]{2})\.(?:(?P<upload_date_Y>[0-9]{4})|(?P<upload_date_y>[0-9]{2})) [0-9]{2}:[0-9]{2} Uhr)?\]\]></title>', playerdata)
        if mobj:
            video_description = mobj.group('description')
            if mobj.group('upload_date_Y'):
                video_upload_date = mobj.group('upload_date_Y')
            elif mobj.group('upload_date_y'):
                video_upload_date = '20' + mobj.group('upload_date_y')
            else:
                video_upload_date = None
            if video_upload_date:
                video_upload_date += mobj.group('upload_date_m') + mobj.group('upload_date_d')
        else:
            video_description = None
            video_upload_date = None
            self._downloader.report_warning('Unable to extract description and upload date')

        # Thumbnail: not every video has an thumbnail
        mobj = re.search(r'<meta property="og:image" content="(?P<thumbnail>[^"]+)">', webpage)
        if mobj:
            video_thumbnail = mobj.group('thumbnail')
        else:
            video_thumbnail = None

        mobj = re.search(r'<filename [^>]+><!\[CDATA\[(?P<url>rtmpe://(?:[^/]+/){2})(?P<play_path>[^\]]+)\]\]></filename>', playerdata)
        if mobj is None:
            raise ExtractorError('Unable to extract media URL')
        video_url = mobj.group('url')
        video_play_path = 'mp4:' + mobj.group('play_path')
        video_player_url = video_page_url + 'includes/vodplayer.swf'

        return {
            'id': video_id,
            'url': video_url,
            'play_path': video_play_path,
            'page_url': video_page_url,
            'player_url': video_player_url,
            'ext': 'flv',
            'title': video_title,
            'description': video_description,
            'upload_date': video_upload_date,
            'thumbnail': video_thumbnail,
        }
