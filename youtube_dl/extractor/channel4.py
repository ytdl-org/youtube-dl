from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urlparse,
)
from ..utils import (
    unified_strdate,
    ExtractorError
)

class Channel4IE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?channel4\.com/programmes/(?P<pid>.*?)/on-demand/(?P<id>.*)'

    _TESTS = [{
        'url': 'http://www.channel4.com/programmes/black-mirror/on-demand/49114-002',
        'info_dict': {
            'id': '49114-002',
            '_programme_title': "Black Mirror",
            'title': "15 Million Merits",
            'description': "In the near future, everyone is confined to a life of strange physical drudgery. The only way to escape is to enter the 'Hot Shot' talent show and pray you can impress the judges.",
            'duration': 222780,
        },
        'params': {
            # unimplemented DRM
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_data = json.loads(self._search_regex(
            r'onDemand.selectedEpisode = (?P<json>{.+?});\n',
            webpage, 'video data json'))

        thumbnails = [{
            'url': video_data["pictureComponent"]["url"]
        }]

        request_id = video_data["requestId"]
        # XXX: the Flash player also puts the Unix timestamp in the query string. the download works without it just fine, though
        asset_url = 'http://ais.channel4.com/asset/%s' % (request_id)
        stream_info = self._download_xml(asset_url, video_id)

        service_report = stream_info.find('./serviceReport')
        if service_report.attrib.get('returnCode') != "200":
            raise ExtractorError(service_report.findtext('./description'), expected=True)

        subtitles = stream_info.findtext('./assetInfo/subtitlesFileUri')
        if subtitles:
            subtitles = {
                'en': [{
                    'ext': 'sami',
                    'url': compat_urlparse.urljoin(asset_url, subtitles),
                }]
            }

        formats = self._extract_f4m_formats(stream_info.findtext('./assetInfo/uriData/streamUri'), video_id)

        return {
            'id': video_id,
            '_programme_title': stream_info.findtext('./assetInfo/brandTitle'),
            'title': stream_info.findtext('./assetInfo/episodeTitle'),
            'upload_date': unified_strdate(video_data['txDate'] + ' ' + video_data.get('txTime', '')),
            'description': video_data.get('synopsis'),
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
            'duration': video_data["assetDuration"] * 60,
            '_drm_token': stream_info.findtext('./assetInfo/uriData/token'),
            '_programme_series': video_data.get("seriesNumber"),
            '_programme_episode': video_data.get("episodeNumber"),
        }
