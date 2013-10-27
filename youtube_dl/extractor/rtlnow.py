# encoding: utf-8
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    ExtractorError,
)

class RTLnowIE(InfoExtractor):
    """Information Extractor for RTL NOW, RTL2 NOW, RTL NITRO, SUPER RTL NOW, VOX NOW and n-tv NOW"""
    _VALID_URL = r'(?:http://)?(?P<url>(?P<base_url>rtl-now\.rtl\.de/|rtl2now\.rtl2\.de/|(?:www\.)?voxnow\.de/|(?:www\.)?rtlnitronow\.de/|(?:www\.)?superrtlnow\.de/|(?:www\.)?n-tvnow\.de/)[a-zA-Z0-9-]+/[a-zA-Z0-9-]+\.php\?(?:container_id|film_id)=(?P<video_id>[0-9]+)&player=1(?:&season=[0-9]+)?(?:&.*)?)'
    _TESTS = [{
        u'url': u'http://rtl-now.rtl.de/ahornallee/folge-1.php?film_id=90419&player=1&season=1',
        u'file': u'90419.flv',
        u'info_dict': {
            u'upload_date': u'20070416', 
            u'title': u'Ahornallee - Folge 1 - Der Einzug',
            u'description': u'Folge 1 - Der Einzug',
        },
        u'params': {
            u'skip_download': True,
        },
        u'skip': u'Only works from Germany',
    },
    {
        u'url': u'http://rtl2now.rtl2.de/aerger-im-revier/episode-15-teil-1.php?film_id=69756&player=1&season=2&index=5',
        u'file': u'69756.flv',
        u'info_dict': {
            u'upload_date': u'20120519', 
            u'title': u'Ärger im Revier - Ein junger Ladendieb, ein handfester Streit...',
            u'description': u'Ärger im Revier - Ein junger Ladendieb, ein handfester Streit u.a.',
            u'thumbnail': u'http://autoimg.static-fra.de/rtl2now/219850/1500x1500/image2.jpg',
        },
        u'params': {
            u'skip_download': True,
        },
        u'skip': u'Only works from Germany',
    },
    {
        u'url': u'www.voxnow.de/voxtours/suedafrika-reporter-ii.php?film_id=13883&player=1&season=17',
        u'file': u'13883.flv',
        u'info_dict': {
            u'upload_date': u'20090627', 
            u'title': u'Voxtours - Südafrika-Reporter II',
            u'description': u'Südafrika-Reporter II',
        },
        u'params': {
            u'skip_download': True,
        },
    },
    {
        u'url': u'http://superrtlnow.de/medicopter-117/angst.php?film_id=99205&player=1',
        u'file': u'99205.flv',
        u'info_dict': {
            u'upload_date': u'20080928', 
            u'title': u'Medicopter 117 - Angst!',
            u'description': u'Angst!',
            u'thumbnail': u'http://autoimg.static-fra.de/superrtlnow/287529/1500x1500/image2.jpg'
        },
        u'params': {
            u'skip_download': True,
        },
    },
    {
        u'url': u'http://www.rtlnitronow.de/recht-ordnung/stadtpolizei-frankfurt-gerichtsvollzieher-leipzig.php?film_id=129679&player=1&season=1',
        u'file': u'129679.flv',
        u'info_dict': {
            u'upload_date': u'20131016', 
            u'title': u'Recht & Ordnung - Stadtpolizei Frankfurt/ Gerichtsvollzieher...',
            u'description': u'Stadtpolizei Frankfurt/ Gerichtsvollzieher Leipzig',
        },
        u'params': {
            u'skip_download': True,
        },
    },
    {
        u'url': u'http://www.n-tvnow.de/top-gear/episode-1-2013-01-01-00-00-00.php?film_id=124903&player=1&season=10',
        u'file': u'124903.flv',
        u'info_dict': {
            u'upload_date': u'20130101', 
            u'title': u'Top Gear vom 01.01.2013',
            u'description': u'Episode 1',
        },
        u'params': {
            u'skip_download': True,
        },
        u'skip': u'Only works from Germany',
    }]


    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)

        webpage_url = u'http://' + mobj.group('url')
        video_page_url = u'http://' + mobj.group('base_url')
        video_id = mobj.group(u'video_id')

        webpage = self._download_webpage(webpage_url, video_id)

        note_m = re.search(r'''(?sx)
            <div[ ]style="margin-left:[ ]20px;[ ]font-size:[ ]13px;">(.*?)
            <div[ ]id="playerteaser">''', webpage)
        if note_m:
            msg = clean_html(note_m.group(1))
            raise ExtractorError(msg)

        video_title = self._html_search_regex(r'<title>(?P<title>[^<]+?)( \| [^<]*)?</title>',
            webpage, u'title')
        playerdata_url = self._html_search_regex(r'\'playerdata\': \'(?P<playerdata_url>[^\']+)\'',
            webpage, u'playerdata_url')

        playerdata = self._download_webpage(playerdata_url, video_id)
        mobj = re.search(r'<title><!\[CDATA\[(?P<description>.+?)(?:\s+- (?:Sendung )?vom (?P<upload_date_d>[0-9]{2})\.(?P<upload_date_m>[0-9]{2})\.(?:(?P<upload_date_Y>[0-9]{4})|(?P<upload_date_y>[0-9]{2})) [0-9]{2}:[0-9]{2} Uhr)?\]\]></title>', playerdata)
        if mobj:
            video_description = mobj.group(u'description')
            if mobj.group('upload_date_Y'):
                video_upload_date = mobj.group('upload_date_Y')
            elif mobj.group('upload_date_y'):
                video_upload_date = u'20' + mobj.group('upload_date_y')
            else:
                video_upload_date = None
            if video_upload_date:
                video_upload_date += mobj.group('upload_date_m')+mobj.group('upload_date_d')
        else:
            video_description = None
            video_upload_date = None
            self._downloader.report_warning(u'Unable to extract description and upload date')

        # Thumbnail: not every video has an thumbnail
        mobj = re.search(r'<meta property="og:image" content="(?P<thumbnail>[^"]+)">', webpage)
        if mobj:
            video_thumbnail = mobj.group(u'thumbnail')
        else:
            video_thumbnail = None

        mobj = re.search(r'<filename [^>]+><!\[CDATA\[(?P<url>rtmpe://(?:[^/]+/){2})(?P<play_path>[^\]]+)\]\]></filename>', playerdata)
        if mobj is None:
            raise ExtractorError(u'Unable to extract media URL')
        video_url = mobj.group(u'url')
        video_play_path = u'mp4:' + mobj.group(u'play_path')
        video_player_url = video_page_url + u'includes/vodplayer.swf'

        return [{
            'id':          video_id,
            'url':         video_url,
            'play_path':   video_play_path,
            'page_url':    video_page_url,
            'player_url':  video_player_url,
            'ext':         'flv',
            'title':       video_title,
            'description': video_description,
            'upload_date': video_upload_date,
            'thumbnail':   video_thumbnail,
        }]
