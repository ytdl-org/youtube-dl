# encoding: utf-8

import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,

    ExtractorError,
    HEADRequest,
    smuggle_url,
    unescapeHTML,
    unified_strdate,
    url_basename,
)
from .brightcove import BrightcoveIE
from .ooyala import OoyalaIE


class GenericIE(InfoExtractor):
    IE_DESC = u'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = u'generic'
    _TESTS = [
        {
            u'url': u'http://www.hodiho.fr/2013/02/regis-plante-sa-jeep.html',
            u'file': u'13601338388002.mp4',
            u'md5': u'6e15c93721d7ec9e9ca3fdbf07982cfd',
            u'info_dict': {
                u"uploader": u"www.hodiho.fr",
                u"title": u"R\u00e9gis plante sa Jeep"
            }
        },
        # embedded vimeo video
        {
            u'add_ie': ['Vimeo'],
            u'url': u'http://skillsmatter.com/podcast/home/move-semanticsperfect-forwarding-and-rvalue-references',
            u'file': u'22444065.mp4',
            u'md5': u'2903896e23df39722c33f015af0666e2',
            u'info_dict': {
                u'title': u'ACCU 2011: Move Semantics,Perfect Forwarding, and Rvalue references- Scott Meyers- 13/04/2011',
                u"uploader_id": u"skillsmatter",
                u"uploader": u"Skills Matter",
            }
        },
        # bandcamp page with custom domain
        {
            u'add_ie': ['Bandcamp'],
            u'url': u'http://bronyrock.com/track/the-pony-mash',
            u'file': u'3235767654.mp3',
            u'info_dict': {
                u'title': u'The Pony Mash',
                u'uploader': u'M_Pallante',
            },
            u'skip': u'There is a limit of 200 free downloads / month for the test song',
        },
        # embedded brightcove video
        # it also tests brightcove videos that need to set the 'Referer' in the
        # http requests
        {
            u'add_ie': ['Brightcove'],
            u'url': u'http://www.bfmtv.com/video/bfmbusiness/cours-bourse/cours-bourse-l-analyse-technique-154522/',
            u'info_dict': {
                u'id': u'2765128793001',
                u'ext': u'mp4',
                u'title': u'Le cours de bourse : l’analyse technique',
                u'description': u'md5:7e9ad046e968cb2d1114004aba466fd9',
                u'uploader': u'BFM BUSINESS',
            },
            u'params': {
                u'skip_download': True,
            },
        },
        # Direct link to a video
        {
            u'url': u'http://media.w3.org/2010/05/sintel/trailer.mp4',
            u'file': u'trailer.mp4',
            u'md5': u'67d406c2bcb6af27fa886f31aa934bbe',
            u'info_dict': {
                u'id': u'trailer',
                u'title': u'trailer',
                u'upload_date': u'20100513',
            }
        },
        # ooyala video
        {
            u'url': u'http://www.rollingstone.com/music/videos/norwegian-dj-cashmere-cat-goes-spartan-on-with-me-premiere-20131219',
            u'md5': u'5644c6ca5d5782c1d0d350dad9bd840c',
            u'info_dict': {
                u'id': u'BwY2RxaTrTkslxOfcan0UCf0YqyvWysJ',
                u'ext': u'mp4',
                u'title': u'2cc213299525360.mov', #that's what we get
            },
        },
    ]

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        if not self._downloader.params.get('test', False):
            self._downloader.report_warning(u'Falling back on generic information extractor.')
        super(GenericIE, self).report_download_webpage(video_id)

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen(u'[redirect] Following redirect to %s' % new_url)

    def _send_head(self, url):
        """Check if it is a redirect, like url shorteners, in case return the new url."""

        class HEADRedirectHandler(compat_urllib_request.HTTPRedirectHandler):
            """
            Subclass the HTTPRedirectHandler to make it use our
            HEADRequest also on the redirected URL
            """
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if code in (301, 302, 303, 307):
                    newurl = newurl.replace(' ', '%20')
                    newheaders = dict((k,v) for k,v in req.headers.items()
                                      if k.lower() not in ("content-length", "content-type"))
                    return HEADRequest(newurl,
                                       headers=newheaders,
                                       origin_req_host=req.get_origin_req_host(),
                                       unverifiable=True)
                else:
                    raise compat_urllib_error.HTTPError(req.get_full_url(), code, msg, headers, fp)

        class HTTPMethodFallback(compat_urllib_request.BaseHandler):
            """
            Fallback to GET if HEAD is not allowed (405 HTTP error)
            """
            def http_error_405(self, req, fp, code, msg, headers):
                fp.read()
                fp.close()

                newheaders = dict((k,v) for k,v in req.headers.items()
                                  if k.lower() not in ("content-length", "content-type"))
                return self.parent.open(compat_urllib_request.Request(req.get_full_url(),
                                                 headers=newheaders,
                                                 origin_req_host=req.get_origin_req_host(),
                                                 unverifiable=True))

        # Build our opener
        opener = compat_urllib_request.OpenerDirector()
        for handler in [compat_urllib_request.HTTPHandler, compat_urllib_request.HTTPDefaultErrorHandler,
                        HTTPMethodFallback, HEADRedirectHandler,
                        compat_urllib_request.HTTPErrorProcessor, compat_urllib_request.HTTPSHandler]:
            opener.add_handler(handler())

        response = opener.open(HEADRequest(url))
        if response is None:
            raise ExtractorError(u'Invalid URL protocol')
        return response

    def _real_extract(self, url):
        parsed_url = compat_urlparse.urlparse(url)
        if not parsed_url.scheme:
            self._downloader.report_warning('The url doesn\'t specify the protocol, trying with http')
            return self.url_result('http://' + url)
        video_id = os.path.splitext(url.split('/')[-1])[0]

        self.to_screen(u'%s: Requesting header' % video_id)

        try:
            response = self._send_head(url)

            # Check for redirect
            new_url = response.geturl()
            if url != new_url:
                self.report_following_redirect(new_url)
                return self.url_result(new_url)

            # Check for direct link to a video
            content_type = response.headers.get('Content-Type', '')
            m = re.match(r'^(?P<type>audio|video|application(?=/ogg$))/(?P<format_id>.+)$', content_type)
            if m:
                upload_date = response.headers.get('Last-Modified')
                if upload_date:
                    upload_date = unified_strdate(upload_date)
                return {
                    'id': video_id,
                    'title': os.path.splitext(url_basename(url))[0],
                    'formats': [{
                        'format_id': m.group('format_id'),
                        'url': url,
                        'vcodec': u'none' if m.group('type') == 'audio' else None
                    }],
                    'upload_date': upload_date,
                }

        except compat_urllib_error.HTTPError:
            # This may be a stupid server that doesn't like HEAD, our UA, or so
            pass

        try:
            webpage = self._download_webpage(url, video_id)
        except ValueError:
            # since this is the last-resort InfoExtractor, if
            # this error is thrown, it'll be thrown here
            raise ExtractorError(u'Failed to download URL: %s' % url)

        self.report_extraction(video_id)

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, u'video title',
            default=u'video')

        # video uploader is domain name
        video_uploader = self._search_regex(
            r'^(?:https?://)?([^/]*)/.*', url, u'video uploader')

        # Look for BrightCove:
        bc_url = BrightcoveIE._extract_brightcove_url(webpage)
        if bc_url is not None:
            self.to_screen(u'Brightcove video detected.')
            return self.url_result(bc_url, 'Brightcove')

        # Look for embedded (iframe) Vimeo player
        mobj = re.search(
            r'<iframe[^>]+?src="(https?://player.vimeo.com/video/.+?)"', webpage)
        if mobj:
            player_url = unescapeHTML(mobj.group(1))
            surl = smuggle_url(player_url, {'Referer': url})
            return self.url_result(surl, 'Vimeo')

        # Look for embedded (swf embed) Vimeo player
        mobj = re.search(
            r'<embed[^>]+?src="(https?://(?:www\.)?vimeo.com/moogaloop.swf.+?)"', webpage)
        if mobj:
            return self.url_result(mobj.group(1), 'Vimeo')

        # Look for embedded YouTube player
        matches = re.findall(r'''(?x)
            (?:<iframe[^>]+?src=|embedSWF\(\s*)
            (["\'])(?P<url>(?:https?:)?//(?:www\.)?youtube\.com/
                (?:embed|v)/.+?)
            \1''', webpage)
        if matches:
            urlrs = [self.url_result(unescapeHTML(tuppl[1]), 'Youtube')
                     for tuppl in matches]
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for embedded Dailymotion player
        matches = re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?dailymotion\.com/embed/video/.+?)\1', webpage)
        if matches:
            urlrs = [self.url_result(unescapeHTML(tuppl[1]), 'Dailymotion')
                     for tuppl in matches]
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for embedded Wistia player
        match = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:fast\.)?wistia\.net/embed/iframe/.+?)\1', webpage)
        if match:
            return {
                '_type': 'url_transparent',
                'url': unescapeHTML(match.group('url')),
                'ie_key': 'Wistia',
                'uploader': video_uploader,
                'title': video_title,
                'id': video_id,
            }

        # Look for embedded blip.tv player
        mobj = re.search(r'<meta\s[^>]*https?://api.blip.tv/\w+/redirect/\w+/(\d+)', webpage)
        if mobj:
            return self.url_result('http://blip.tv/seo/-'+mobj.group(1), 'BlipTV')
        mobj = re.search(r'<(?:iframe|embed|object)\s[^>]*https?://(?:\w+\.)?blip.tv/(?:play/|api\.swf#)([a-zA-Z0-9]+)', webpage)
        if mobj:
            player_url = 'http://blip.tv/play/%s.x?p=1' % mobj.group(1)
            player_page = self._download_webpage(player_url, mobj.group(1))
            blip_video_id = self._search_regex(r'data-episode-id="(\d+)', player_page, u'blip_video_id', fatal=False)
            if blip_video_id:
                return self.url_result('http://blip.tv/seo/-'+blip_video_id, 'BlipTV')

        # Look for Bandcamp pages with custom domain
        mobj = re.search(r'<meta property="og:url"[^>]*?content="(.*?bandcamp\.com.*?)"', webpage)
        if mobj is not None:
            burl = unescapeHTML(mobj.group(1))
            # Don't set the extractor because it can be a track url or an album
            return self.url_result(burl)

        # Look for embedded Vevo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:cache\.)?vevo\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Ooyala videos
        mobj = re.search(r'player.ooyala.com/[^"?]+\?[^"]*?(?:embedCode|ec)=([^"&]+)', webpage)
        if mobj is not None:
            return OoyalaIE._build_url_result(mobj.group(1))

        # Look for Aparat videos
        mobj = re.search(r'<iframe src="(http://www.aparat.com/video/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Aparat')

        # Start with something easy: JW Player in SWFObject
        mobj = re.search(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit
            mobj = re.search(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit: JWPlayer JS loader
            mobj = re.search(r'[^A-Za-z0-9]?file["\']?:\s*["\'](http[^\'"]*)', webpage)
        if mobj is None:
            # Try to find twitter cards info
            mobj = re.search(r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage)
        if mobj is None:
            # We look for Open Graph info:
            # We have to match any number spaces between elements, some sites try to align them (eg.: statigr.am)
            m_video_type = re.search(r'<meta.*?property="og:video:type".*?content="video/(.*?)"', webpage)
            # We only look in og:video if the MIME type is a video, don't try if it's a Flash player:
            if m_video_type is not None:
                mobj = re.search(r'<meta.*?property="og:video".*?content="(.*?)"', webpage)
        if mobj is None:
            # HTML5 video
            mobj = re.search(r'<video[^<]*(?:>.*?<source.*?)? src="([^"]+)"', webpage, flags=re.DOTALL)
        if mobj is None:
            raise ExtractorError(u'Unsupported URL: %s' % url)

        # It's possible that one of the regexes
        # matched, but returned an empty group:
        if mobj.group(1) is None:
            raise ExtractorError(u'Did not find a valid video URL at %s' % url)

        video_url = mobj.group(1)
        video_url = compat_urlparse.urljoin(url, video_url)
        video_id = compat_urllib_parse.unquote(os.path.basename(video_url))

        # here's a fun little line of code for you:
        video_id = os.path.splitext(video_id)[0]

        return {
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'title':    video_title,
        }
