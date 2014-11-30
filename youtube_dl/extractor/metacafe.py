from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_parse_qs,
    compat_urllib_parse,
    compat_urllib_request,
    determine_ext,
    ExtractorError,
    int_or_none,
)


class MetacafeIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?metacafe\.com/watch/([^/]+)/([^/]+)/.*'
    _DISCLAIMER = 'http://www.metacafe.com/family_filter/'
    _FILTER_POST = 'http://www.metacafe.com/f/index.php?inputType=filter&controllerGroup=user'
    IE_NAME = 'metacafe'
    _TESTS = [
        # Youtube video
        {
            'add_ie': ['Youtube'],
            'url': 'http://metacafe.com/watch/yt-_aUehQsCQtM/the_electric_company_short_i_pbs_kids_go/',
            'info_dict': {
                'id': '_aUehQsCQtM',
                'ext': 'mp4',
                'upload_date': '20090102',
                'title': 'The Electric Company | "Short I" | PBS KIDS GO!',
                'description': 'md5:2439a8ef6d5a70e380c22f5ad323e5a8',
                'uploader': 'PBS',
                'uploader_id': 'PBS'
            }
        },
        # Normal metacafe video
        {
            'url': 'http://www.metacafe.com/watch/11121940/news_stuff_you_wont_do_with_your_playstation_4/',
            'md5': '6e0bca200eaad2552e6915ed6fd4d9ad',
            'info_dict': {
                'id': '11121940',
                'ext': 'mp4',
                'title': 'News: Stuff You Won\'t Do with Your PlayStation 4',
                'uploader': 'ign',
                'description': 'Sony released a massive FAQ on the PlayStation Blog detailing the PS4\'s capabilities and limitations.',
            },
        },
        # AnyClip video
        {
            'url': 'http://www.metacafe.com/watch/an-dVVXnuY7Jh77J/the_andromeda_strain_1971_stop_the_bomb_part_3/',
            'info_dict': {
                'id': 'an-dVVXnuY7Jh77J',
                'ext': 'mp4',
                'title': 'The Andromeda Strain (1971): Stop the Bomb Part 3',
                'uploader': 'anyclip',
                'description': 'md5:38c711dd98f5bb87acf973d573442e67',
            },
        },
        # age-restricted video
        {
            'url': 'http://www.metacafe.com/watch/5186653/bbc_internal_christmas_tape_79_uncensored_outtakes_etc/',
            'md5': '98dde7c1a35d02178e8ab7560fe8bd09',
            'info_dict': {
                'id': '5186653',
                'ext': 'mp4',
                'title': 'BBC INTERNAL Christmas Tape \'79 - UNCENSORED Outtakes, Etc.',
                'uploader': 'Dwayne Pipe',
                'description': 'md5:950bf4c581e2c059911fa3ffbe377e4b',
                'age_limit': 18,
            },
        },
        # cbs video
        {
            'url': 'http://www.metacafe.com/watch/cb-8VD4r_Zws8VP/open_this_is_face_the_nation_february_9/',
            'info_dict': {
                'id': '8VD4r_Zws8VP',
                'ext': 'flv',
                'title': 'Open: This is Face the Nation, February 9',
                'description': 'md5:8a9ceec26d1f7ed6eab610834cc1a476',
                'duration': 96,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        # Movieclips.com video
        {
            'url': 'http://www.metacafe.com/watch/mv-Wy7ZU/my_week_with_marilyn_do_you_love_me/',
            'info_dict': {
                'id': 'mv-Wy7ZU',
                'ext': 'mp4',
                'title': 'My Week with Marilyn - Do You Love Me?',
                'description': 'From the movie My Week with Marilyn - Colin (Eddie Redmayne) professes his love to Marilyn (Michelle Williams) and gets her to promise to return to set and finish the movie.',
                'uploader': 'movie_trailers',
                'duration': 176,
            },
            'params': {
                'skip_download': 'requires rtmpdump',
            }
        }
    ]

    def report_disclaimer(self):
        self.to_screen('Retrieving disclaimer')

    def _real_initialize(self):
        # Retrieve disclaimer
        self.report_disclaimer()
        self._download_webpage(self._DISCLAIMER, None, False, 'Unable to retrieve disclaimer')

        # Confirm age
        disclaimer_form = {
            'filters': '0',
            'submit': "Continue - I'm over 18",
        }
        request = compat_urllib_request.Request(self._FILTER_POST, compat_urllib_parse.urlencode(disclaimer_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        self.report_age_confirmation()
        self._download_webpage(request, None, False, 'Unable to confirm age')

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)

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
        video_url = None
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
        if video_url is None:
            mobj = re.search(r'<video src="([^"]+)"', webpage)
            if mobj:
                video_url = mobj.group(1)
                video_ext = 'mp4'
        if video_url is None:
            flashvars = self._search_regex(
                r' name="flashvars" value="(.*?)"', webpage, 'flashvars',
                default=None)
            if flashvars:
                vardict = compat_parse_qs(flashvars)
                if 'mediaData' not in vardict:
                    raise ExtractorError('Unable to extract media URL')
                mobj = re.search(
                    r'"mediaURL":"(?P<mediaURL>http.*?)",(.*?)"key":"(?P<key>.*?)"', vardict['mediaData'][0])
                if mobj is None:
                    raise ExtractorError('Unable to extract media URL')
                mediaURL = mobj.group('mediaURL').replace('\\/', '/')
                video_url = '%s?__gda__=%s' % (mediaURL, mobj.group('key'))
                video_ext = determine_ext(video_url)
        if video_url is None:
            player_url = self._search_regex(
                r"swfobject\.embedSWF\('([^']+)'",
                webpage, 'config URL', default=None)
            if player_url:
                config_url = self._search_regex(
                    r'config=(.+)$', player_url, 'config URL')
                config_doc = self._download_xml(
                    config_url, video_id,
                    note='Downloading video config')
                smil_url = config_doc.find('.//properties').attrib['smil_file']
                smil_doc = self._download_xml(
                    smil_url, video_id,
                    note='Downloading SMIL document')
                base_url = smil_doc.find('./head/meta').attrib['base']
                video_url = []
                for vn in smil_doc.findall('.//video'):
                    br = int(vn.attrib['system-bitrate'])
                    play_path = vn.attrib['src']
                    video_url.append({
                        'format_id': 'smil-%d' % br,
                        'url': base_url,
                        'play_path': play_path,
                        'page_url': url,
                        'player_url': player_url,
                        'ext': play_path.partition(':')[0],
                    })

        if video_url is None:
            raise ExtractorError('Unsupported video type')

        video_title = self._html_search_regex(
            r'(?im)<title>(.*) - Video</title>', webpage, 'title')
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        video_uploader = self._html_search_regex(
            r'submitter=(.*?);|googletag\.pubads\(\)\.setTargeting\("(?:channel|submiter)","([^"]+)"\);',
            webpage, 'uploader nickname', fatal=False)
        duration = int_or_none(
            self._html_search_meta('video:duration', webpage))

        age_limit = (
            18
            if re.search(r'"contentRating":"restricted"', webpage)
            else 0)

        if isinstance(video_url, list):
            formats = video_url
        else:
            formats = [{
                'url': video_url,
                'ext': video_ext,
            }]

        self._sort_formats(formats)
        return {
            'id': video_id,
            'description': description,
            'uploader': video_uploader,
            'title': video_title,
            'thumbnail': thumbnail,
            'age_limit': age_limit,
            'formats': formats,
            'duration': duration,
        }
