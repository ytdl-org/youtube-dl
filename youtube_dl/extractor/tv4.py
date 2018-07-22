# coding: utf-8
from __future__ import unicode_literals

from io import StringIO
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class TV4IE(InfoExtractor):
    IE_DESC = 'tv4.se and tv4play.se'
    _VALID_URL = r'''(?x)https?://(?:www\.)?
        (?:
            tv4\.se/(?:[^/]+)/klipp/(?:.*)-|
            tv4play\.se/
            (?:
                (?:program|barn)/(?:[^/]+/|(?:[^\?]+)\?video_id=)|
                iframe/video/|
                film/|
                sport/|
            )
        )(?P<id>[0-9]+)'''
    _GEO_COUNTRIES = ['SE']
    _TESTS = [
        {
            'url': 'http://www.tv4.se/kalla-fakta/klipp/kalla-fakta-5-english-subtitles-2491650',
            'md5': 'cb837212f342d77cec06e6dad190e96d',
            'info_dict': {
                'id': '2491650',
                'ext': 'mp4',
                'title': 'Kalla Fakta 5 (english subtitles)',
                'thumbnail': r're:^https?://.*\.jpg$',
                'timestamp': int,
                'upload_date': '20131125',
            },
        },
        {
            'url': 'http://www.tv4play.se/iframe/video/3054113',
            'md5': 'cb837212f342d77cec06e6dad190e96d',
            'info_dict': {
                'id': '3054113',
                'ext': 'mp4',
                'title': 'Så här jobbar ficktjuvarna - se avslöjande bilder',
                'thumbnail': r're:^https?://.*\.jpg$',
                'description': 'Unika bilder avslöjar hur turisternas fickor vittjas mitt på Stockholms central. Två experter på ficktjuvarna avslöjar knepen du ska se upp för.',
                'timestamp': int,
                'upload_date': '20150130',
            },
        },
        {
            'url': 'http://www.tv4play.se/sport/3060959',
            'only_matching': True,
        },
        {
            'url': 'http://www.tv4play.se/film/2378136',
            'only_matching': True,
        },
        {
            'url': 'http://www.tv4play.se/barn/looney-tunes?video_id=3062412',
            'only_matching': True,
        },
        {
            'url': 'http://www.tv4play.se/program/farang/3922081',
            'only_matching': True,
        }
    ]

    _ENCODING = 'UTF-8'
    _MPEG2_PTS_RATE_HZ = 90000
    """:type Pattern"""
    _REGEX_SUB_ENTRY_TIMELINE = re.compile(
        r'^(\d+):(\d+):(\d+).(\d+)[^0-9]+(\d+):(\d+):(\d+).(\d+)$'
    )
    """:type Pattern"""
    _REGEX_X_TIMESTAMP = re.compile(
        r'^X-TIMESTAMP-MAP=MPEGTS:(\d+),LOCAL:(\d+):(\d+):(\d+).(\d+)$'
    )
    """:type Pattern"""
    _REGEX_WEBVTT = re.compile(r'^(.+-(\d+)\.webvtt.*)$')
    """:type Pattern"""

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._download_json(
            'http://www.tv4play.se/player/assets/%s.json' % video_id,
            video_id, 'Downloading video info JSON')

        title = info['title']

        manifest_url = self._download_json(
            'https://playback-api.b17g.net/media/' + video_id,
            video_id, query={
                'service': 'tv4',
                'device': 'browser',
                'protocol': 'hls',
            })['playbackItem']['manifestUrl']
        all_formats = self._extract_m3u8_formats(
            manifest_url, video_id, 'mp4',
            'm3u8_native', m3u8_id='hls', fatal=False)
        all_formats.extend(self._extract_mpd_formats(
            manifest_url.replace('.m3u8', '.mpd'),
            video_id, mpd_id='dash', fatal=False))
        all_formats.extend(self._extract_f4m_formats(
            manifest_url.replace('.m3u8', '.f4m'),
            video_id, f4m_id='hds', fatal=False))
        all_formats.extend(self._extract_ism_formats(
            re.sub(r'\.ism/.+?\.m3u8', r'.ism/Manifest', manifest_url),
            video_id, ism_id='mss', fatal=False))

        if not all_formats and info.get('is_geo_restricted'):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        subtitle_formats = []
        other_formats = []
        for _index, _format in enumerate(all_formats):
            if re.match(r'^.*textstream.*$', _format['format_id']):
                subtitle_formats.append(_format)
            else:
                other_formats.append(_format)

        self._sort_formats(other_formats)

        subtitles = self._webvtt_download_all_subtitle_data(
            video_id,
            subtitle_formats
        )

        return {
            'id': video_id,
            'title': title,
            'formats': other_formats,
            'subtitles': subtitles,
            'description': info.get('description'),
            'timestamp': parse_iso8601(info.get('broadcast_date_time')),
            'duration': int_or_none(info.get('duration')),
            'thumbnail': info.get('image'),
            'is_live': info.get('is_live') is True,
        }

    @staticmethod
    def _webvtt_adjust_time(reference_sec, ahead_sec, actual_sec):
        """

        :param reference_sec:
        :type reference_sec: float
        :param ahead_sec:
        :type ahead_sec: float
        :param actual_sec:
        :type actual_sec: float
        :return:
        :rtype: float
        """
        return reference_sec - ahead_sec + actual_sec

    def _webvtt_download_all_subtitle_data(self, video_id, subtitle_formats):
        subtitles = {}
        for subtitle_format in subtitle_formats:
            tag = subtitle_format['language']
            subtitle = self._webvtt_download_subtitle_data(
                video_id, subtitle_format
            )
            if subtitle is not None:
                if tag not in subtitles.keys():
                    subtitles[tag] = []
                subtitles[tag].append(subtitle)

        return subtitles

    def _webvtt_download_subtitle_data(self, video_id, subtitle_format):
        subs_m3u8_url = subtitle_format['url']
        urlh = self._request_webpage(subs_m3u8_url, video_id, fatal=False)
        subs_m3u8_body = ''
        if urlh:
            subs_m3u8_data = urlh.read()
            if subs_m3u8_data:
                subs_m3u8_body = subs_m3u8_data.decode(encoding=self._ENCODING)
        subs_body_io = StringIO()
        base_url = re.search(
            r'^(.+)/[^/]+',
            subtitle_format['manifest_url']
        ).group(1)
        first_fragment = True
        for subs_m3u8_line in subs_m3u8_body.split('\n'):
            match = self._REGEX_WEBVTT.match(subs_m3u8_line)
            if match:
                subs_fragment_partial_url = match.group(1)
                subs_fragment_index = match.group(2)
                subs_fragment_url = '/'.join(
                    [base_url, subs_fragment_partial_url]
                )
                urlh = self._request_webpage(
                    subs_fragment_url,
                    '{}-{}'.format(video_id, subs_fragment_index),
                    fatal=False
                )
                if urlh:
                    subs_fragment_data = urlh.read()
                    if subs_fragment_data:
                        self._webvtt_write_fragment(
                            subs_fragment_data, subs_body_io, first_fragment
                        )
                        first_fragment = False
        subtitle = {'ext': 'vtt', 'data': subs_body_io.getvalue()}
        subs_body_io.close()

        return subtitle

    def _webvtt_handle_one_fragment(
            self,
            webvtt_bytes,
            vtt_file,
            first_fragment=False
    ):
        """

        :param webvtt_bytes:
        :type webvtt_bytes: bytes
        :param vtt_file:
        :type vtt_file: TextIO
        :param first_fragment:
        :type first_fragment: bool
        :return:
        :rtype: int
        """
        mpeg_ref_sec: float = None
        local_ref_sec: float = 0.0

        for line_index, line in enumerate(
                StringIO(
                    webvtt_bytes.decode(encoding=self._ENCODING)
                ).readlines()
        ):
            line = line.strip()
            if line_index == 0:
                if line == 'WEBVTT':
                    if first_fragment:
                        print(line, file=vtt_file)
                    continue
                else:
                    break
            elif line_index == 1:
                match = self._REGEX_X_TIMESTAMP.match(line)
                """:type: Match"""
                if match:
                    mpeg_ref_sec = (
                       int(match.group(1)) - (10 * self._MPEG2_PTS_RATE_HZ)
                    ) / self._MPEG2_PTS_RATE_HZ
                    local_ref_sec: float = self._webvtt_time_parts_to_float(
                        int(match.group(2)),
                        int(match.group(3)),
                        int(match.group(4)),
                        int(match.group(5))
                    )
                continue
            else:
                if len(line.strip()) > 0:
                    match = self._REGEX_SUB_ENTRY_TIMELINE.match(line)
                    """:type: Match"""
                    if match:
                        print('', file=vtt_file)
                        print(self._webvtt_make_timeline(
                            self._webvtt_adjust_time(
                                mpeg_ref_sec,
                                local_ref_sec,
                                self._webvtt_time_parts_to_float(
                                    int(match.group(1)),
                                    int(match.group(2)),
                                    int(match.group(3)),
                                    int(match.group(4))
                                )
                            ),
                            self._webvtt_adjust_time(
                                mpeg_ref_sec,
                                local_ref_sec,
                                self._webvtt_time_parts_to_float(
                                    int(match.group(5)),
                                    int(match.group(6)),
                                    int(match.group(7)),
                                    int(match.group(8))
                                )
                            )
                        ), file=vtt_file)
                    else:
                        print('{}'.format(line), file=vtt_file)

    def _webvtt_make_timeline(self, start_sec=0.0, stop_sec=0.0):
        """

        :param start_sec:
        :type start_sec: float
        :param stop_sec:
        :type stop_sec: float
        :return:
        :rtype: str
        """
        return (
            '{:02d}:{:02d}:{:02d}.{:03d} --> {:02d}:{:02d}:{:02d}.{:03d}'
        ).format(
            *self._webvtt_time_float_to_parts(start_sec),
            *self._webvtt_time_float_to_parts(stop_sec)
        )

    @staticmethod
    def _webvtt_time_parts_to_float(
            hours=0, minutes=0, seconds=0, milli_seconds=0
    ):
        """

        :param hours:
        :type hours: int
        :param minutes:
        :type minutes: int
        :param seconds:
        :type seconds: int
        :param milli_seconds:
        :type milli_seconds: int
        :return:
        :rtype: float
        """
        return seconds + 60 * (minutes + 60 * hours) + milli_seconds / 1000

    @staticmethod
    def _webvtt_time_float_to_parts(input_sec=0.0):
        """

        :param input_sec:
        :type input_sec: float
        :return:
        :rtype: Tuple[int, int, int, int]
        """
        minutes, seconds = divmod(input_sec, 60)
        hours, minutes = divmod(minutes, 60)
        milli_seconds: int = int(1000 * (input_sec % 1))

        return int(hours), int(minutes), int(seconds), milli_seconds

    def _webvtt_write_fragment(
            self,
            webvtt_data,
            output_stream,
            first_fragment=False
    ):
        """

        :param webvtt_data:
        :type webvtt_data: bytes
        :param output_stream:
        :type output_stream: TextIO
        :param first_fragment:
        :type first_fragment: bool
        """
        self._webvtt_handle_one_fragment(
            webvtt_data, output_stream, first_fragment
        )

