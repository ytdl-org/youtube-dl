from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_parse_urlparse,
    compat_urlparse,
    ExtractorError,
    find_xpath_attr,
    int_or_none,
    orderedSet,
    xpath_with_ns,
)


class LivestreamIE(InfoExtractor):
    IE_NAME = 'livestream'
    _VALID_URL = r'https?://new\.livestream\.com/.*?/(?P<event_name>.*?)(/videos/(?P<id>[0-9]+)(?:/player)?)?/?(?:$|[?#])'
    _TESTS = [{
        'url': 'http://new.livestream.com/CoheedandCambria/WebsterHall/videos/4719370',
        'md5': '53274c76ba7754fb0e8d072716f2292b',
        'info_dict': {
            'id': '4719370',
            'ext': 'mp4',
            'title': 'Live from Webster Hall NYC',
            'upload_date': '20121012',
            'like_count': int,
            'view_count': int,
            'thumbnail': 're:^http://.*\.jpg$'
        }
    }, {
        'url': 'http://new.livestream.com/tedx/cityenglish',
        'info_dict': {
            'title': 'TEDCity2.0 (English)',
        },
        'playlist_mincount': 4,
    }, {
        'url': 'https://new.livestream.com/accounts/362/events/3557232/videos/67864563/player?autoPlay=false&height=360&mute=false&width=640',
        'only_matching': True,
    }]

    def _parse_smil(self, video_id, smil_url):
        formats = []
        _SWITCH_XPATH = (
            './/{http://www.w3.org/2001/SMIL20/Language}body/'
            '{http://www.w3.org/2001/SMIL20/Language}switch')
        smil_doc = self._download_xml(
            smil_url, video_id,
            note='Downloading SMIL information',
            errnote='Unable to download SMIL information',
            fatal=False)
        if smil_doc is False:  # Download failed
            return formats
        title_node = find_xpath_attr(
            smil_doc, './/{http://www.w3.org/2001/SMIL20/Language}meta',
            'name', 'title')
        if title_node is None:
            self.report_warning('Cannot find SMIL id')
            switch_node = smil_doc.find(_SWITCH_XPATH)
        else:
            title_id = title_node.attrib['content']
            switch_node = find_xpath_attr(
                smil_doc, _SWITCH_XPATH, 'id', title_id)
        if switch_node is None:
            raise ExtractorError('Cannot find switch node')
        video_nodes = switch_node.findall(
            '{http://www.w3.org/2001/SMIL20/Language}video')

        for vn in video_nodes:
            tbr = int_or_none(vn.attrib.get('system-bitrate'))
            furl = (
                'http://livestream-f.akamaihd.net/%s?v=3.0.3&fp=WIN%%2014,0,0,145' %
                (vn.attrib['src']))
            if 'clipBegin' in vn.attrib:
                furl += '&ssek=' + vn.attrib['clipBegin']
            formats.append({
                'url': furl,
                'format_id': 'smil_%d' % tbr,
                'ext': 'flv',
                'tbr': tbr,
                'preference': -1000,
            })
        return formats

    def _extract_video_info(self, video_data):
        video_id = compat_str(video_data['id'])

        FORMAT_KEYS = (
            ('sd', 'progressive_url'),
            ('hd', 'progressive_url_hd'),
        )
        formats = [{
            'format_id': format_id,
            'url': video_data[key],
            'quality': i + 1,
        } for i, (format_id, key) in enumerate(FORMAT_KEYS)
            if video_data.get(key)]

        smil_url = video_data.get('smil_url')
        if smil_url:
            formats.extend(self._parse_smil(video_id, smil_url))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_data['caption'],
            'thumbnail': video_data.get('thumbnail_url'),
            'upload_date': video_data['updated_at'].replace('-', '')[:8],
            'like_count': video_data.get('likes', {}).get('total'),
            'view_count': video_data.get('views'),
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        event_name = mobj.group('event_name')
        webpage = self._download_webpage(url, video_id or event_name)

        og_video = self._og_search_video_url(
            webpage, 'player url', fatal=False, default=None)
        if og_video is not None:
            query_str = compat_urllib_parse_urlparse(og_video).query
            query = compat_urlparse.parse_qs(query_str)
            if 'play_url' in query:
                api_url = query['play_url'][0].replace('.smil', '')
                info = json.loads(self._download_webpage(
                    api_url, video_id, 'Downloading video info'))
                return self._extract_video_info(info)

        config_json = self._search_regex(
            r'window.config = ({.*?});', webpage, 'window config')
        info = json.loads(config_json)['event']

        def is_relevant(vdata, vid):
            result = vdata['type'] == 'video'
            if video_id is not None:
                result = result and compat_str(vdata['data']['id']) == vid
            return result

        videos = [self._extract_video_info(video_data['data'])
                  for video_data in info['feed']['data']
                  if is_relevant(video_data, video_id)]
        if video_id is None:
            # This is an event page:
            return self.playlist_result(videos, info['id'], info['full_name'])
        else:
            if not videos:
                raise ExtractorError('Cannot find video %s' % video_id)
            return videos[0]


