from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    ExtractorError,
    find_xpath_attr,
    fix_xml_ampersands,
    HEADRequest,
    unescapeHTML,
    url_basename,
    RegexNotFoundError,
)


def _media_xml_tag(tag):
    return '{http://search.yahoo.com/mrss/}%s' % tag


class MTVServicesInfoExtractor(InfoExtractor):
    _MOBILE_TEMPLATE = None

    @staticmethod
    def _id_from_uri(uri):
        return uri.split(':')[-1]

    # This was originally implemented for ComedyCentral, but it also works here
    @staticmethod
    def _transform_rtmp_url(rtmp_video_url):
        m = re.match(r'^rtmpe?://.*?/(?P<finalid>gsp\..+?/.*)$', rtmp_video_url)
        if not m:
            return rtmp_video_url
        base = 'http://viacommtvstrmfs.fplive.net/'
        return base + m.group('finalid')

    def _get_feed_url(self, uri):
        return self._FEED_URL

    def _get_thumbnail_url(self, uri, itemdoc):
        search_path = '%s/%s' % (_media_xml_tag('group'), _media_xml_tag('thumbnail'))
        thumb_node = itemdoc.find(search_path)
        if thumb_node is None:
            return None
        else:
            return thumb_node.attrib['url']

    def _extract_mobile_video_formats(self, mtvn_id):
        webpage_url = self._MOBILE_TEMPLATE % mtvn_id
        req = compat_urllib_request.Request(webpage_url)
        # Otherwise we get a webpage that would execute some javascript
        req.add_header('Youtubedl-user-agent', 'curl/7')
        webpage = self._download_webpage(req, mtvn_id,
                                         'Downloading mobile page')
        metrics_url = unescapeHTML(self._search_regex(r'<a href="(http://metrics.+?)"', webpage, 'url'))
        req = HEADRequest(metrics_url)
        response = self._request_webpage(req, mtvn_id, 'Resolving url')
        url = response.geturl()
        # Transform the url to get the best quality:
        url = re.sub(r'.+pxE=mp4', 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=0+_pxK=18639+_pxE=mp4', url, 1)
        return [{'url': url, 'ext': 'mp4'}]

    def _extract_video_formats(self, mdoc, mtvn_id):
        if re.match(r'.*/(error_country_block\.swf|geoblock\.mp4)$', mdoc.find('.//src').text) is not None:
            if mtvn_id is not None and self._MOBILE_TEMPLATE is not None:
                self.to_screen('The normal version is not available from your '
                               'country, trying with the mobile version')
                return self._extract_mobile_video_formats(mtvn_id)
            raise ExtractorError('This video is not available from your country.',
                                 expected=True)

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
        self._sort_formats(formats)
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
            if title_el.text is None:
                title_el = None

        title = title_el.text
        if title is None:
            raise ExtractorError('Could not find video title')
        title = title.strip()

        # This a short id that's used in the webpage urls
        mtvn_id = None
        mtvn_id_node = find_xpath_attr(itemdoc, './/{http://search.yahoo.com/mrss/}category',
                                       'scheme', 'urn:mtvn:id')
        if mtvn_id_node is not None:
            mtvn_id = mtvn_id_node.text

        return {
            'title': title,
            'formats': self._extract_video_formats(mediagen_doc, mtvn_id),
            'id': video_id,
            'thumbnail': self._get_thumbnail_url(uri, itemdoc),
            'description': description,
        }

    def _get_videos_info(self, uri):
        video_id = self._id_from_uri(uri)
        feed_url = self._get_feed_url(uri)
        data = compat_urllib_parse.urlencode({'uri': uri})
        idoc = self._download_xml(
            feed_url + '?' + data, video_id,
            'Downloading info', transform_source=fix_xml_ampersands)
        return self.playlist_result(
            [self._get_video_info(item) for item in idoc.findall('.//item')])

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
            mgid = None

        if mgid is None or ':' not in mgid:
            mgid = self._search_regex(
                [r'data-mgid="(.*?)"', r'swfobject.embedSWF\(".*?(mgid:.*?)"'],
                webpage, 'mgid')
        return self._get_videos_info(mgid)


class MTVServicesEmbeddedIE(MTVServicesInfoExtractor):
    IE_NAME = 'mtvservices:embedded'
    _VALID_URL = r'https?://media\.mtvnservices\.com/embed/(?P<mgid>.+?)(\?|/|$)'

    _TEST = {
        # From http://www.thewrap.com/peter-dinklage-sums-up-game-of-thrones-in-45-seconds-video/
        'url': 'http://media.mtvnservices.com/embed/mgid:uma:video:mtv.com:1043906/cp~vid%3D1043906%26uri%3Dmgid%3Auma%3Avideo%3Amtv.com%3A1043906',
        'md5': 'cb349b21a7897164cede95bd7bf3fbb9',
        'info_dict': {
            'id': '1043906',
            'ext': 'mp4',
            'title': 'Peter Dinklage Sums Up \'Game Of Thrones\' In 45 Seconds',
            'description': '"Sexy sexy sexy, stabby stabby stabby, beautiful language," says Peter Dinklage as he tries summarizing "Game of Thrones" in under a minute.',
        },
    }

    def _get_feed_url(self, uri):
        video_id = self._id_from_uri(uri)
        site_id = uri.replace(video_id, '')
        config_url = ('http://media.mtvnservices.com/pmt/e1/players/{0}/'
                      'context4/context5/config.xml'.format(site_id))
        config_doc = self._download_xml(config_url, video_id)
        feed_node = config_doc.find('.//feed')
        feed_url = feed_node.text.strip().split('?')[0]
        return feed_url

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        mgid = mobj.group('mgid')
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
                vevo_id = m_vevo.group(1)
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
