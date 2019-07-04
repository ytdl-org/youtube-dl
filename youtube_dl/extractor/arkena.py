# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    int_or_none,
    mimetype2ext,
    parse_iso8601,
    strip_jsonp,
)


class ArkenaIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:
                                video\.arkena\.com/play2/embed/player\?|
                                play\.arkena\.com/(?:config|embed)/avp/v\d/player/media/(?P<id>[^/]+)/[^/]+/(?P<account_id>\d+)
                            )
                        '''
    _TESTS = [{
        'url': 'https://play.arkena.com/embed/avp/v2/player/media/b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe/1/129411',
        'md5': 'b96f2f71b359a8ecd05ce4e1daa72365',
        'info_dict': {
            'id': 'b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'description': 'Royalty free test video',
            'timestamp': 1432816365,
            'upload_date': '20150528',
            'is_live': False,
        },
    }, {
        'url': 'https://play.arkena.com/config/avp/v2/player/media/b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe/1/129411/?callbackMethod=jQuery1111023664739129262213_1469227693893',
        'only_matching': True,
    }, {
        'url': 'http://play.arkena.com/config/avp/v1/player/media/327336/darkmatter/131064/?callbackMethod=jQuery1111002221189684892677_1469227595972',
        'only_matching': True,
    }, {
        'url': 'http://play.arkena.com/embed/avp/v1/player/media/327336/darkmatter/131064/',
        'only_matching': True,
    }, {
        'url': 'http://video.arkena.com/play2/embed/player?accountId=472718&mediaId=35763b3b-00090078-bf604299&pageStyling=styled',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        # See https://support.arkena.com/display/PLAY/Ways+to+embed+your+video
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//play\.arkena\.com/embed/avp/.+?)\1',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        account_id = mobj.group('account_id')

        # Handle http://video.arkena.com/play2/embed/player URL
        if not video_id:
            qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            video_id = qs.get('mediaId', [None])[0]
            account_id = qs.get('accountId', [None])[0]
            if not video_id or not account_id:
                raise ExtractorError('Invalid URL', expected=True)

        playlist = self._download_json(
            'https://play.arkena.com/config/avp/v2/player/media/%s/0/%s/?callbackMethod=_'
            % (video_id, account_id),
            video_id, transform_source=strip_jsonp)['Playlist'][0]

        media_info = playlist['MediaInfo']
        title = media_info['Title']
        media_files = playlist['MediaFiles']

        is_live = False
        formats = []
        for kind_case, kind_formats in media_files.items():
            kind = kind_case.lower()
            for f in kind_formats:
                f_url = f.get('Url')
                if not f_url:
                    continue
                is_live = f.get('Live') == 'true'
                exts = (mimetype2ext(f.get('Type')), determine_ext(f_url, None))
                if kind == 'm3u8' or 'm3u8' in exts:
                    formats.extend(self._extract_m3u8_formats(
                        f_url, video_id, 'mp4', 'm3u8_native',
                        m3u8_id=kind, fatal=False, live=is_live))
                elif kind == 'flash' or 'f4m' in exts:
                    formats.extend(self._extract_f4m_formats(
                        f_url, video_id, f4m_id=kind, fatal=False))
                elif kind == 'dash' or 'mpd' in exts:
                    formats.extend(self._extract_mpd_formats(
                        f_url, video_id, mpd_id=kind, fatal=False))
                elif kind == 'silverlight':
                    # TODO: process when ism is supported (see
                    # https://github.com/ytdl-org/youtube-dl/issues/8118)
                    continue
                else:
                    tbr = float_or_none(f.get('Bitrate'), 1000)
                    formats.append({
                        'url': f_url,
                        'format_id': '%s-%d' % (kind, tbr) if tbr else kind,
                        'tbr': tbr,
                    })
        self._sort_formats(formats)

        description = media_info.get('Description')
        video_id = media_info.get('VideoId') or video_id
        timestamp = parse_iso8601(media_info.get('PublishDate'))
        thumbnails = [{
            'url': thumbnail['Url'],
            'width': int_or_none(thumbnail.get('Size')),
        } for thumbnail in (media_info.get('Poster') or []) if thumbnail.get('Url')]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'is_live': is_live,
            'thumbnails': thumbnails,
            'formats': formats,
        }
