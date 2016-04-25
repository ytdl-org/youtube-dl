from __future__ import unicode_literals

from .theplatform import ThePlatformIE
from ..utils import (
    xpath_text,
    xpath_element,
    int_or_none,
    find_xpath_attr,
)


class CBSBaseIE(ThePlatformIE):
    def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        closed_caption_e = find_xpath_attr(smil, self._xpath_ns('.//param', namespace), 'name', 'ClosedCaptionURL')
        return {
            'en': [{
                'ext': 'ttml',
                'url': closed_caption_e.attrib['value'],
            }]
        } if closed_caption_e is not None and closed_caption_e.attrib.get('value') else []


class CBSIE(CBSBaseIE):
    _VALID_URL = r'https?://(?:www\.)?(?:cbs\.com/shows/[^/]+/(?:video|artist)|colbertlateshow\.com/(?:video|podcasts))/[^/]+/(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'info_dict': {
            'id': '_u7W953k6la293J7EPTd9oHkSPs6Xn6_',
            'display_id': 'connect-chat-feat-garth-brooks',
            'ext': 'mp4',
            'title': 'Connect Chat feat. Garth Brooks',
            'description': 'Connect with country music singer Garth Brooks, as he chats with fans on Wednesday November 27, 2013. Be sure to tune in to Garth Brooks: Live from Las Vegas, Friday November 29, at 9/8c on CBS!',
            'duration': 1495,
            'timestamp': 1385585425,
            'upload_date': '20131127',
            'uploader': 'CBSI-NEW',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        '_skip': 'Blocked outside the US',
    }, {
        'url': 'http://www.cbs.com/shows/liveonletterman/artist/221752/st-vincent/',
        'info_dict': {
            'id': 'WWF_5KqY3PK1',
            'display_id': 'st-vincent',
            'ext': 'flv',
            'title': 'Live on Letterman - St. Vincent',
            'description': 'Live On Letterman: St. Vincent in concert from New York\'s Ed Sullivan Theater on Tuesday, July 16, 2014.',
            'duration': 3221,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        '_skip': 'Blocked outside the US',
    }, {
        'url': 'http://colbertlateshow.com/video/8GmB0oY0McANFvp2aEffk9jZZZ2YyXxy/the-colbeard/',
        'only_matching': True,
    }, {
        'url': 'http://www.colbertlateshow.com/podcasts/dYSwjqPs_X1tvbV_P2FcPWRa_qT6akTC/in-the-bad-room-with-stephen/',
        'only_matching': True,
    }]
    TP_RELEASE_URL_TEMPLATE = 'http://link.theplatform.com/s/dJ5BDC/%s?mbr=true'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        content_id = self._search_regex(
            [r"video\.settings\.content_id\s*=\s*'([^']+)';", r"cbsplayer\.contentId\s*=\s*'([^']+)';"],
            webpage, 'content id')
        items_data = self._download_xml(
            'http://can.cbs.com/thunder/player/videoPlayerService.php',
            content_id, query={'partner': 'cbs', 'contentId': content_id})
        video_data = xpath_element(items_data, './/item')
        title = xpath_text(video_data, 'videoTitle', 'title', True)

        subtitles = {}
        formats = []
        for item in items_data.findall('.//item'):
            pid = xpath_text(item, 'pid')
            if not pid:
                continue
            tp_release_url = self.TP_RELEASE_URL_TEMPLATE % pid
            if '.m3u8' in xpath_text(item, 'contentUrl', default=''):
                tp_release_url += '&manifest=m3u'
            tp_formats, tp_subtitles = self._extract_theplatform_smil(
                tp_release_url, content_id, 'Downloading %s SMIL data' % pid)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        self._sort_formats(formats)

        info = self.get_metadata('dJ5BDC/media/guid/2198311517/%s' % content_id, content_id)
        info.update({
            'id': content_id,
            'display_id': display_id,
            'title': title,
            'series': xpath_text(video_data, 'seriesTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
            'duration': int_or_none(xpath_text(video_data, 'videoLength'), 1000),
            'thumbnail': xpath_text(video_data, 'previewImageURL'),
            'formats': formats,
            'subtitles': subtitles,
        })
        return info
