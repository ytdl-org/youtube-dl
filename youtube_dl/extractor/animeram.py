import re
import json
from .common import InfoExtractor
from ..utils import (
    ExtractorError
)

sources = (
    "animebam","auengine","mp4upload","videoweed","videonest"
)

def get_video_source(embed_page_url):
    video_source = ""

    for source in sources:
        if source in embed_page_url:
            video_source = source
            break

    return video_source

## adding implementations for the major sources available to download in the animeram webpage. the regex may change in future if the respective sites have changed impl
def get_video_url(instance,video_source,webpage):
   if "animebam" in video_source  :
       player_setup_str = re.compile(r'sources:.*"}]').search(webpage).group(0)
       player_setup_str = player_setup_str.replace('file','"file"').replace('label','"label"').replace('sources:','')
       player_setup_json = json.loads(player_setup_str)

       map = {}
       for item in player_setup_json:
           ## animebam has 2 cdn servers one is om126 and other is om139 but its not guaranteed that both have all files
           ## so better choose another source ? since probability is 0.5
           map[item["label"]] = item["file"].replace('cdn',"om139.cdn").replace("/video","")

       return map["720p"]
   if "auengine" in video_source:
       return re.compile(r'.*video_link\s+=\s+\'(?P<url>[^\']+).*').search(webpage).group('url')
   if "mp4upload" in video_source:
       return  re.compile(r'\'(?P<url>http.*[.]mp4)\'').search(webpage).group('url')
   if "videonest" in video_source:
       player_setup_str = re.compile(r'sources:.*"}]').search(webpage).group(0)
       player_setup_str = player_setup_str.replace('file','"file"').replace('label','"label"').replace('sources:','')
       player_setup_json = json.loads(player_setup_str)
       return player_setup_json[0]["file"]
   if "videoweed" in video_source:
       key = re.compile(r'.*fkz\s?=\s?"(?P<key>[^"]+).*').search(webpage).group('key')
       file = re.compile(r'.*flashvars.file\s?=\s?"(?P<file>[^"]+).*').search(webpage).group('file')
       url = "http://www.videoweed.es/api/player.api.php?file="+file+"&key="+key
       response = instance._download_webpage(url,"")
       pairs = [s2 for s1 in response.split('&') for s2 in s1.split(';')]
       return pairs[0].split('=')[1]

class AnimeRamIE(InfoExtractor):
    _VALID_URL = r'http://(?:\w+\.)?animeram\.me/(?:[\w\-]+\/)(?P<id>[\w]+)(/?)(?:[\w+\d+]?)'
    _TESTS = [{
        'url': 'http://www.animeram.me/one-piece-streaming/700/',
        'md5': '6c418c3bc4e595938b2ae3b1b87fc5c3',
        'info_dict': {
            'id': '700',
            'ext': 'mp4',
            'title': 'One Piece Episode 700',
        }
    }, {
        'url': 'http://www.animeram.me/one-piece-streaming/689/5/',
        'md5': 'd86e4db4ac00bf77906886ab8ac9b7f8',
        'info_dict': {
            'id': '689',
            'ext': 'mp4',
            'title': 'One Piece Episode 689',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        age_limit = self._rta_search(webpage)
        video_title = re.compile(r'javascript:void\(0\)"\s?title="(?P<title>[^"]+)"').search(webpage).group('title')

        embed_page_url = re.findall(r'https?://[\w+\.+\?+\&+/+=+]+embed[\w\.\?\&/=-]+', webpage, 0)[1]
        video_source = get_video_source(embed_page_url)

        if video_source == "":
            raise ExtractorError("unable to download for the given page since source is not supported or found."
                                 "Please try with other source by clicking tabs in the page")

        webpage = self._download_webpage(embed_page_url, video_id, note='downloading embed page')
        this = self

        # Get the video URL
        video_url = get_video_url(this,video_source,webpage)

        if video_url == "":
            raise ExtractorError("unable to download for the given page, maybe html markup has changed for url."
                                 "Please try with other source by clicking tabs in the page")

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': 'mp4',
            'format': 'mp4',
            'player_url': embed_page_url,
            'age_limit': age_limit,
        }

