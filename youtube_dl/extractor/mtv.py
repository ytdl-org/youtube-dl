from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    ExtractorError,
    find_xpath_attr,
    fix_xml_ampersands,
    url_basename,
    RegexNotFoundError,
)


def _media_xml_tag(tag):
    return '{http://search.yahoo.com/mrss/}%s' % tag


class MTVServicesInfoExtractor(InfoExtractor):
    @staticmethod
    def _id_from_uri(uri):
        return uri.split(':')[-1]

    # This was originally implemented for ComedyCentral, but it also works here
    @staticmethod
    def _transform_rtmp_url(rtmp_video_url):
        m = re.match(r'^rtmpe?://.*?/(?P<finalid>gsp\..+?/.*)$', rtmp_video_url)
        if not m:
            return rtmp_video_url
        base = 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=1+_pxI0=Ripod-h264+_pxL0=undefined+_pxM0=+_pxK=18639+_pxE=mp4/44620/mtvnorigin/'
        return base + m.group('finalid')

    def _get_thumbnail_url(self, uri, itemdoc):
        search_path = '%s/%s' % (_media_xml_tag('group'), _media_xml_tag('thumbnail'))
        thumb_node = itemdoc.find(search_path)
        if thumb_node is None:
            return None
        else:
            return thumb_node.attrib['url']

    def _extract_video_formats(self, mdoc):
        if re.match(r'.*/error_country_block\.swf$', mdoc.find('.//src').text) is not None:
            raise ExtractorError('This video is not available from your country.', expected=True)

        formats = []
        for rendition in mdoc.findall('.//rendition'):
            try:
                _, _, ext = rendition.attrib['type'].partition('/')
                rtmp_video_url = rendition.find('./src').text
                formats.append({'ext': ext,
                                'url': self._transform_rtmp_url(rtmp_video_url),
                                'format_id': rendition.get('bitrate'),
                                'width': int(rendition.get('width')),
                                'height': int(rendition.get('height')),
                                })
            except (KeyError, TypeError):
                raise ExtractorError('Invalid rendition field.')
        return formats

    def _get_video_info(self, itemdoc):
        uri = itemdoc.find('guid').text
        video_id = self._id_from_uri(uri)
        self.report_extraction(video_id)
        mediagen_url = itemdoc.find('%s/%s' % (_media_xml_tag('group'), _media_xml_tag('content'))).attrib['url']
        # Remove the templates, like &device={device}
        mediagen_url = re.sub(r'&[^=]*?={.*?}(?=(&|$))', '', mediagen_url)
        if 'acceptMethods' not in mediagen_url:
            mediagen_url += '&acceptMethods=fms'

        mediagen_doc = self._download_xml(mediagen_url, video_id,
            'Downloading video urls')

        description_node = itemdoc.find('description')
        if description_node is not None:
            description = description_node.text.strip()
        else:
            description = None

        title_el = None
        if title_el is None:
            title_el = find_xpath_attr(
                itemdoc, './/{http://search.yahoo.com/mrss/}category',
                'scheme', 'urn:mtvn:video_title')
        if title_el is None:
            title_el = itemdoc.find('.//{http://search.yahoo.com/mrss/}title')
        if title_el is None:
            title_el = itemdoc.find('.//title')
        title = title_el.text
        if title is None:
            raise ExtractorError('Could not find video title')
        title = title.strip()

        return {
            'title': title,
            'formats': self._extract_video_formats(mediagen_doc),
            'id': video_id,
            'thumbnail': self._get_thumbnail_url(uri, itemdoc),
            'description': description,
        }

    def _get_videos_info(self, uri):
        video_id = self._id_from_uri(uri)
        data = compat_urllib_parse.urlencode({'uri': uri})

        idoc = self._download_xml(
            self._FEED_URL + '?' + data, video_id,
            'Downloading info', transform_source=fix_xml_ampersands)
        return [self._get_video_info(item) for item in idoc.findall('.//item')]

    def _real_extract(self, url):
        title = url_basename(url)
        webpage = self._download_webpage(url, title)
        try:
            # the url can be http://media.mtvnservices.com/fb/{mgid}.swf
            # or http://media.mtvnservices.com/{mgid}
            og_url = self._og_search_video_url(webpage)
            mgid = url_basename(og_url)
            if mgid.endswith('.swf'):
                mgid = mgid[:-4]
        except RegexNotFoundError:
            mgid = self._search_regex(
                [r'data-mgid="(.*?)"', r'swfobject.embedSWF\(".*?(mgid:.*?)"'],
                webpage, u'mgid')
        return self._get_videos_info(mgid)


class MTVIE(MTVServicesInfoExtractor):
    _VALID_URL = r'''(?x)^https?://
        (?:(?:www\.)?mtv\.com/videos/.+?/(?P<videoid>[0-9]+)/[^/]+$|
           m\.mtv\.com/videos/video\.rbml\?.*?id=(?P<mgid>[^&]+))'''

    _FEED_URL = 'http://www.mtv.com/player/embed/AS3/rss/'

    _TESTS = [
        {
            'url': 'http://www.mtv.com/videos/misc/853555/ours-vh1-storytellers.jhtml',
            'file': '853555.mp4',
            'md5': '850f3f143316b1e71fa56a4edfd6e0f8',
            'info_dict': {
                'title': 'Taylor Swift - "Ours (VH1 Storytellers)"',
                'description': 'Album: Taylor Swift performs "Ours" for VH1 Storytellers at Harvey Mudd College.',
            },
        },
        {
            'add_ie': ['Vevo'],
            'url': 'http://www.mtv.com/videos/taylor-swift/916187/everything-has-changed-ft-ed-sheeran.jhtml',
            'file': 'USCJY1331283.mp4',
            'md5': '73b4e7fcadd88929292fe52c3ced8caf',
            'info_dict': {
                'title': 'Everything Has Changed',
                'upload_date': '20130606',
                'uploader': 'Taylor Swift',
            },
            'skip': 'VEVO is only available in some countries',
        },
    ]

    def _get_thumbnail_url(self, uri, itemdoc):
        return 'http://mtv.mtvnimages.com/uri/' + uri

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        uri = mobj.groupdict().get('mgid')
        if uri is None:
            webpage = self._download_webpage(url, video_id)
    
            # Some videos come from Vevo.com
            m_vevo = re.search(r'isVevoVideo = true;.*?vevoVideoId = "(.*?)";',
                               webpage, re.DOTALL)
            if m_vevo:
                vevo_id = m_vevo.group(1);
                self.to_screen('Vevo video detected: %s' % vevo_id)
                return self.url_result('vevo:%s' % vevo_id, ie='Vevo')
    
            uri = self._html_search_regex(r'/uri/(.*?)\?', webpage, 'uri')
        return self._get_videos_info(uri)


class MTVIggyIE(MTVServicesInfoExtractor):
    IE_NAME = 'mtviggy.com'
    _VALID_URL = r'https?://www\.mtviggy\.com/videos/.+'
    _TEST = {
        'url': 'http://www.mtviggy.com/videos/arcade-fire-behind-the-scenes-at-the-biggest-music-experiment-yet/',
        'info_dict': {
            'id': '984696',
            'ext': 'mp4',
            'title': 'Arcade Fire: Behind the Scenes at the Biggest Music Experiment Yet',
        }
    }
    _FEED_URL = 'http://all.mtvworldverticals.com/feed-xml/'
