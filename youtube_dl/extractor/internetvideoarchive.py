from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    int_or_none,
    xpath_text,
)


class InternetVideoArchiveIE(InfoExtractor):
    _VALID_URL = r'https?://video\.internetvideoarchive\.net/(?:player|flash/players)/.*?\?.*?publishedid.*?'

    _TEST = {
        'url': 'http://video.internetvideoarchive.net/player/6/configuration.ashx?customerid=69249&publishedid=194487&reporttag=vdbetatitle&playerid=641&autolist=0&domain=www.videodetective.com&maxrate=high&minrate=low&socialplayer=false',
        'info_dict': {
            'id': '194487',
            'ext': 'mp4',
            'title': 'KICK-ASS 2',
            'description': 'md5:c189d5b7280400630a1d3dd17eaa8d8a',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    @staticmethod
    def _build_json_url(query):
        return 'http://video.internetvideoarchive.net/player/6/configuration.ashx?' + query

    @staticmethod
    def _build_xml_url(query):
        return 'http://video.internetvideoarchive.net/flash/players/flashconfiguration.aspx?' + query

    def _real_extract(self, url):
        query = compat_urlparse.urlparse(url).query
        query_dic = compat_parse_qs(query)
        video_id = query_dic['publishedid'][0]

        if '/player/' in url:
            configuration = self._download_json(url, video_id)

            # There are multiple videos in the playlist whlie only the first one
            # matches the video played in browsers
            video_info = configuration['playlist'][0]

            formats = []
            for source in video_info['sources']:
                file_url = source['file']
                if determine_ext(file_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        file_url, video_id, ext='mp4', m3u8_id='hls'))
                else:
                    a_format = {
                        'url': file_url,
                    }

                    if source.get('label') and source['label'][-4:] == ' kbs':
                        tbr = int_or_none(source['label'][:-4])
                        a_format.update({
                            'tbr': tbr,
                            'format_id': 'http-%d' % tbr,
                        })
                        formats.append(a_format)

            self._sort_formats(formats)

            title = video_info['title']
            description = video_info.get('description')
            thumbnail = video_info.get('image')
        else:
            configuration = self._download_xml(url, video_id)
            formats = [{
                'url': xpath_text(configuration, './file', 'file URL', fatal=True),
            }]
            thumbnail = xpath_text(configuration, './image', 'thumbnail')
            title = 'InternetVideoArchive video %s' % video_id
            description = None

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
        }
