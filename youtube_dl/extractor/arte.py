import re
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,

    ExtractorError,
    unified_strdate,
)

class ArteTvIE(InfoExtractor):
    """arte.tv information extractor."""

    _VALID_URL = r'(?:http://)?videos\.arte\.tv/(?:fr|de)/videos/.*'
    _LIVE_URL = r'index-[0-9]+\.html$'

    IE_NAME = u'arte.tv'

    def fetch_webpage(self, url):
        request = compat_urllib_request.Request(url)
        try:
            self.report_download_webpage(url)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve video webpage: %s' % compat_str(err))
        except ValueError as err:
            raise ExtractorError(u'Invalid URL: %s' % url)
        return webpage

    def grep_webpage(self, url, regex, regexFlags, matchTuples):
        page = self.fetch_webpage(url)
        mobj = re.search(regex, page, regexFlags)
        info = {}

        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        for (i, key, err) in matchTuples:
            if mobj.group(i) is None:
                raise ExtractorError(err)
            else:
                info[key] = mobj.group(i)

        return info

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

    def extractPlus7Stream(self, url):
        video_lang = url.split('/')[-3]
        info = self.grep_webpage(
            url,
            r'param name="movie".*?videorefFileUrl=(http[^\'"&]*)',
            0,
            [
                (1, 'url', u'Invalid URL: %s' % url)
            ]
        )
        next_url = compat_urllib_parse.unquote(info.get('url'))
        info = self.grep_webpage(
            next_url,
            r'<video lang="%s" ref="(http[^\'"&]*)' % video_lang,
            0,
            [
                (1, 'url', u'Could not find <video> tag: %s' % url)
            ]
        )
        next_url = compat_urllib_parse.unquote(info.get('url'))

        info = self.grep_webpage(
            next_url,
            r'<video id="(.*?)".*?>.*?' +
                '<name>(.*?)</name>.*?' +
                '<dateVideo>(.*?)</dateVideo>.*?' +
                '<url quality="hd">(.*?)</url>',
            re.DOTALL,
            [
                (1, 'id',    u'could not extract video id: %s' % url),
                (2, 'title', u'could not extract video title: %s' % url),
                (3, 'date',  u'could not extract video date: %s' % url),
                (4, 'url',   u'could not extract video url: %s' % url)
            ]
        )

        return {
            'id':           info.get('id'),
            'url':          compat_urllib_parse.unquote(info.get('url')),
            'uploader':     u'arte.tv',
            'upload_date':  unified_strdate(info.get('date')),
            'title':        info.get('title').decode('utf-8'),
            'ext':          u'mp4',
            'format':       u'NA',
            'player_url':   None,
        }

    def _real_extract(self, url):
        video_id = url.split('/')[-1]
        self.report_extraction(video_id)

        if re.search(self._LIVE_URL, video_id) is not None:
            raise ExtractorError(u'Arte live streams are not yet supported, sorry')
            # self.extractLiveStream(url)
            # return
        else:
            info = self.extractPlus7Stream(url)

        return [info]
