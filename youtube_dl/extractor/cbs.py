from __future__ import unicode_literals

from .theplatform import ThePlatformFeedIE
from ..utils import (
    int_or_none,
    find_xpath_attr,
    ExtractorError,
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

    def _extract_video_info(self, guid):
        path = 'dJ5BDC/media/guid/2198311517/' + guid
        smil_url = 'http://link.theplatform.com/s/%s?mbr=true' % path
        formats, subtitles = self._extract_theplatform_smil(smil_url + '&manifest=m3u', guid)
        for r in ('OnceURL&formats=M3U', 'HLS&formats=M3U', 'RTMP', 'WIFI', '3G'):
            try:
                tp_formats, _ = self._extract_theplatform_smil(smil_url + '&assetTypes=' + r, guid, 'Downloading %s SMIL data' % r.split('&')[0])
                formats.extend(tp_formats)
            except ExtractorError:
                continue
        self._sort_formats(formats)
        metadata = self._download_theplatform_metadata(path, guid)
        info = self._parse_theplatform_metadata(metadata)
        info.update({
            'id': guid,
            'formats': formats,
            'subtitles': subtitles,
            'series': metadata.get('cbs$SeriesTitle'),
            'season_number': int_or_none(metadata.get('cbs$SeasonNumber')),
            'episode': metadata.get('cbs$EpisodeTitle'),
            'episode_number': int_or_none(metadata.get('cbs$EpisodeNumber')),
        })
        return info

    def _real_extract(self, url):
        content_id = self._match_id(url)
        return self._extract_video_info(content_id)
