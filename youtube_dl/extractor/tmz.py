# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urllib_parse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
)


class TMZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/videos/(?P<id>\w+)/?'
    _TEST = {
        'url': 'http://www.tmz.com/videos/0_okj015ty/',
        'md5': '326b78a2ecf6a4185ac9109a3fc9b496',
        'info_dict': {
            'id': '0_okj015ty',
            'ext': 'mp4',
            'title': 'Kim Kardashian\'s Boobs Unlock a Mystery!',
            'description': 'Did Kim Kardasain try to one-up Khloe by one-upping Kylie???  Or is she just showing off her amazing boobs?',
            'duration': 101,
            'uploader_id': 'TMZ',
            'timestamp': 1394823600,
            'upload_date': '20140314',
        }
    }

    def _call_api(self, path, param):
        request = compat_urllib_request.Request(
            'https://cdn-mw-api.tmz.com/api/v1/%s/%s' % (path, compat_urllib_parse.quote(param)),
            headers={'X-TMZ-AUTH': '85bcfbd793d84806bd67fa8cb9b13525'})
        json_data = self._download_json(request, param)
        if json_data['errors']:
            raise ExtractorError(json_data['errors'][0]['friendlyMessage'])
        return json_data['item']

    def _parse_video_data(self, video_data):
        additionalProperties = video_data.get('additionalProperties', {})

        return {
            '_type': 'url_transparent',
            'url': 'kaltura:591531:%s' % additionalProperties.get('kalturaId'),
            'title': video_data['title'],
            'description': additionalProperties.get('description'),
            'thumbnail': additionalProperties.get('thumbnailUrl'),
            'duration': int_or_none(additionalProperties.get('duration')),
            'timestamp': parse_iso8601(video_data.get('publishedDate')),
            'uploader_id': 'TMZ',
        }

    def _real_extract(self, url):
        video_slug = self._match_id(url).replace('_', '-')

        video_data = self._call_api('videos/slug', video_slug)

        return self._parse_video_data(video_data)


class TMZArticleIE(TMZIE):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/(?P<id>\d{4}/\d{2}/\d{2}/[^/]+)/?'
    _TEST = {
        'url': 'http://www.tmz.com/2015/04/19/bobby-brown-bobbi-kristina-awake-video-concert',
        'md5': '5429c85db8bde39a473a56ca8c4c5602',
        'info_dict': {
            'id': '0_6snoelag',
            'ext': 'mp4',
            'title': 'Bobby Brown Tells Crowd ... Bobbi Kristina is Awake',
            'description': 'Bobby Brown stunned his audience during a concert Saturday night, when he told the crowd, "Bobbi is awake.  She\'s watching me."',
            'duration': 29,
            'uploader_id': 'TMZ',
            'upload_date': '20150419',
            'timestamp': 1429466400,
        }
    }

    def _real_extract(self, url):
        article_slug = self._match_id(url)
        article_data = self._call_api('articles/slug', article_slug)
        relatedItemReferences = article_data.get('relatedItemReferences', {})
        video_ids = relatedItemReferences.get('featuredVideo') or relatedItemReferences.get('videoSubAssets')
        if video_ids:
            video_data = self._call_api('videos', video_ids[0])
            return self._parse_video_data(video_data)
        else:
            raise ExtractorError('no video in article')
