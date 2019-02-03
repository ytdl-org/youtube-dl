# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    determine_ext,
    strip_jsonp,
    try_get,
)


class WillowTvReplayIE(InfoExtractor):
    IE_NAME = 'willowtv:replay'
    _VALID_URL = r'https?://(?:www\.)?willow\.tv/watch-live/(?P<id>.*)(?:/.*)'
    _TESTS = [{
        'url': 'https://www.willow.tv/watch-live/iu-vs-kk-streaming-online-eliminator-1-pakistan-super-league-2019/replay',
        'info_dict': {
            'id': 'iu-vs-kk-streaming-online-eliminator-1-pakistan-super-league-2019',
            'ext': 'mp4',
        },
        'skip': 'There are no free examples. An account and cookies are required',
    }]

    def _real_extract(self, url):
        meta_format = 'https://willowfeedsv2.willow.tv/willowds/mspecific/%s.json'
        replay_format = 'https://www.willow.tv/match_replay_data_by_id?matchid=%s'

        slug = self._match_id(url)

        meta = self._download_json(
            meta_format % slug,
            slug,
            transform_source=strip_jsonp)

        results = try_get(meta, lambda x: x['result'], list) or []
        if not results:
            raise ExtractorError(
                'No results present for this match. Is it finished yet?',
                expected=True)

        entries = []
        for result in results:
            matchid = result['Id']

            name = try_get(result, lambda x: x['Name'], compat_str)
            series = try_get(result, lambda x: x['SeriesName'], compat_str)
            match_type = try_get(result, lambda x: x['Type'], compat_str)

            data = self._download_json(
                replay_format % matchid,
                matchid,
                transform_source=strip_jsonp)

            status = try_get(data, lambda x: x['status'], compat_str)
            if status != 'success':
                raise ExtractorError(
                    'You must pass the cookies for a logged in willow.tv '
                    'session with --cookies to download replays.',
                    expected=True)

            replays = try_get(data, lambda x: x['result']['replay'], list) \
                or []
            if not replays:
                raise ExtractorError(
                    'No replays present for this match. '
                    'They may not have been uploaded yet.',
                    expected=True)

            vid_format = try_get(data, lambda x: x['result']['vidFormat'],
                                 compat_str)
            if vid_format != 'HLS':
                raise ExtractorError(
                    'Unsupported video format "%s".' % vid_format,
                    expected=True)

            for outer in replays:
                for inner in outer:
                    part = inner['priority']
                    part_id = compat_str(part)
                    url = inner['secureurl']

                    formats = self._extract_m3u8_formats(
                        url, part_id, 'mp4',
                        entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=True)
                    self._sort_formats(formats)

                    title = try_get(inner, lambda x: x['title'], compat_str) \
                        or name or slug

                    entries.append({
                        'id': part_id,
                        'title': title,
                        'series': series,
                        'episode_name': name,
                        'episode_id': matchid,
                        'chapter_number': part,
                        'chapter_id': part_id,
                        'match_type': match_type,
                        'formats': formats,
                    })

        return self.playlist_result(entries, slug)
