from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .mtv import MTVServicesInfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_parse,

    ExtractorError,
    unified_strdate,
)


class ComedyCentralIE(MTVServicesInfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?(comedycentral|cc)\.com/
        (video-clips|episodes|cc-studios|video-collections)
        /(?P<title>.*)'''
    _FEED_URL = 'http://comedycentral.com/feeds/mrss/'

    _TEST = {
        'url': 'http://www.comedycentral.com/video-clips/kllhuv/stand-up-greg-fitzsimmons--uncensored---too-good-of-a-mother',
        'md5': '4167875aae411f903b751a21f357f1ee',
        'info_dict': {
            'id': 'cef0cbb3-e776-4bc9-b62e-8016deccb354',
            'ext': 'mp4',
            'title': 'CC:Stand-Up|Greg Fitzsimmons: Life on Stage|Uncensored - Too Good of a Mother',
            'description': 'After a certain point, breastfeeding becomes c**kblocking.',
        },
    }


class ComedyCentralShowsIE(InfoExtractor):
    IE_DESC = 'The Daily Show / Colbert Report'
    # urls can be abbreviations like :thedailyshow or :colbert
    # urls for episodes like:
    # or urls for clips like: http://www.thedailyshow.com/watch/mon-december-10-2012/any-given-gun-day
    #                     or: http://www.colbertnation.com/the-colbert-report-videos/421667/november-29-2012/moon-shattering-news
    #                     or: http://www.colbertnation.com/the-colbert-report-collections/422008/festival-of-lights/79524
    _VALID_URL = r"""^(:(?P<shortname>tds|thedailyshow|cr|colbert|colbertnation|colbertreport)
                      |(https?://)?(www\.)?
                          (?P<showname>thedailyshow|colbertnation)\.com/
                         (full-episodes/(?P<episode>.*)|
                          (?P<clip>
                              (the-colbert-report-(videos|collections)/(?P<clipID>[0-9]+)/[^/]*/(?P<cntitle>.*?))
                              |(watch/(?P<date>[^/]*)/(?P<tdstitle>.*)))|
                          (?P<interview>
                              extended-interviews/(?P<interID>[0-9]+)/playlist_tds_extended_(?P<interview_title>.*?)/.*?)))
                     $"""
    _TEST = {
        'url': 'http://www.thedailyshow.com/watch/thu-december-13-2012/kristen-stewart',
        'file': '422212.mp4',
        'md5': '4e2f5cb088a83cd8cdb7756132f9739d',
        'info_dict': {
            "upload_date": "20121214",
            "description": "Kristen Stewart",
            "uploader": "thedailyshow",
            "title": "thedailyshow-kristen-stewart part 1"
        }
    }

    _available_formats = ['3500', '2200', '1700', '1200', '750', '400']

    _video_extensions = {
        '3500': 'mp4',
        '2200': 'mp4',
        '1700': 'mp4',
        '1200': 'mp4',
        '750': 'mp4',
        '400': 'mp4',
    }
    _video_dimensions = {
        '3500': (1280, 720),
        '2200': (960, 540),
        '1700': (768, 432),
        '1200': (640, 360),
        '750': (512, 288),
        '400': (384, 216),
    }

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    @staticmethod
    def _transform_rtmp_url(rtmp_video_url):
        m = re.match(r'^rtmpe?://.*?/(?P<finalid>gsp\.comedystor/.*)$', rtmp_video_url)
        if not m:
            raise ExtractorError('Cannot transform RTMP url')
        base = 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=1+_pxI0=Ripod-h264+_pxL0=undefined+_pxM0=+_pxK=18639+_pxE=mp4/44620/mtvnorigin/'
        return base + m.group('finalid')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)

        if mobj.group('shortname'):
            if mobj.group('shortname') in ('tds', 'thedailyshow'):
                url = 'http://www.thedailyshow.com/full-episodes/'
            else:
                url = 'http://www.colbertnation.com/full-episodes/'
            mobj = re.match(self._VALID_URL, url, re.VERBOSE)
            assert mobj is not None

        if mobj.group('clip'):
            if mobj.group('showname') == 'thedailyshow':
                epTitle = mobj.group('tdstitle')
            else:
                epTitle = mobj.group('cntitle')
            dlNewest = False
        elif mobj.group('interview'):
            epTitle = mobj.group('interview_title')
            dlNewest = False
        else:
            dlNewest = not mobj.group('episode')
            if dlNewest:
                epTitle = mobj.group('showname')
            else:
                epTitle = mobj.group('episode')

        self.report_extraction(epTitle)
        webpage,htmlHandle = self._download_webpage_handle(url, epTitle)
        if dlNewest:
            url = htmlHandle.geturl()
            mobj = re.match(self._VALID_URL, url, re.VERBOSE)
            if mobj is None:
                raise ExtractorError('Invalid redirected URL: ' + url)
            if mobj.group('episode') == '':
                raise ExtractorError('Redirected URL is still not specific: ' + url)
            epTitle = mobj.group('episode')

        mMovieParams = re.findall('(?:<param name="movie" value="|var url = ")(http://media.mtvnservices.com/([^"]*(?:episode|video).*?:.*?))"', webpage)

        if len(mMovieParams) == 0:
            # The Colbert Report embeds the information in a without
            # a URL prefix; so extract the alternate reference
            # and then add the URL prefix manually.

            altMovieParams = re.findall('data-mgid="([^"]*(?:episode|video).*?:.*?)"', webpage)
            if len(altMovieParams) == 0:
                raise ExtractorError('unable to find Flash URL in webpage ' + url)
            else:
                mMovieParams = [("http://media.mtvnservices.com/" + altMovieParams[0], altMovieParams[0])]

        uri = mMovieParams[0][1]
        indexUrl = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?' + compat_urllib_parse.urlencode({'uri': uri})
        idoc = self._download_xml(indexUrl, epTitle,
                                          'Downloading show index',
                                          'unable to download episode index')

        results = []

        itemEls = idoc.findall('.//item')
        for partNum,itemEl in enumerate(itemEls):
            mediaId = itemEl.findall('./guid')[0].text
            shortMediaId = mediaId.split(':')[-1]
            showId = mediaId.split(':')[-2].replace('.com', '')
            officialTitle = itemEl.findall('./title')[0].text
            officialDate = unified_strdate(itemEl.findall('./pubDate')[0].text)

            configUrl = ('http://www.comedycentral.com/global/feeds/entertainment/media/mediaGenEntertainment.jhtml?' +
                        compat_urllib_parse.urlencode({'uri': mediaId}))
            cdoc = self._download_xml(configUrl, epTitle,
                                               'Downloading configuration for %s' % shortMediaId)

            turls = []
            for rendition in cdoc.findall('.//rendition'):
                finfo = (rendition.attrib['bitrate'], rendition.findall('./src')[0].text)
                turls.append(finfo)

            if len(turls) == 0:
                self._downloader.report_error('unable to download ' + mediaId + ': No videos found')
                continue

            formats = []
            for format, rtmp_video_url in turls:
                w, h = self._video_dimensions.get(format, (None, None))
                formats.append({
                    'url': self._transform_rtmp_url(rtmp_video_url),
                    'ext': self._video_extensions.get(format, 'mp4'),
                    'format_id': format,
                    'height': h,
                    'width': w,
                })

            effTitle = showId + '-' + epTitle + ' part ' + compat_str(partNum+1)
            results.append({
                'id': shortMediaId,
                'formats': formats,
                'uploader': showId,
                'upload_date': officialDate,
                'title': effTitle,
                'thumbnail': None,
                'description': compat_str(officialTitle),
            })

        return results
