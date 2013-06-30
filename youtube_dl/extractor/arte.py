import re
import json

from .common import InfoExtractor
from ..utils import (
    # This is used by the not implemented extractLiveStream method
    compat_urllib_parse,

    ExtractorError,
    unified_strdate,
)

class ArteTvIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?www\.arte.tv/guide/(?:fr|de)/(?:(?:sendungen|emissions)/)?(?P<id>.*?)/(?P<name>.*?)(\?.*)?'
    _LIVE_URL = r'index-[0-9]+\.html$'

    IE_NAME = u'arte.tv'

    # TODO implement Live Stream
    # def extractLiveStream(self, url):
    #     video_lang = url.split('/')[-4]
    #     info = self.grep_webpage(
    #         url,
    #         r'src="(.*?/videothek_js.*?\.js)',
    #         0,
    #         [
    #             (1, 'url', u'Invalid URL: %s' % url)
    #         ]
    #     )
    #     http_host = url.split('/')[2]
    #     next_url = 'http://%s%s' % (http_host, compat_urllib_parse.unquote(info.get('url')))
    #     info = self.grep_webpage(
    #         next_url,
    #         r'(s_artestras_scst_geoFRDE_' + video_lang + '.*?)\'.*?' +
    #             '(http://.*?\.swf).*?' +
    #             '(rtmp://.*?)\'',
    #         re.DOTALL,
    #         [
    #             (1, 'path',   u'could not extract video path: %s' % url),
    #             (2, 'player', u'could not extract video player: %s' % url),
    #             (3, 'url',    u'could not extract video url: %s' % url)
    #         ]
    #     )
    #     video_url = u'%s/%s' % (info.get('url'), info.get('path'))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        # This is not a real id, it can be for example AJT for the news
        # http://www.arte.tv/guide/fr/emissions/AJT/arte-journal
        video_id = mobj.group('id')

        if re.search(self._LIVE_URL, video_id) is not None:
            raise ExtractorError(u'Arte live streams are not yet supported, sorry')
            # self.extractLiveStream(url)
            # return

        webpage = self._download_webpage(url, video_id)
        json_url = self._html_search_regex(r'arte_vp_url="(.*?)"', webpage, 'json url')

        json_info = self._download_webpage(json_url, video_id, 'Downloading info json')
        self.report_extraction(video_id)
        info = json.loads(json_info)
        player_info = info['videoJsonPlayer']

        info_dict = {'id': player_info['VID'],
                     'title': player_info['VTI'],
                     'description': player_info['VDE'],
                     'upload_date': unified_strdate(player_info['VDA'].split(' ')[0]),
                     'thumbnail': player_info['programImage'],
                     }

        formats = player_info['VSR'].values()
        # We order the formats by quality
        formats = sorted(formats, key=lambda f: int(f['height']))
        # Pick the best quality
        format_info = formats[-1]
        if format_info['mediaType'] == u'rtmp':
            info_dict['url'] = format_info['streamer']
            info_dict['play_path'] = 'mp4:' + format_info['url']
            info_dict['ext'] = 'mp4'
        else:
            info_dict['url'] = format_info['url']
            info_dict['ext'] = 'mp4'

        return info_dict
