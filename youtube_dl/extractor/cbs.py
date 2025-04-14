# coding: utf-8
from __future__ import unicode_literals

from .theplatform import ThePlatformFeedIE
from ..utils import (
    ExtractorError,
    int_or_none,
    find_xpath_attr,
    xpath_element,
    xpath_text,
    update_url_query,
    url_or_none,
)


class CBSBaseIE(ThePlatformFeedIE):
    def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        subtitles = {}
        for k, ext in [('sMPTE-TTCCURL', 'tt'), ('ClosedCaptionURL', 'ttml'), ('webVTTCaptionURL', 'vtt')]:
            cc_e = find_xpath_attr(smil, self._xpath_ns('.//param', namespace), 'name', k)
            if cc_e is not None:
                cc_url = cc_e.get('value')
                if cc_url:
                    subtitles.setdefault(subtitles_lang, []).append({
                        'ext': ext,
                        'url': cc_url,
                    })
        return subtitles

    def _extract_common_video_info(self, content_id, asset_types, mpx_acc, extra_info):
        tp_path = 'dJ5BDC/media/guid/%d/%s' % (mpx_acc, content_id)
        tp_release_url = 'http://link.theplatform.com/s/' + tp_path
        info = self._extract_theplatform_metadata(tp_path, content_id)

        formats, subtitles = [], {}
        last_e = None
        for asset_type, query in asset_types.items():
            try:
                tp_formats, tp_subtitles = self._extract_theplatform_smil(
                    update_url_query(tp_release_url, query), content_id,
                    'Downloading %s SMIL data' % asset_type)
            except ExtractorError as e:
                last_e = e
                if asset_type != 'fallback':
                    continue
                query['formats'] = ''  # blank query to check if expired
            try:
                tp_formats, tp_subtitles = self._extract_theplatform_smil(
                    update_url_query(tp_release_url, query), content_id,
                    'Downloading %s SMIL data, trying again with another format' % asset_type)
            except ExtractorError as e:
                last_e = e
                continue
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        if last_e and not formats:
            raise last_e
        self._sort_formats(formats)

        extra_info.update({
            'id': content_id,
            'formats': formats,
            'subtitles': subtitles,
        })
        info.update({k: v for k, v in extra_info.items() if v is not None})
        return info

    def _extract_video_info(self, *args, **kwargs):
        # Extract assets + metadata and call _extract_common_video_info
        raise NotImplementedError('This method must be implemented by subclasses')

    def _real_extract(self, url):
        return self._extract_video_info(self._match_id(url))


class CBSIE(CBSBaseIE):
    _VALID_URL = r'''(?x)
        (?:
            cbs:|
            https?://(?:www\.)?(?:
                cbs\.com/(?:shows|movies)/(?:video|[^/]+/video|[^/]+)/|
                colbertlateshow\.com/(?:video|podcasts)/)
        )(?P<id>[\w-]+)'''

    # All tests are blocked outside US
    _TESTS = [{
        'url': 'https://www.cbs.com/shows/video/xrUyNLtl9wd8D_RWWAg9NU2F_V6QpB3R/',
        'info_dict': {
            'id': 'xrUyNLtl9wd8D_RWWAg9NU2F_V6QpB3R',
            'ext': 'mp4',
            'title': 'Tough As Nails - Dreams Never Die',
            'description': 'md5:a3535a62531cdd52b0364248a2c1ae33',
            'duration': 2588,
            'timestamp': 1639015200,
            'upload_date': '20211209',
            'uploader': 'CBSI-NEW',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        '_skip': 'Blocked outside the US',
    }, {
        'url': 'https://www.cbs.com/shows/video/sZH1MGgomIosZgxGJ1l263MFq16oMtW1/',
        'info_dict': {
            'id': 'sZH1MGgomIosZgxGJ1l263MFq16oMtW1',
            'title': 'The Late Show - 3/16/22 (Michael Buble, Rose Matafeo)',
            'timestamp': 1647488100,
            'description': 'md5:d0e6ec23c544b7fa8e39a8e6844d2439',
            'uploader': 'CBSI-NEW',
            'upload_date': '20220317',
        },
        'params': {
            'ignore_no_formats_error': True,
            'skip_download': True,
        },
        'expected_warnings': [
            'This content expired on', 'No video formats found', 'Requested format is not available'],
    }, {
        'url': 'http://colbertlateshow.com/video/8GmB0oY0McANFvp2aEffk9jZZZ2YyXxy/the-colbeard/',
        'only_matching': True,
    }, {
        'url': 'http://www.colbertlateshow.com/podcasts/dYSwjqPs_X1tvbV_P2FcPWRa_qT6akTC/in-the-bad-room-with-stephen/',
        'only_matching': True,
    }, {
        # old format
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'only_matching': True,
    }]

    def _extract_video_info(self, content_id, site='cbs', mpx_acc=2198311517):
        items_data = self._download_xml(
            'https://can.cbs.com/thunder/player/videoPlayerService.php',
            content_id, query={'partner': site, 'contentId': content_id})
        video_data = xpath_element(items_data, './/item')
        title = xpath_text(video_data, 'videoTitle', 'title') or xpath_text(video_data, 'videotitle', 'title')

        asset_types = {}
        has_drm = False
        for item in items_data.findall('.//item'):
            asset_type = xpath_text(item, 'assetType')
            query = {
                'mbr': 'true',
                'assetTypes': asset_type,
            }
            if not asset_type:
                # fallback for content_ids that videoPlayerService doesn't return anything for
                asset_type = 'fallback'
                query['formats'] = 'M3U+none,MPEG4,M3U+appleHlsEncryption,MP3'
                del query['assetTypes']
            if asset_type in asset_types:
                continue
            elif any(excluded in asset_type for excluded in ('HLS_FPS', 'DASH_CENC', 'OnceURL')):
                if 'DASH_CENC' in asset_type:
                    has_drm = True
                continue
            if asset_type.startswith('HLS') or 'StreamPack' in asset_type:
                query['formats'] = 'MPEG4,M3U'
            elif asset_type in ('RTMP', 'WIFI', '3G'):
                query['formats'] = 'MPEG4,FLV'
            asset_types[asset_type] = query

        if not asset_types and has_drm:
            raise ExtractorError('Only DRM formats found', video_id=content_id, expected=True)

        return self._extract_common_video_info(content_id, asset_types, mpx_acc, extra_info={
            'title': title,
            'series': xpath_text(video_data, 'seriesTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
            'duration': int_or_none(xpath_text(video_data, 'videoLength'), 1000),
            'thumbnail': url_or_none(xpath_text(video_data, 'previewImageURL')),
        })
