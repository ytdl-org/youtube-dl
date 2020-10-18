# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_iso8601, parse_resolution, int_or_none


class OpencastIE(InfoExtractor):
    IE_NAME = 'Opencast'
    _INSTANCES_RE = r'''(?:
                            opencast\.informatik\.kit\.edu|
                            electures\.uni-muenster\.de|
                            oc-presentation\.ltcc\.tuwien\.ac\.at|
                            medien\.ph-noe\.ac\.at|
                            oc-video\.ruhr-uni-bochum\.de|
                            oc-video1\.ruhr-uni-bochum\.de|
                            opencast\.informatik\.uni-goettingen\.de|
                            heicast\.uni-heidelberg\.de|
                            opencast\.hawk\.de:8080|
                            opencast\.hs-osnabrueck\.de|
                            opencast\.uni-koeln\.de|
                            media\.opencast\.hochschule-rhein-waal\.de|
                            matterhorn\.dce\.harvard\.edu|
                            hs-harz\.opencast\.uni-halle\.de|
                            videocampus\.urz\.uni-leipzig\.de|
                            media\.uct\.ac\.za|
                            vid\.igb\.illinois\.edu|
                            cursosabertos\.c3sl\.ufpr\.br|
                            mcmedia\.missioncollege\.org|
                            clases\.odon\.edu\.uy
                        )'''

    _UUID_RE = r'[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'

    _VALID_URL = r'''(?x)
                    https?://(?P<host>%s)/paella/ui/watch.html\?.*?
                    id=(?P<id>%s)
                    ''' % (
        _INSTANCES_RE,
        _UUID_RE,
    )

    _API_BASE = 'https://%s/search/episode.json?id=%s'

    _TEST = {
        'url': 'https://oc-video1.ruhr-uni-bochum.de/paella/ui/watch.html?id=ed063cd5-72c8-46b5-a60a-569243edcea8',
        'md5': '554c8e99a90f7be7e874619fcf2a3bc9',
        'info_dict': {
            'id': 'ed063cd5-72c8-46b5-a60a-569243edcea8',
            'ext': 'mp4',
            'title': '11 - Kryptographie - 24.11.2015',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1606208400,
            'upload_date': '20201124'
        },
    }

    def _call_api(self, host, video_id, path, note=None, errnote=None, fatal=True):
        return self._download_json(self._API_BASE % (host, video_id), video_id, note=note, errnote=errnote, fatal=fatal)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        video_id = mobj.group('id')

        api_json = self._call_api(host, video_id, '', note='Downloading video JSON')

        video = api_json.get('search-results', {}).get('result', {}).get('mediapackage', {})

        # webpage = self._download_webpage(url, video_id)

        title = video.get('title', '')
        series = video.get('seriestitle', '')
        season_id = video.get('series', '')
        creator = video.get('creators', {}).get('creator', '')
        timestamp = parse_iso8601(video.get('start', ''))

        tracks = video.get('media', {}).get('track', [])
        formats = []

        for track in tracks:
            track_obj = {'url': track['url']}

            audio_info = track.get('audio')
            if audio_info is not None:
                if 'bitrate' in audio_info:
                    track_obj.update({'abr': int_or_none(audio_info.get('bitrate'), 1000)})
                if 'samplingrate' in audio_info:
                    track_obj.update({'asr': int_or_none(audio_info.get('samplingrate'))})
                audio_encoder = audio_info.get('encoder', {})
                if 'type' in audio_encoder:
                    track_obj.update({'acodec': audio_encoder.get('type')})

            video_info = track.get('video')
            if video_info is not None:
                if 'resolution' in video_info:
                    track_obj.update({'resolution': video_info.get('resolution')})
                    resolution = parse_resolution(video_info.get('resolution'))
                    track_obj.update(resolution)
                if 'framerate' in video_info:
                    track_obj.update({'fps': int_or_none(video_info.get('framerate'))})
                if 'bitrate' in video_info:
                    track_obj.update({'vbr': int_or_none(video_info.get('bitrate'), 1000)})
                video_encoder = video_info.get('encoder', {})
                if 'type' in video_encoder:
                    track_obj.update({'vcodec': video_encoder.get('type')})

            formats.append(track_obj)

        self._sort_formats(formats)

        result_obj = {
            'id': video_id,
            'title': title,
            'creator': creator,
            'series': series,
            'season_id': season_id,
            'formats': formats,
            'timestamp': timestamp,
        }

        attachments = video.get('attachments', {}).get('attachment', [])
        if len(attachments) > 0:
            thumbnail = attachments[0].get('url')
            result_obj.update({'thumbnail': thumbnail})

        return result_obj
