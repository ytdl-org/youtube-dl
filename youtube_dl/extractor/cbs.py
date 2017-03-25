from __future__ import unicode_literals

from .common import InfoExtractor
from .theplatform import ThePlatformFeedIE
from ..utils import (
    int_or_none,
    js_to_json,
    find_xpath_attr,
    RegexNotFoundError,
    xpath_element,
    xpath_text,
    update_url_query,
    urljoin,
)


class CBSBaseIE(ThePlatformFeedIE):
    def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        closed_caption_e = find_xpath_attr(smil, self._xpath_ns('.//param', namespace), 'name', 'ClosedCaptionURL')
        return {
            'en': [{
                'ext': 'ttml',
                'url': closed_caption_e.attrib['value'],
            }]
        } if closed_caption_e is not None and closed_caption_e.attrib.get('value') else []

class CBSShowIE(InfoExtractor):
    IE_DESC = 'CBS show playlists, including full episodes and clips'
    IE_NAME = 'cbs.com:playlist'
    _VALID_URL = r'(?i)https?://(?:www\.)cbs.com/shows/(?P<id>[\w-]+)/?$'
    _TEST = {
        'url': 'http://www.cbs.com/shows/the-late-show-with-stephen-colbert',
        'info_dict': {
            'id': 61456254,
            'title': 'The Late Show with Stephen Colbert',
        },
        'playlist_mincount': 14,
    }

    def carousel_playlist(self, url, type):
        carousel = self._download_json(url, 'Downloading %s carousel' % type)
        episodes = carousel['result']['data']
        carousel_title = episodes[0]['series_title']

        entries = []
        for ep in episodes:
            entries.append(self.url_result(
                urljoin(url, ep['app_url']),
                'CBS',
                ep['content_id'],
                ep['episode_title']))

        return self.playlist_result(entries, playlist_title=carousel_title)

    def _real_extract(self, url):
        show_name = self._match_id(url)
        webpage = self._download_webpage(url, show_name)

        # not-quite JSON, no double-quotes:
        #  var show = new CBS.Show({id:61456254});
        show_id_json = self._search_regex(r'new CBS\.Show\(([^)]*)\);', webpage, 'show_id')

        show = self._parse_json(show_id_json, show_name, transform_source=js_to_json)

        # Found in http://www.cbs.com/assets/min/js/min/com.cbs.min.js?20170303-224247
        # unminified at http://www.cbs.com/assets/js/min/com.cbs.js
        # http://www.cbs.com/carousels/shows/61456254/offset/0/limit/15/xs/0/
        # => {id: 240172, title: "Full Episodes",
        episodes_url = urljoin(url, '/carousels/shows/%d/offset/0/limit/15/xs/0/' % show['id'])

        #  var loader = new CBS.V2.CarouselLoader({
        #                        'video-preview-carousel': function(element) {
        #                            element.videoCarousel({
        #                                id          : 241426,
        #                                templates   : 'carousels/videoAdaptive',
        #                                scroll      : 3,
        #                                layout      : 3,
        #                                start       : 0,
        #                                saveState   : false
        #                            });
        #                        }
        try:
            clipdata = self._parse_json(
                self._search_regex(r'element\.videoCarousel\(([^)]*)\);', webpage,
                                   'clip carousel'),
                show_name, transform_source=js_to_json)

            # http://www.cbs.com/carousels/videosBySection/241426/offset/0/limit/15/xs/0/
            # => {id: 241426, title: "Clips",
            clips_url = urljoin(url,
                    '/carousels/videosBySection/%d/offset/0/limit/15/xs/0' % clipdata['id'])
            clips = self.carousel_playlist(clips_url, 'clips')
        except RegexNotFoundError:
            clips = { 'entries': [] }

        playlist = self.carousel_playlist(episodes_url, 'episodes')
        playlist['entries'] += clips['entries']
        playlist['id'] = show['id']

	return playlist

class CBSIE(CBSBaseIE):
    _VALID_URL = r'(?:cbs:|https?://(?:www\.)?(?:cbs\.com/shows/[^/]+/video|colbertlateshow\.com/(?:video|podcasts))/)(?P<id>[\w-]+)'

    _TESTS = [{
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'info_dict': {
            'id': '_u7W953k6la293J7EPTd9oHkSPs6Xn6_',
            'ext': 'mp4',
            'title': 'Connect Chat feat. Garth Brooks',
            'description': 'Connect with country music singer Garth Brooks, as he chats with fans on Wednesday November 27, 2013. Be sure to tune in to Garth Brooks: Live from Las Vegas, Friday November 29, at 9/8c on CBS!',
            'duration': 1495,
            'timestamp': 1385585425,
            'upload_date': '20131127',
            'uploader': 'CBSI-NEW',
        },
        'params': {
            # m3u8 download
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

    def _extract_video_info(self, content_id):
        items_data = self._download_xml(
            'http://can.cbs.com/thunder/player/videoPlayerService.php',
            content_id, query={'partner': 'cbs', 'contentId': content_id})
        video_data = xpath_element(items_data, './/item')
        title = xpath_text(video_data, 'videoTitle', 'title', True)
        tp_path = 'dJ5BDC/media/guid/2198311517/%s' % content_id
        tp_release_url = 'http://link.theplatform.com/s/' + tp_path

        asset_types = []
        subtitles = {}
        formats = []
        for item in items_data.findall('.//item'):
            asset_type = xpath_text(item, 'assetType')
            if not asset_type or asset_type in asset_types:
                continue
            asset_types.append(asset_type)
            query = {
                'mbr': 'true',
                'assetTypes': asset_type,
            }
            if asset_type.startswith('HLS') or asset_type in ('OnceURL', 'StreamPack'):
                query['formats'] = 'MPEG4,M3U'
            elif asset_type in ('RTMP', 'WIFI', '3G'):
                query['formats'] = 'MPEG4,FLV'
            tp_formats, tp_subtitles = self._extract_theplatform_smil(
                update_url_query(tp_release_url, query), content_id,
                'Downloading %s SMIL data' % asset_type)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        self._sort_formats(formats)

        info = self._extract_theplatform_metadata(tp_path, content_id)
        info.update({
            'id': content_id,
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

    def _real_extract(self, url):
        content_id = self._match_id(url)
        return self._extract_video_info(content_id)
