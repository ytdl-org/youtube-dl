# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    merge_dicts,
    parse_filesize,
    parse_resolution,
    strip_or_none,
    T,
    traverse_obj,
    txt_or_none,
    url_basename,
    url_or_none,
    urlencode_postdata,
    urljoin,
)

from functools import partial
k_int_or_none = partial(int_or_none, scale=1000)


class ZoomIE(InfoExtractor):
    IE_NAME = 'zoom'
    _VALID_URL = r'(?P<base_url>https?://(?:[^.]+\.)?zoom\.us/)rec(?:ording)?/(?P<type>play|share)/(?P<id>[\w.-]+)'
    _TESTS = [{
        'url': 'https://economist.zoom.us/rec/play/dUk_CNBETmZ5VA2BwEl-jjakPpJ3M1pcfVYAPRsoIbEByGsLjUZtaa4yCATQuOL3der8BlTwxQePl_j0.EImBkXzTIaPvdZO5',
        'md5': 'ab445e8c911fddc4f9adc842c2c5d434',
        'info_dict': {
            'id': 'dUk_CNBETmZ5VA2BwEl-jjakPpJ3M1pcfVYAPRsoIbEByGsLjUZtaa4yCATQuOL3der8BlTwxQePl_j0.EImBkXzTIaPvdZO5',
            'ext': 'mp4',
            'title': 'China\'s "two sessions" and the new five-year plan',
        },
        'skip': 'Recording requires email authentication to access',
    }, {
        'url': 'https://us06web.zoom.us/rec/play/W1ctyErikzJ2CxtwlsTW3xNbiMHze6ZkU1adqeshzivi58DHEJ-7HX2Z8-nqK80a8d4CWHAhrSpsl9mG.OaL6JvfC1gAa1EvZ?canPlayFromShare=true&from=share_recording_detail&continueMode=true&componentName=rec-play&originRequestUrl=https%3A%2F%2Fus06web.zoom.us%2Frec%2Fshare%2F60THDorqjAyUm_IXKS88Z4KgfYRAER3wIG20jgrLqaSFBWJW14qBVBRkfHylpFrk.KXJxuNLN0sRBXyvf',
        'md5': 'b180e7773a878e4799f194f2280648d5',
        'info_dict': {
            'id': 'W1ctyErikzJ2CxtwlsTW3xNbiMHze6ZkU1adqeshzivi58DHEJ-7HX2Z8-nqK80a8d4CWHAhrSpsl9mG.OaL6JvfC1gAa1EvZ',
            'ext': 'mp4',
            'title': 'Chipathon Bi-Weekly Meeting',
            'description': 'Shared screen with speaker view',
            'timestamp': 1715263581,
            'upload_date': '20240509',
        }
    }, {
        # play URL
        'url': 'https://ffgolf.zoom.us/rec/play/qhEhXbrxq1Zoucx8CMtHzq1Z_2YZRPVCqWK_K-2FkEGRsSLDeOX8Tu4P6jtjZcRry8QhIbvKZdtr4UNo.QcPn2debFskI9whJ',
        'md5': '2c4b1c4e5213ebf9db293e88d9385bee',
        'info_dict': {
            'id': 'qhEhXbrxq1Zoucx8CMtHzq1Z_2YZRPVCqWK_K-2FkEGRsSLDeOX8Tu4P6jtjZcRry8QhIbvKZdtr4UNo.QcPn2debFskI9whJ',
            'ext': 'mp4',
            'title': 'Prépa AF2023 - Séance 5 du 11 avril - R20/VM/GO',
        },
        'skip': 'Recording expired',
    }, {
        # share URL
        'url': 'https://us02web.zoom.us/rec/share/hkUk5Zxcga0nkyNGhVCRfzkA2gX_mzgS3LpTxEEWJz9Y_QpIQ4mZFOUx7KZRZDQA.9LGQBdqmDAYgiZ_8',
        'md5': '90fdc7cfcaee5d52d1c817fc03c43c9b',
        'info_dict': {
            'id': 'hkUk5Zxcga0nkyNGhVCRfzkA2gX_mzgS3LpTxEEWJz9Y_QpIQ4mZFOUx7KZRZDQA.9LGQBdqmDAYgiZ_8',
            'ext': 'mp4',
            'title': 'Timea Andrea Lelik\'s Personal Meeting Room',
        },
        'skip': 'This recording has expired',
    }, {
        # view_with_share URL
        'url': 'https://cityofdetroit.zoom.us/rec/share/VjE-5kW3xmgbEYqR5KzRgZ1OFZvtMtiXk5HyRJo5kK4m5PYE6RF4rF_oiiO_9qaM.UTAg1MI7JSnF3ZjX',
        'md5': 'bdc7867a5934c151957fb81321b3c024',
        'info_dict': {
            'id': 'VjE-5kW3xmgbEYqR5KzRgZ1OFZvtMtiXk5HyRJo5kK4m5PYE6RF4rF_oiiO_9qaM.UTAg1MI7JSnF3ZjX',
            'ext': 'mp4',
            'title': 'February 2022 Detroit Revenue Estimating Conference',
            'description': 'Speaker view',
            'timestamp': 1645200510,
            'upload_date': '20220218',
            'duration': 7299,
            'formats': 'mincount:3',
        },
    }, {
        # ytdl-org/youtube-dl#32094
        'url': 'https://us02web.zoom.us/rec/share/9pdVT4f2XWBaEOSqDJagSsvI0Yu2ixXW0YcJGIVhfV19Zr7E1q5gf0wTMZHnqrvq.Yoq1dDHeeKjaVcv3',
        'md5': 'fdb6f8df7f5ee0c07ced5fae55c0ced4',
        'info_dict': {
            'id': '9pdVT4f2XWBaEOSqDJagSsvI0Yu2ixXW0YcJGIVhfV19Zr7E1q5gf0wTMZHnqrvq.Yoq1dDHeeKjaVcv3',
            'ext': 'mp4',
            'title': 'Untersuchungskurs Gruppe V',
            'description': 'Shared screen with speaker view',
            'timestamp': 1681889972,
            'upload_date': '20230419',
        },
    }]

    def _get_page_data(self, webpage, video_id):
        return self._search_json(
            r'window\.__data__\s*=', webpage, 'data', video_id, transform_source=js_to_json)

    def _get_real_webpage(self, url, base_url, video_id, url_type):
        webpage = self._download_webpage(url, video_id, note='Downloading {0} webpage'.format(url_type))
        try:
            form = self._form_hidden_inputs('password_form', webpage)
        except ExtractorError:
            return webpage

        password = self.get_param('videopassword')
        if not password:
            raise ExtractorError(
                'This video is protected by a passcode: use the --video-password option', expected=True)
        is_meeting = form.get('useWhichPasswd') == 'meeting'
        validation = self._download_json(
            base_url + 'rec/validate%s_passwd' % ('_meet' if is_meeting else ''),
            video_id, 'Validating passcode', 'Wrong passcode', data=urlencode_postdata({
                'id': form[('meet' if is_meeting else 'file') + 'Id'],
                'passwd': password,
                'action': form.get('action'),
            }))
        if not validation.get('status'):
            raise ExtractorError(validation['errorMessage'], expected=True)
        return self._download_webpage(url, video_id, note='Re-downloading {0} webpage'.format(url_type))

    def _real_extract(self, url):
        base_url, url_type, video_id = self._match_valid_url(url).group('base_url', 'type', 'id')
        query = {}

        if url_type == 'share':
            webpage = self._get_real_webpage(url, base_url, video_id, 'share')
            meeting_id = self._get_page_data(webpage, video_id)['meetingId']
            share_info = self._download_json(
                '{0}nws/recording/1.0/play/share-info/{1}'.format(base_url, meeting_id),
                video_id, note='Downloading share info JSON', fatal=False)
            url = traverse_obj(share_info, (
                'result', 'redirectUrl', T(lambda u: urljoin(base_url, u))))
            if not url:
                raise ExtractorError(traverse_obj(
                    share_info, 'errorMessage') or 'No video found from share link')
            query['continueMode'] = 'true'

        webpage = self._get_real_webpage(url, base_url, video_id, 'play')
        file_id = traverse_obj(webpage, T(lambda x: txt_or_none(self._get_page_data(x, video_id)['fileId'])))
        if not file_id:
            # When things go wrong, file_id can be empty string
            raise ExtractorError('Unable to extract file ID')

        data = self._download_json(
            '{0}nws/recording/1.0/play/info/{1}'.format(base_url, file_id), video_id, query=query,
            note='Downloading play info JSON')['result']

        formats = []
        subtitles = dict(
            (s_type, [{'url': s_url, 'ext': 'vtt', }])
            for s_type, s_url in traverse_obj(
                ('transcript', 'cc', 'chapter'),
                (Ellipsis,
                 T(lambda t: (t, urljoin(base_url, txt_or_none(data['%sUrl' % (t,)])))),
                 T(lambda x: x if x[1] else None)))) or None

        def if_url(f):
            return lambda x: f(x) if x.get('url') else None

        formats.extend(traverse_obj(data, ((
            ({
                'url': ('viewMp4Url', T(url_or_none)),
                'width': ('viewResolvtions', 0, T(int_or_none)),
                'height': ('viewResolvtions', 1, T(int_or_none)),
                'format_id': ('recording', 'id', T(txt_or_none)),
                'filesize_approx': ('recording', 'fileSizeInMB', T(parse_filesize)),
            }, T(if_url(lambda x: merge_dicts({
                'format_note': 'Camera stream',
                'ext': 'mp4',
                'preference': 0,
            }, x)))),
            ({
                'url': ('shareMp4Url', T(url_or_none)),
                'width': ('shareResolvtions', 0, T(int_or_none)),
                'height': ('shareResolvtions', 1, T(int_or_none)),
                'format_id': ('shareVideo', 'id', T(txt_or_none)),
                'filesize_approx': ('recording', 'fileSizeInMB', T(parse_filesize)),
            }, T(if_url(lambda x: merge_dicts({
                'format_note': 'Screen share stream',
                'ext': 'mp4',
                'preference': -1,
            }, x)))),
            ({
                'url': ('viewMp4WithshareUrl', T(url_or_none)),
            }, T(if_url(lambda x: merge_dicts({
                'format_note': 'Screen share with camera',
                'format_id': 'view_with_share',
                'ext': 'mp4',
                'preference': 1,
            }, parse_resolution(self._search_regex(
                r'_(\d+x\d+)\.mp4', url_basename(x['url']),
                'resolution', default=None)), x)
            )))), all)
        ))

        if not formats and data.get('message'):
            raise ExtractorError('No media found; %s said "%s"' % (self.IE_NAME, data['message'],), expected=True)
        self._sort_formats(formats)

        return merge_dicts(traverse_obj(data, {
            'title': ('meet', 'topic', T(strip_or_none)),
            'description': ('recording', 'displayFileName', T(strip_or_none)),
            'duration': ('duration', T(int_or_none)),
            'timestamp': (('clipStartTime', 'fileStartTime'), T(k_int_or_none), any),
        }), {
            'id': video_id,
            'subtitles': subtitles,
            'formats': formats,
            'http_headers': {
                'Referer': base_url,
            },
        })
