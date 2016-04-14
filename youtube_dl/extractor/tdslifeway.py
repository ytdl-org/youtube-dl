from __future__ import unicode_literals

from .common import InfoExtractor


class TDSLifewayIE(InfoExtractor):
    _VALID_URL = r'https?://tds\.lifeway\.com/v1/trainingdeliverysystem/courses/(?P<id>\d+)/index\.html'

    _TEST = {
        # From http://www.ministrygrid.com/training-viewer/-/training/t4g-2014-conference/the-gospel-by-numbers-4/the-gospel-by-numbers
        'url': 'http://tds.lifeway.com/v1/trainingdeliverysystem/courses/3453494717001/index.html?externalRegistration=AssetId%7C34F466F1-78F3-4619-B2AB-A8EFFA55E9E9%21InstanceId%7C0%21UserId%7Caaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa&grouping=http%3A%2F%2Flifeway.com%2Fvideo%2F3453494717001&activity_id=http%3A%2F%2Flifeway.com%2Fvideo%2F3453494717001&content_endpoint=http%3A%2F%2Ftds.lifeway.com%2Fv1%2Ftrainingdeliverysystem%2FScormEngineInterface%2FTCAPI%2Fcontent%2F&actor=%7B%22name%22%3A%5B%22Guest%20Guest%22%5D%2C%22account%22%3A%5B%7B%22accountServiceHomePage%22%3A%22http%3A%2F%2Fscorm.lifeway.com%2F%22%2C%22accountName%22%3A%22aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa%22%7D%5D%2C%22objectType%22%3A%22Agent%22%7D&content_token=462a50b2-b6f9-4970-99b1-930882c499fb&registration=93d6ec8e-7f7b-4ed3-bbc8-a857913c0b2a&externalConfiguration=access%7CFREE%21adLength%7C-1%21assignOrgId%7C4AE36F78-299A-425D-91EF-E14A899B725F%21assignOrgParentId%7C%21courseId%7C%21isAnonymous%7Cfalse%21previewAsset%7Cfalse%21previewLength%7C-1%21previewMode%7Cfalse%21royalty%7CFREE%21sessionId%7C671422F9-8E79-48D4-9C2C-4EE6111EA1CD%21trackId%7C&auth=Basic%20OjhmZjk5MDBmLTBlYTMtNDJhYS04YjFlLWE4MWQ3NGNkOGRjYw%3D%3D&endpoint=http%3A%2F%2Ftds.lifeway.com%2Fv1%2Ftrainingdeliverysystem%2FScormEngineInterface%2FTCAPI%2F',
        'info_dict': {
            'id': '3453494717001',
            'ext': 'mp4',
            'title': 'The Gospel by Numbers',
            'thumbnail': 're:^https?://.*\.jpg',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # XXX: A generic brightcove function?
        json_data = self._download_json(
            'http://api.brightcove.com/services/library', video_id,
            query={
                'command': 'find_video_by_id',
                'video_id': video_id,
                'video_fields': 'id,name,videoStillURL,HLSURL,FLVURL',
                'media_delivery': 'http',
                # token extracted from http://tds.lifeway.com/v1/trainingdeliverysystem/courses/player_test.js
                'token': 'MrrNjVSP15NGY3R0gipp-lvclofucPXKD3skFouJMjZXM3KOS2ch0g..',
            })

        formats = []

        if 'HLSURL' in json_data:
            formats.extend(self._extract_m3u8_formats(
                json_data['HLSURL'], video_id, ext='mp4', m3u8_id='hls', fatal=False))
        if 'FLVURL' in json_data:
            formats.append({
                'url': json_data['FLVURL'],
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': json_data['name'],
            'thumbnail': json_data.get('videoStillURL'),
            'formats': formats,
        }
