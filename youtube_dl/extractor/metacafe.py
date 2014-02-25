import re

from .common import InfoExtractor
from ..utils import (
    compat_parse_qs,
    compat_urllib_parse,
    compat_urllib_request,
    determine_ext,
    ExtractorError,
)

class MetacafeIE(InfoExtractor):
    """Information Extractor for metacafe.com."""

    _VALID_URL = r'(?:http://)?(?:www\.)?metacafe\.com/watch/([^/]+)/([^/]+)/.*'
    _DISCLAIMER = 'http://www.metacafe.com/family_filter/'
    _FILTER_POST = 'http://www.metacafe.com/f/index.php?inputType=filter&controllerGroup=user'
    IE_NAME = u'metacafe'
    _TESTS = [
    # Youtube video
    {
        u"add_ie": ["Youtube"],
        u"url":  u"http://metacafe.com/watch/yt-_aUehQsCQtM/the_electric_company_short_i_pbs_kids_go/",
        u"file":  u"_aUehQsCQtM.mp4",
        u"info_dict": {
            u"upload_date": u"20090102",
            u"title": u"The Electric Company | \"Short I\" | PBS KIDS GO!",
            u"description": u"md5:2439a8ef6d5a70e380c22f5ad323e5a8",
            u"uploader": u"PBS",
            u"uploader_id": u"PBS"
        }
    },
    # Normal metacafe video
    {
        u'url': u'http://www.metacafe.com/watch/11121940/news_stuff_you_wont_do_with_your_playstation_4/',
        u'md5': u'6e0bca200eaad2552e6915ed6fd4d9ad',
        u'info_dict': {
            u'id': u'11121940',
            u'ext': u'mp4',
            u'title': u'News: Stuff You Won\'t Do with Your PlayStation 4',
            u'uploader': u'ign',
            u'description': u'Sony released a massive FAQ on the PlayStation Blog detailing the PS4\'s capabilities and limitations.',
        },
    },
    # AnyClip video
    {
        u"url": u"http://www.metacafe.com/watch/an-dVVXnuY7Jh77J/the_andromeda_strain_1971_stop_the_bomb_part_3/",
        u"file": u"an-dVVXnuY7Jh77J.mp4",
        u"info_dict": {
            u"title": u"The Andromeda Strain (1971): Stop the Bomb Part 3",
            u"uploader": u"anyclip",
            u"description": u"md5:38c711dd98f5bb87acf973d573442e67",
        },
    },
    # age-restricted video
    {
        u'url': u'http://www.metacafe.com/watch/5186653/bbc_internal_christmas_tape_79_uncensored_outtakes_etc/',
        u'md5': u'98dde7c1a35d02178e8ab7560fe8bd09',
        u'info_dict': {
            u'id': u'5186653',
            u'ext': u'mp4',
            u'title': u'BBC INTERNAL Christmas Tape \'79 - UNCENSORED Outtakes, Etc.',
            u'uploader': u'Dwayne Pipe',
            u'description': u'md5:950bf4c581e2c059911fa3ffbe377e4b',
            u'age_limit': 18,
        },
    },
    # cbs video
    {
        u'url': u'http://www.metacafe.com/watch/cb-0rOxMBabDXN6/samsung_galaxy_note_2_samsungs_next_generation_phablet/',
        u'info_dict': {
            u'id': u'0rOxMBabDXN6',
            u'ext': u'flv',
            u'title': u'Samsung Galaxy Note 2: Samsung\'s next-generation phablet',
            u'description': u'md5:54d49fac53d26d5a0aaeccd061ada09d',
            u'duration': 129,
        },
        u'params': {
            # rtmp download
            u'skip_download': True,
        },
    },
    ]


    def report_disclaimer(self):
        """Report disclaimer retrieval."""
        self.to_screen(u'Retrieving disclaimer')

    def _real_initialize(self):
        # Retrieve disclaimer
        self.report_disclaimer()
        self._download_webpage(self._DISCLAIMER, None, False, u'Unable to retrieve disclaimer')

        # Confirm age
        disclaimer_form = {
            'filters': '0',
            'submit': "Continue - I'm over 18",
            }
        request = compat_urllib_request.Request(self._FILTER_POST, compat_urllib_parse.urlencode(disclaimer_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        self.report_age_confirmation()
        self._download_webpage(request, None, False, u'Unable to confirm age')

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group(1)

        # the video may come from an external site
        m_external = re.match('^(\w{2})-(.*)$', video_id)
        if m_external is not None:
            prefix, ext_id = m_external.groups()
            # Check if video comes from YouTube
            if prefix == 'yt':
                return self.url_result('http://www.youtube.com/watch?v=%s' % ext_id, 'Youtube')
            # CBS videos use theplatform.com
            if prefix == 'cb':
                return self.url_result('theplatform:%s' % ext_id, 'ThePlatform')

        # Retrieve video webpage to extract further information
        req = compat_urllib_request.Request('http://www.metacafe.com/watch/%s/' % video_id)

        # AnyClip videos require the flashversion cookie so that we get the link
        # to the mp4 file
        mobj_an = re.match(r'^an-(.*?)$', video_id)
        if mobj_an:
            req.headers['Cookie'] = 'flashVersion=0;'
        webpage = self._download_webpage(req, video_id)

        # Extract URL, uploader and title from webpage
        self.report_extraction(video_id)
        mobj = re.search(r'(?m)&mediaURL=([^&]+)', webpage)
        if mobj is not None:
            mediaURL = compat_urllib_parse.unquote(mobj.group(1))
            video_ext = mediaURL[-3:]

            # Extract gdaKey if available
            mobj = re.search(r'(?m)&gdaKey=(.*?)&', webpage)
            if mobj is None:
                video_url = mediaURL
            else:
                gdaKey = mobj.group(1)
                video_url = '%s?__gda__=%s' % (mediaURL, gdaKey)
        else:
            mobj = re.search(r'<video src="([^"]+)"', webpage)
            if mobj:
                video_url = mobj.group(1)
                video_ext = 'mp4'
            else:
                mobj = re.search(r' name="flashvars" value="(.*?)"', webpage)
                if mobj is None:
                    raise ExtractorError(u'Unable to extract media URL')
                vardict = compat_parse_qs(mobj.group(1))
                if 'mediaData' not in vardict:
                    raise ExtractorError(u'Unable to extract media URL')
                mobj = re.search(r'"mediaURL":"(?P<mediaURL>http.*?)",(.*?)"key":"(?P<key>.*?)"', vardict['mediaData'][0])
                if mobj is None:
                    raise ExtractorError(u'Unable to extract media URL')
                mediaURL = mobj.group('mediaURL').replace('\\/', '/')
                video_url = '%s?__gda__=%s' % (mediaURL, mobj.group('key'))
                video_ext = determine_ext(video_url)

        video_title = self._html_search_regex(r'(?im)<title>(.*) - Video</title>', webpage, u'title')
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        video_uploader = self._html_search_regex(
                r'submitter=(.*?);|googletag\.pubads\(\)\.setTargeting\("(?:channel|submiter)","([^"]+)"\);',
                webpage, u'uploader nickname', fatal=False)

        if re.search(r'"contentRating":"restricted"', webpage) is not None:
            age_limit = 18
        else:
            age_limit = 0

        return {
            '_type':    'video',
            'id':       video_id,
            'url':      video_url,
            'description': description,
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'thumbnail':thumbnail,
            'ext':      video_ext,
            'age_limit': age_limit,
        }