# The original version of Livestream uses a different system
class LivestreamOriginalIE(InfoExtractor):
    IE_NAME = 'livestream:original'
    _VALID_URL = r'''(?x)https?://www\.livestream\.com/
        (?P<user>[^/]+)/(?P<type>video|folder)
        (?:\?.*?Id=|/)(?P<id>.*?)(&|$)
        '''
    _TESTS = [{
        'url': 'http://www.livestream.com/dealbook/video?clipId=pla_8aa4a3f1-ba15-46a4-893b-902210e138fb',
        'info_dict': {
            'id': 'pla_8aa4a3f1-ba15-46a4-893b-902210e138fb',
            'ext': 'flv',
            'title': 'Spark 1 (BitCoin) with Cameron Winklevoss & Tyler Winklevoss of Winklevoss Capital',
        },
        'params': {
            # rtmp
            'skip_download': True,
        },
    }, {
        'url': 'https://www.livestream.com/newplay/folder?dirId=a07bf706-d0e4-4e75-a747-b021d84f2fd3',
        'info_dict': {
            'id': 'a07bf706-d0e4-4e75-a747-b021d84f2fd3',
        },
        'playlist_mincount': 4,
    }]

    def _extract_video(self, user, video_id):
        api_url = 'http://x{0}x.api.channel.livestream.com/2.0/clipdetails?extendedInfo=true&id={1}'.format(user, video_id)

        info = self._download_xml(api_url, video_id)
        item = info.find('channel').find('item')
        ns = {'media': 'http://search.yahoo.com/mrss'}
        thumbnail_url = item.find(xpath_with_ns('media:thumbnail', ns)).attrib['url']
        # Remove the extension and number from the path (like 1.jpg)
        path = self._search_regex(r'(user-files/.+)_.*?\.jpg$', thumbnail_url, 'path')

        return {
            'id': video_id,
            'title': item.find('title').text,
            'url': 'rtmp://extondemand.livestream.com/ondemand',
            'play_path': 'trans/dv15/mogulus-{0}'.format(path),
            'player_url': 'http://static.livestream.com/chromelessPlayer/v21/playerapi.swf?hash=5uetk&v=0803&classid=D27CDB6E-AE6D-11cf-96B8-444553540000&jsEnabled=false&wmode=opaque',
            'ext': 'flv',
            'thumbnail': thumbnail_url,
        }

    def _extract_folder(self, url, folder_id):
        webpage = self._download_webpage(url, folder_id)
        paths = orderedSet(re.findall(
            r'''(?x)(?:
                <li\s+class="folder">\s*<a\s+href="|
                <a\s+href="(?=https?://livestre\.am/)
            )([^"]+)"''', webpage))

        return {
            '_type': 'playlist',
            'id': folder_id,
            'entries': [{
                '_type': 'url',
                'url': compat_urlparse.urljoin(url, p),
            } for p in paths],
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        id = mobj.group('id')
        user = mobj.group('user')
        url_type = mobj.group('type')
        if url_type == 'folder':
            return self._extract_folder(url, id)
        else:
            return self._extract_video(user, id)


# The server doesn't support HEAD request, the generic extractor can't detect
# the redirection
class LivestreamShortenerIE(InfoExtractor):
    IE_NAME = 'livestream:shortener'
    IE_DESC = False  # Do not list
    _VALID_URL = r'https?://livestre\.am/(?P<id>.+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        id = mobj.group('id')
        webpage = self._download_webpage(url, id)

        return {
            '_type': 'url',
            'url': self._og_search_url(webpage),
        }
