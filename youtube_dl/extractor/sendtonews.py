# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    dict_get,
    ExtractorError,
    float_or_none,
    parse_iso8601,
    update_url_query,
    int_or_none,
    determine_ext,
    determine_protocol,
    strip_or_none,
    try_get,
    unescapeHTML,
    urljoin,
)


class SendtoNewsIE(InfoExtractor):
    # TODO handle items with ?fk=XXXX6789&cid=1234 -> SC=XXXX6789-???????-1234
    _VALID_URL = r'https?://embed\.sendtonews\.com/(?:player\d/embed(?:player|code)\.(?:php|js)|oembed/?)\?.*\bSC=(?P<id>[\w-]+)'
    _TESTS = [{
        # From http://cleveland.cbslocal.com/2016/05/16/indians-score-season-high-15-runs-in-blowout-win-over-reds-rapid-reaction/
        'url': 'http://embed.sendtonews.com/player2/embedplayer.php?SC=GxfCe0Zo7D-175909-5588&type=single&autoplay=on&sound=YES',
        'info_dict': {
            'id': 'GxfCe0Zo7D-175909-5588'
        },
        'playlist_count': 10,
    }, {
        'url': 'https://embed.sendtonews.com/player4/embedplayer.php?SC=mq3wIKSb68-1206898-8402&type=single',
        'info_dict': {
            'id': '1752278',
            'ext': 'mp4',
            'title': 'Las vegas homebuilders had banner sales year in 2021, and other top stories from January 24, 2022.',
            'description': 'LAS VEGAS HOMEBUILDERS HAD BANNER SALES YEAR IN 2021., and other top stories from January 24, 2022.',
            'timestamp': 1643063702,
            'upload_date': '20220124',
            'thumbnail': r're:https?://.*\.(?:png|jpg)$',
            'categories': ['Business'],
            'tags': list,
        },
    }]

    _URL_TEMPLATE = '//embed.sendtonews.com/player2/embedplayer.php?SC=%s'

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(r'''(?x)<script[^>]+src=([\'"])
            (?:https?:)?//embed\.sendtonews\.com/player/responsiveembed\.php\?
                .*\bSC=(?P<SC>[0-9a-zA-Z-]+).*
            \1>''', webpage)
        if mobj:
            sc = mobj.group('SC')
            return cls._URL_TEMPLATE % sc

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        data_url = update_url_query(
            re.sub(
                r'(?P<player>player\d)?(?<!/)/(?P<embed>embed.+?|oembed/)\?',
                lambda m: '/%s/data_read.php?' % ((m.group('player') or 'player4'), ),
                url),
            {'cmd': 'loadInitial', 'type': 'single', })
        playlist_data = self._download_json(data_url, playlist_id)
        playlist = try_get(playlist_data, lambda x: x['playlistData'][0], (dict, list)) or {}
        if isinstance(playlist, dict):
            err = playlist.get('error', 'No or invalid data returned from API')
            raise ExtractorError(err)

        entries = []
        info_dict = {}
        for video in playlist:
            try:
                err = video.get('error')
                if err and video.get('S_ID') is not None:
                    e = ExtractorError(err)
                    e.msg = err
                    raise e
            except AttributeError:
                continue
            except ExtractorError as e:
                self.report_warning(e.msg, playlist_id)
                continue
            if 'jwconfiguration' in video:
                info_dict.update(self._parse_jwplayer_data(
                    video['jwconfiguration'],
                    require_title=False, m3u8_id='hls', rtmp_params={'no_resume': True}))
            elif 'configuration' not in video:
                continue
            else:
                fmt_url = urljoin(
                    url,
                    try_get(video, lambda x: x['configuration']['sources']['src']))
                if not fmt_url:
                    continue
                video_id = strip_or_none(video.get('SM_ID') or video['configuration']['mediaid'])
                title = strip_or_none(video.get('S_headLine') or video['configuration']['title'])
                if not video_id or not title:
                    continue
                ext = determine_ext(fmt_url)
                if ext == 'm3u8':
                    formats = self._extract_m3u8_formats(
                        fmt_url, playlist_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False)
                else:
                    formats = [{
                        'url': fmt_url,
                        'ext': ext,
                        'width': int_or_none(video.get('SM_M_VIDEO_WIDTH')),
                        'height': int_or_none(video.get('SM_M_VIDEO_HEIGHT')),
                    }]
                info_dict['formats'] = formats

            for f in info_dict.get('formats') or []:
                if f.get('tbr'):
                    continue
                tbr = int_or_none(self._search_regex(
                    r'/(\d+)k/', f['url'], 'bitrate', default=None))
                if not tbr:
                    continue
                f.update({
                    'format_id': '%s-%d' % (determine_protocol(f), tbr),
                    'tbr': tbr,
                })
            self._sort_formats(info_dict['formats'], ('tbr', 'height', 'width', 'format_id'))

            thumbnails = []
            for tn_id, tn in (('poster', video['configuration'].get('poster')),
                              ('normal', video.get('thumbnailUrl')),
                              ('small', video.get('smThumbnailUrl'))):
                tn = urljoin(url, tn)
                if not tn:
                    continue
                thumbnails.append({
                    'id': tn_id,
                    'url': tn,
                })
            info_dict.update({
                'id': video_id,
                'title': title,
                'description': unescapeHTML(dict_get(video, ('S_fullStory', 'S_shortSummary'))),
                'thumbnails': thumbnails,
                'duration': float_or_none(
                    dict_get(video, ('SM_length', 'SM_M_LENGTH'))
                    or video['configuration'].get('duration')),
                'timestamp': parse_iso8601(video.get('S_sysDate'), delimiter=' '),
                'tags': [t for t in video.get('S_tags', '').split(',') if t],
                'categories': [c for c in video.get('S_category', '').split(',') if c],
            })
            entries.append(info_dict)

        if len(entries) == 1:
            entries[0]['display_id'] = playlist_id
            return entries[0]
        return self.playlist_result(entries, playlist_id)
