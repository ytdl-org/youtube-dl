from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError

class Channel9IE(InfoExtractor):
    '''
    Common extractor for channel9.msdn.com.

    The type of provided URL (video or playlist) is determined according to
    meta Search.PageType from web page HTML rather than URL itself, as it is
    not always possible to do.
    '''
    IE_DESC = 'Channel 9'
    IE_NAME = 'channel9'
    _VALID_URL = r'https?://(?:www\.)?channel9\.msdn\.com/(?P<contentpath>.+)/?'

    _TESTS = [
        {
            'url': 'http://channel9.msdn.com/Events/TechEd/Australia/2013/KOS002',
            'md5': 'bbd75296ba47916b754e73c3a4bbdf10',
            'info_dict': {
                'id': 'Events/TechEd/Australia/2013/KOS002',
                'ext': 'mp4',
                'title': 'Developer Kick-Off Session: Stuff We Love',
                'description': 'md5:c08d72240b7c87fcecafe2692f80e35f',
                'duration': 4576,
                'thumbnail': 'http://media.ch9.ms/ch9/9d51/03902f2d-fc97-4d3c-b195-0bfe15a19d51/KOS002_220.jpg',
                'session_code': 'KOS002',
                'session_day': 'Day 1',
                'session_room': 'Arena 1A',
                'session_speakers': [ 'Ed Blankenship', 'Andrew Coates', 'Brady Gaster', 'Patrick Klug', 'Mads Kristensen' ],
            },
        },
        {
            'url': 'http://channel9.msdn.com/posts/Self-service-BI-with-Power-BI-nuclear-testing',
            'md5': 'b43ee4529d111bc37ba7ee4f34813e68',
            'info_dict': {
                'id': 'posts/Self-service-BI-with-Power-BI-nuclear-testing',
                'ext': 'mp4',
                'title': 'Self-service BI with Power BI - nuclear testing',
                'description': 'md5:d1e6ecaafa7fb52a2cacdf9599829f5b',
                'duration': 1540,
                'thumbnail': 'http://media.ch9.ms/ch9/87e1/0300391f-a455-4c72-bec3-4422f19287e1/selfservicenuk_512.jpg',
                'authors': [ 'Mike Wilmot' ],
            },
        }
    ]

    _RSS_URL = 'http://channel9.msdn.com/%s/RSS'

    # Sorted by quality
    _known_formats = ['MP3', 'MP4', 'Mid Quality WMV', 'Mid Quality MP4', 'High Quality WMV', 'High Quality MP4']

    def _restore_bytes(self, formatted_size):
        if not formatted_size:
            return 0
        m = re.match(r'^(?P<size>\d+(?:\.\d+)?)\s+(?P<units>[a-zA-Z]+)', formatted_size)
        if not m:
            return 0
        units = m.group('units')
        try:
            exponent = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'].index(units.upper())
        except ValueError:
            return 0
        size = float(m.group('size'))
        return int(size * (1024 ** exponent))

    def _formats_from_html(self, html):
        FORMAT_REGEX = r'''
            (?x)
            <a\s+href="(?P<url>[^"]+)">(?P<quality>[^<]+)</a>\s*
            <span\s+class="usage">\((?P<note>[^\)]+)\)</span>\s*
            (?:<div\s+class="popup\s+rounded">\s*
            <h3>File\s+size</h3>\s*(?P<filesize>.*?)\s*
            </div>)?                                                # File size part may be missing
        '''
        # Extract known formats
        formats = [{
            'url': x.group('url'),
            'format_id': x.group('quality'),
            'format_note': x.group('note'),
            'format': '%s (%s)' % (x.group('quality'), x.group('note')),
            'filesize': self._restore_bytes(x.group('filesize')), # File size is approximate
            'preference': self._known_formats.index(x.group('quality')),
            'vcodec': 'none' if x.group('note') == 'Audio only' else None,
        } for x in list(re.finditer(FORMAT_REGEX, html)) if x.group('quality') in self._known_formats]

        self._sort_formats(formats)

        return formats

    def _extract_title(self, html):
        title = self._html_search_meta('title', html, 'title')
        if title is None:           
            title = self._og_search_title(html)
            TITLE_SUFFIX = ' (Channel 9)'
            if title is not None and title.endswith(TITLE_SUFFIX):
                title = title[:-len(TITLE_SUFFIX)]
        return title

    def _extract_description(self, html):
        DESCRIPTION_REGEX = r'''(?sx)
            <div\s+class="entry-content">\s*
            <div\s+id="entry-body">\s*
            (?P<description>.+?)\s*
            </div>\s*
            </div>
        '''
        m = re.search(DESCRIPTION_REGEX, html)
        if m is not None:
            return m.group('description')
        return self._html_search_meta('description', html, 'description')

    def _extract_duration(self, html):
        m = re.search(r'data-video_duration="(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})"', html)
        return ((int(m.group('hours')) * 60 * 60) + (int(m.group('minutes')) * 60) + int(m.group('seconds'))) if m else None

    def _extract_slides(self, html):
        m = re.search(r'<a href="(?P<slidesurl>[^"]+)" class="slides">Slides</a>', html)
        return m.group('slidesurl') if m is not None else None

    def _extract_zip(self, html):
        m = re.search(r'<a href="(?P<zipurl>[^"]+)" class="zip">Zip</a>', html)
        return m.group('zipurl') if m is not None else None

    def _extract_avg_rating(self, html):
        m = re.search(r'<p class="avg-rating">Avg Rating: <span>(?P<avgrating>[^<]+)</span></p>', html)
        return float(m.group('avgrating')) if m is not None else 0

    def _extract_rating_count(self, html):
        m = re.search(r'<div class="rating-count">\((?P<ratingcount>[^<]+)\)</div>', html)
        return int(self._fix_count(m.group('ratingcount'))) if m is not None else 0

    def _extract_view_count(self, html):
        m = re.search(r'<li class="views">\s*<span class="count">(?P<viewcount>[^<]+)</span> Views\s*</li>', html)
        return int(self._fix_count(m.group('viewcount'))) if m is not None else 0

    def _extract_comment_count(self, html):
        m = re.search(r'<li class="comments">\s*<a href="#comments">\s*<span class="count">(?P<commentcount>[^<]+)</span> Comments\s*</a>\s*</li>', html)
        return int(self._fix_count(m.group('commentcount'))) if m is not None else 0

    def _fix_count(self, count):
        return int(str(count).replace(',', '')) if count is not None else None

    def _extract_authors(self, html):
        m = re.search(r'(?s)<li class="author">(.*?)</li>', html)
        if m is None:
            return None
        return re.findall(r'<a href="/Niners/[^"]+">([^<]+)</a>', m.group(1))

    def _extract_session_code(self, html):
        m = re.search(r'<li class="code">\s*(?P<code>.+?)\s*</li>', html)
        return m.group('code') if m is not None else None

    def _extract_session_day(self, html):
        m = re.search(r'<li class="day">\s*<a href="/Events/[^"]+">(?P<day>[^<]+)</a>\s*</li>', html)
        return m.group('day') if m is not None else None

    def _extract_session_room(self, html):
        m = re.search(r'<li class="room">\s*(?P<room>.+?)\s*</li>', html)
        return m.group('room') if m is not None else None

    def _extract_session_speakers(self, html):
        return re.findall(r'<a href="/Events/Speakers/[^"]+">([^<]+)</a>', html)

    def _extract_content(self, html, content_path):
        # Look for downloadable content        
        formats = self._formats_from_html(html)
        slides = self._extract_slides(html)
        zip_ = self._extract_zip(html)

        # Nothing to download
        if len(formats) == 0 and slides is None and zip_ is None:
            self._downloader.report_warning('None of recording, slides or zip are available for %s' % content_path)
            return

        # Extract meta
        title = self._extract_title(html)
        description = self._extract_description(html)
        thumbnail = self._og_search_thumbnail(html)
        duration = self._extract_duration(html)
        avg_rating = self._extract_avg_rating(html)
        rating_count = self._extract_rating_count(html)
        view_count = self._extract_view_count(html)
        comment_count = self._extract_comment_count(html)

        common = {'_type': 'video',
                  'id': content_path,
                  'description': description,
                  'thumbnail': thumbnail,
                  'duration': duration,
                  'avg_rating': avg_rating,
                  'rating_count': rating_count,
                  'view_count': view_count,
                  'comment_count': comment_count,
                }

        result = []

        if slides is not None:
            d = common.copy()
            d.update({ 'title': title + '-Slides', 'url': slides })
            result.append(d)

        if zip_ is not None:
            d = common.copy()
            d.update({ 'title': title + '-Zip', 'url': zip_ })
            result.append(d)

        if len(formats) > 0:
            d = common.copy()
            d.update({ 'title': title, 'formats': formats })
            result.append(d)

        return result

    def _extract_entry_item(self, html, content_path):
        contents = self._extract_content(html, content_path)
        if contents is None:
            return contents

        authors = self._extract_authors(html)

        for content in contents:
            content['authors'] = authors

        return contents

    def _extract_session(self, html, content_path):
        contents = self._extract_content(html, content_path)
        if contents is None:
            return contents

        session_meta = {'session_code': self._extract_session_code(html),
                        'session_day': self._extract_session_day(html),
                        'session_room': self._extract_session_room(html),
                        'session_speakers': self._extract_session_speakers(html),
                        }

        for content in contents:
            content.update(session_meta)

        return contents

    def _extract_list(self, content_path):
        rss = self._download_xml(self._RSS_URL % content_path, content_path, 'Downloading RSS')
        entries = [self.url_result(session_url.text, 'Channel9')
                   for session_url in rss.findall('./channel/item/link')]
        title_text = rss.find('./channel/title').text
        return self.playlist_result(entries, content_path, title_text)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        content_path = mobj.group('contentpath')

        webpage = self._download_webpage(url, content_path, 'Downloading web page')

        page_type_m = re.search(r'<meta name="Search.PageType" content="(?P<pagetype>[^"]+)"/>', webpage)
        if page_type_m is None:
            raise ExtractorError('Search.PageType not found, don\'t know how to process this page', expected=True)

        page_type = page_type_m.group('pagetype')
        if page_type == 'List':         # List page, may contain list of 'item'-like objects
            return self._extract_list(content_path)
        elif page_type == 'Entry.Item': # Any 'item'-like page, may contain downloadable content
            return self._extract_entry_item(webpage, content_path)
        elif page_type == 'Session':    # Event session page, may contain downloadable content
            return self._extract_session(webpage, content_path)
        else:
            raise ExtractorError('Unexpected Search.PageType %s' % page_type, expected=True)