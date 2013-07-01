import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_parse,

    ExtractorError,
    unified_strdate,
)


class ComedyCentralIE(InfoExtractor):
    IE_DESC = u'The Daily Show / Colbert Report'
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
                              |(watch/(?P<date>[^/]*)/(?P<tdstitle>.*)))))
                     $"""
    _TEST = {
        u'url': u'http://www.thedailyshow.com/watch/thu-december-13-2012/kristen-stewart',
        u'file': u'422212.mp4',
        u'md5': u'4e2f5cb088a83cd8cdb7756132f9739d',
        u'info_dict': {
            u"upload_date": u"20121214", 
            u"description": u"Kristen Stewart", 
            u"uploader": u"thedailyshow", 
            u"title": u"thedailyshow-kristen-stewart part 1"
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
        '3500': '1280x720',
        '2200': '960x540',
        '1700': '768x432',
        '1200': '640x360',
        '750': '512x288',
        '400': '384x216',
    }

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _print_formats(self, formats):
        print('Available formats:')
        for x in formats:
            print('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'mp4'), self._video_dimensions.get(x, '???')))


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        if mobj.group('shortname'):
            if mobj.group('shortname') in ('tds', 'thedailyshow'):
                url = u'http://www.thedailyshow.com/full-episodes/'
            else:
                url = u'http://www.colbertnation.com/full-episodes/'
            mobj = re.match(self._VALID_URL, url, re.VERBOSE)
            assert mobj is not None

        if mobj.group('clip'):
            if mobj.group('showname') == 'thedailyshow':
                epTitle = mobj.group('tdstitle')
            else:
                epTitle = mobj.group('cntitle')
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
                raise ExtractorError(u'Invalid redirected URL: ' + url)
            if mobj.group('episode') == '':
                raise ExtractorError(u'Redirected URL is still not specific: ' + url)
            epTitle = mobj.group('episode')

        mMovieParams = re.findall('(?:<param name="movie" value="|var url = ")(http://media.mtvnservices.com/([^"]*(?:episode|video).*?:.*?))"', webpage)

        if len(mMovieParams) == 0:
            # The Colbert Report embeds the information in a without
            # a URL prefix; so extract the alternate reference
            # and then add the URL prefix manually.

            altMovieParams = re.findall('data-mgid="([^"]*(?:episode|video).*?:.*?)"', webpage)
            if len(altMovieParams) == 0:
                raise ExtractorError(u'unable to find Flash URL in webpage ' + url)
            else:
                mMovieParams = [("http://media.mtvnservices.com/" + altMovieParams[0], altMovieParams[0])]

        uri = mMovieParams[0][1]
        indexUrl = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?' + compat_urllib_parse.urlencode({'uri': uri})
        indexXml = self._download_webpage(indexUrl, epTitle,
                                          u'Downloading show index',
                                          u'unable to download episode index')

        results = []

        idoc = xml.etree.ElementTree.fromstring(indexXml)
        itemEls = idoc.findall('.//item')
        for partNum,itemEl in enumerate(itemEls):
            mediaId = itemEl.findall('./guid')[0].text
            shortMediaId = mediaId.split(':')[-1]
            showId = mediaId.split(':')[-2].replace('.com', '')
            officialTitle = itemEl.findall('./title')[0].text
            officialDate = unified_strdate(itemEl.findall('./pubDate')[0].text)

            configUrl = ('http://www.comedycentral.com/global/feeds/entertainment/media/mediaGenEntertainment.jhtml?' +
                        compat_urllib_parse.urlencode({'uri': mediaId}))
            configXml = self._download_webpage(configUrl, epTitle,
                                               u'Downloading configuration for %s' % shortMediaId)

            cdoc = xml.etree.ElementTree.fromstring(configXml)
            turls = []
            for rendition in cdoc.findall('.//rendition'):
                finfo = (rendition.attrib['bitrate'], rendition.findall('./src')[0].text)
                turls.append(finfo)

            if len(turls) == 0:
                self._downloader.report_error(u'unable to download ' + mediaId + ': No videos found')
                continue

            if self._downloader.params.get('listformats', None):
                self._print_formats([i[0] for i in turls])
                return

            # For now, just pick the highest bitrate
            format,rtmp_video_url = turls[-1]

            # Get the format arg from the arg stream
            req_format = self._downloader.params.get('format', None)

            # Select format if we can find one
            for f,v in turls:
                if f == req_format:
                    format, rtmp_video_url = f, v
                    break

            m = re.match(r'^rtmpe?://.*?/(?P<finalid>gsp.comedystor/.*)$', rtmp_video_url)
            if not m:
                raise ExtractorError(u'Cannot transform RTMP url')
            base = 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=1+_pxI0=Ripod-h264+_pxL0=undefined+_pxM0=+_pxK=18639+_pxE=mp4/44620/mtvnorigin/'
            video_url = base + m.group('finalid')

            effTitle = showId + u'-' + epTitle + u' part ' + compat_str(partNum+1)
            info = {
                'id': shortMediaId,
                'url': video_url,
                'uploader': showId,
                'upload_date': officialDate,
                'title': effTitle,
                'ext': 'mp4',
                'format': format,
                'thumbnail': None,
                'description': compat_str(officialTitle),
            }
            results.append(info)

        return results
