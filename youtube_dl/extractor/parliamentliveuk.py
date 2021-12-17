from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import compat_str

from ..utils import (
    get_element_by_id,
    int_or_none,
    parse_iso8601,
    try_get,
)


class ParliamentLiveUKIE(InfoExtractor):
    IE_NAME = 'parliamentlive.tv'
    IE_DESC = 'UK parliament videos'
    _VALID_URL = r'(?i)https?://(?:www\.)?parliamentlive\.tv/Event/Index/(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'

    _TESTS = [{
        'url': 'http://parliamentlive.tv/Event/Index/c1e9d44d-fd6c-4263-b50f-97ed26cc998b',
        'info_dict': {
            'id': 'c1e9d44d-fd6c-4263-b50f-97ed26cc998b',
            'ext': 'mp4',
            'title': 'Home Affairs Committee',
            'timestamp': 1622916432,
            'upload_date': '20210605',
            'description': 'Tue, 18 Mar 2014 14:44:32 GMT',
        },
        'params': {
            'format': 'bestvideo/best',
        },
    }, {
        'url': 'http://parliamentlive.tv/event/index/3f24936f-130f-40bf-9a5d-b3d6479da6a4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'https://exposure.api.redbee.live/v2/customer/UKParliament/businessunit/ParliamentLive/entitlement/%s/play?' % video_id,
            video_id, fatal=False,
            headers={'Authorization': 'Bearer 5qIxfu04iGfVXniravNWzlcxk|5qIxfu04iGfVXniravNWzlcxk|5qIxfu04iGfVXniravNWzlcxk|null|1639618587134|1642210587134|true|82293e3a-a0ea-fac9-385d-bfad5829b9c1|WEB||||YipgM4RjyCVP0UqxE29scVZio+L5yUzzCF0Xtp6ToMM=', })
        if video_data:
            webpage = self._download_webpage(url, video_id)
            pub_id = try_get(video_data, 'publicationId', compat_str) or ('%s_0D62A9b' % video_id)
            video_metadata = self._download_json(
                'https://exposure.api.redbee.live/v1/customer/UKParliament/businessunit/ParliamentLive/content/asset/%s?fieldSet=ALL' % pub_id,
                video_id, fatal=False, note='Downloading additional JSON metadata') or {}
            title = (try_get(video_metadata, lambda x: x['localized'][0]['title'], compat_str)
                     or self._html_search_regex(r'<title\b[^>]*>([^<]+)</', webpage, 'title'))
            fmts = []
            for f in try_get(video_data, lambda x: x['formats'], list):
                fmt_url = try_get(f, lambda x: x['mediaLocator'], compat_str)
                if not fmt_url:
                    continue
                if '.ism/Manifest' in fmt_url:
                    fmts.extend(self._extract_ism_formats(
                        fmt_url, video_id, ism_id='mss', fatal=False))
                elif '.m3u8' in fmt_url:
                    fmts.extend(self._extract_m3u8_formats(
                        fmt_url, video_id, 'mp4', fatal=False))
                elif '.mpd' in fmt_url:
                    fmts.extend(self._extract_mpd_formats(
                        fmt_url, video_id, mpd_id='dash', fatal=False))
                else:
                    fmts.append({
                        'format_id': f.get('format'),
                        'url': fmt_url,
                    })
            self._sort_formats(fmts)
            thumbnail = try_get(
                self._download_json(
                    'http://parliamentlive.tv/Event/GetShareVideo/' + video_id, video_id, fatal=False,
                    note='Downloading event JSON metadata'),
                lambda x: x['thumbnailUrl'], compat_str)
            return {
                'id': video_id,
                'title': title,
                'description': (try_get(video_metadata, lambda x: x['localized'][0]['shortDescription'], compat_str)
                                or (get_element_by_id('eventTitleContainer', webpage) or '').split(title)[-1]
                                or self._og_search_description(webpage)),
                'formats': fmts,
                'isLive': try_get(video_data, lambda x: x['streamInfo']['live'], bool) or False,
                'duration': int_or_none(video_data.get('durationInMs'), scale=1000),
                'timestamp': parse_iso8601(try_get(video_metadata, lambda x: x['created'])),
                'release_timestamp': parse_iso8601(try_get(video_metadata, lambda x: x['publications'][0]['publicationDate'])),
                'thumbnail': thumbnail,
            }
        webpage = self._download_webpage(
            'http://vodplayer.parliamentlive.tv/?mid=' + video_id, video_id)
        widget_config = self._parse_json(self._search_regex(
            r'(?s)kWidgetConfig\s*=\s*({.+});',
            webpage, 'kaltura widget config'), video_id)
        kaltura_url = 'kaltura:%s:%s' % (
            widget_config['wid'][1:], widget_config['entry_id'])
        event_title = self._download_json(
            'http://parliamentlive.tv/Event/GetShareVideo/' + video_id, video_id)['event']['title']
        return {
            '_type': 'url_transparent',
            'title': event_title,
            'description': '',
            'url': kaltura_url,
            'ie_key': 'Kaltura',
        }
