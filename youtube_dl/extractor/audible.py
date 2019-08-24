# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    clean_html,
    clean_html_markdown,
    ExtractorError,
    extract_attributes,
    get_element_by_class,
    get_element_by_id,
    get_elements_by_class,
    unified_strdate,
    urlencode_postdata,
)


class AudibleBaseIE(InfoExtractor):
    _BASE_URL = 'https://www.audible.com'

    def _is_logged_in(self, html=None):
        if not html:
            html = self._download_webpage(
                self._BASE_URL, None,
                'Checking login status')

        logged_in_elm = get_element_by_class('ui-it-credit-balance', html)

        if logged_in_elm is None:
            self.report_warning(
                'You don\'t appear to be logged in.  You will not be able to '
                'download full audiobooks without being logged in.  It is '
                'currently not possible to automate the login process for '
                'Audible.  You must login via a browser, then export your '
                'cookies and pass the cookie file to youtube-dl with '
                '--cookies.')
            return False

        else:
            return True


class AudibleIE(AudibleBaseIE):
    IE_NAME = 'audible'
    _VALID_URL = r'https?://(?:.+?\.)?audible\.com/pd/(?:.+)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.audible.com/pd/Neil-Gaimans-How-the-Marquis-Got-His-Coat-Back-Audiobook/B01LZB4R8W',
        'md5': '7bcfd4aab323cee607d8425c9aba275b',
        'info_dict': {
            'id': 'B01LZB4R8W',
            'ext': 'mp3',
            'title': 'Neil Gaiman\'s How the Marquis Got His Coat Back',
            'description': 'md5:851082468b157f20c82caf10051c5a24',
            'thumbnail': 're:^https?://.*\.jpg$',
            'creator': 'Neil Gaiman',
            'album_artist': 'Neil Gaiman',
            'artist': 'Paterson Joseph, Bernard Cribbins, Samantha Beart, Adrian Lester, Mitch Benn, Don Warrington',
        },
        'expected_warnings': ['You don\'t appear to be logged in.']
    }, {
        'url': 'https://www.audible.com/pd/Merrick-Audiobook/B002UUKMKQ',
        'md5': '3bcbc2ed79201332db8d72b4c95a0269',
        'info_dict': {
            'id': 'B002UUKMKQ',
            'ext': 'mp3',
            'title': 'Merrick',
            'description': 'md5:82c8d4687e361ebb70162039288dcba2',
            'thumbnail': 're:^https?://.*\.jpg$',
            'creator': 'Anne Rice',
            'album_artist': 'Anne Rice',
            'artist': 'Graeme Malcolm',
            'series': 'The Vampire Chronicles',
            'album': 'The Vampire Chronicles',
            'episode_number': 7,
            'track_number': 7,
            'episode_id': 'Book 7',
        },
        'expected_warnings': ['You don\'t appear to be logged in.']
    }]

    @staticmethod
    def _get_label_text(class_name, html, prefix=None):
        label_text = None

        label_html = get_element_by_class(class_name, html)
        if label_html:
            label_text = re.sub(r'\s+', ' ', clean_html(label_html))
            if prefix and label_text.startswith(prefix):
                label_text = label_text[len(prefix):].strip()

        return label_text

    def _real_extract(self, url):
        book_id = self._match_id(url)
        webpage = self._download_webpage(url, book_id)

        title = self._og_search_title(webpage)

        thumbnails = []
        og_thumbnail = self._og_search_thumbnail(webpage)
        if og_thumbnail:
            thumbnails.append({
                'url': og_thumbnail,
                'preference': 210
            })
        thumb_element = self._search_regex(
            r'(<img[^>]+alt=["\'][^\'"]*\bcover art\b[^>]*>)', webpage,
            'thumbnail element', default=None)
        if thumb_element:
            lg_thumbnail_attrs = extract_attributes(thumb_element)
            if lg_thumbnail_attrs.get('src'):
                thumbnails.append({
                    'url': lg_thumbnail_attrs.get('src'),
                    'preference': 500
                })

        authors = self._get_label_text('authorLabel', webpage, prefix='By:')
        narrators = self._get_label_text('narratorLabel', webpage, prefix='Narrated by:')
        performance_type = self._get_label_text('format', webpage)
        publisher = self._get_label_text('publisherLabel', webpage, prefix='Publisher:')

        release_date_yyyymmdd = None
        release_date = self._get_label_text('releaseDateLabel', webpage, prefix='Release date:')
        if release_date:
            release_date_yyyymmdd = unified_strdate(release_date, False)

        book_series = None
        book_in_series = None
        book_number = None
        in_multiple_series = False
        all_series = self._get_label_text('seriesLabel', webpage, prefix='Series:')
        if all_series:
            series_sep = all_series.split(',')
            book_series = series_sep[0].strip()
            if len(series_sep) > 1:
                book_in_series = series_sep[1].strip()
                if book_in_series.startswith('Book'):
                    book_number = float(book_in_series[4:].strip())
                if len(series_sep) > 2 and len(series_sep) % 2 == 0:
                    in_multiple_series = True

        categories = []
        breadcrumbs_text = get_elements_by_class('navigation-link', webpage)
        if breadcrumbs_text:
            categories.extend(breadcrumbs_text)

        description = ""
        # Not all summaries show up on a given book, but the publisher summary
        # is the most common
        editorial_summary_html = get_element_by_class('productEditorialSummary', webpage)
        if editorial_summary_html:
            editorial_summary_text = clean_html_markdown(editorial_summary_html)
            description += editorial_summary_text + '\n\n'
        publisher_summary_html = get_element_by_class('productPublisherSummary', webpage)
        if publisher_summary_html:
            publisher_summary_text = clean_html_markdown(publisher_summary_html)
            description += publisher_summary_text + '\n\n'
        critics_summary_html = get_element_by_class('productCriticsSummary', webpage)
        if critics_summary_html:
            critics_summary_text = clean_html_markdown(critics_summary_html)
            description += critics_summary_text + '\n\n'
        if in_multiple_series:
            series_list_text = '## Series List\n\n'
            for sidx in range(0, len(series_sep), 2):
                series_list_text += '- %s, %s\n' % (
                    series_sep[sidx].strip(),
                    series_sep[sidx + 1].strip())
            description += series_list_text + '\n'

        # Audio Sample
        formats = []
        sample_audio = self._search_regex(
            r'\s+data-mp3=(["\'])(?P<url>.+?)\1', webpage,
            'Audio Sample', default=None, group='url')
        sample_format = {
            'url': sample_audio,
            'format_id': 'sample',
            'format': 'sample - audio only',
            'vcodec': 'none',
        }
        formats.append(sample_format)

        is_logged_in = self._is_logged_in(webpage)
        book_purchased = False
        purchase_date_elm = get_element_by_id('adbl-buy-box-purchase-date', webpage)
        if purchase_date_elm is not None:
            book_purchased = True

        if is_logged_in and not book_purchased:
            self.report_warning(
                'You don\'t appear to own this title.',
                book_id)

        duration = None
        chapters = []
        if is_logged_in and book_purchased:
            cloud_player_url = 'https://www.audible.com/cloudplayer?asin=' + book_id
            cloud_player_page = self._download_webpage(
                cloud_player_url, book_id, 'Retrieving token')
            cloud_player_form = self._hidden_inputs(cloud_player_page)

            token = cloud_player_form.get('token')
            if token is None:
                raise ExtractorError("Could not find token")

            metadata = self._download_json(
                'https://www.audible.com/contentlicenseajax', book_id,
                data=urlencode_postdata({
                    'asin': book_id,
                    'token': token,
                    'key': 'AudibleCloudPlayer',
                    'action': 'getUrl'
                }),
                headers={'Referer': cloud_player_url})

            m3u8_url = metadata.get('hlscontentLicenseUrl')
            if m3u8_url:
                m3u8_formats = self._extract_akamai_formats(
                    m3u8_url, book_id, skip_protocols=['f4m'])
                formats.extend(m3u8_formats)
            self._sort_formats(formats)

            duration = metadata.get('runTime')

            for md_chapter in metadata.get('cloudPlayerChapters', []):
                ch_start_time = md_chapter.get('chapterStartPosition')
                ch_end_time = md_chapter.get('chapterEndPosition')
                ch_title = md_chapter.get('chapterTitle')

                if ch_start_time is None or ch_end_time is None:
                    self.report_warning('Missing chapter information')
                    chapters = []
                    break

                chapter = {
                    'start_time': float(ch_start_time) / 1000,
                    'end_time': float(ch_end_time) / 1000
                }

                if ch_title:
                    chapter['title'] = ch_title

                chapters.append(chapter)

        return {
            'id': book_id,
            'title': title,
            'formats': formats,
            'duration': duration,
            'chapters': chapters if len(chapters) > 0 else None,
            'thumbnails': thumbnails if len(thumbnails) > 0 else None,
            'creator': authors,
            'album_artist': authors,
            'artist': narrators,
            'album_type': performance_type,
            'uploader': publisher,
            'release_date': release_date_yyyymmdd,
            'release_year': int(release_date_yyyymmdd[:4]) if release_date_yyyymmdd else None,
            'series': book_series,
            'album': book_series,
            'episode_number': book_number,
            'track_number': book_number,
            'episode_id': book_in_series,
            'categories': categories if len(categories) > 0 else None,
            'genre': ', '.join(categories) if len(categories) > 0 else None,
            'description': description if description is not "" else None,
        }


class AudibleLibraryIE(AudibleBaseIE):
    IE_NAME = 'audible:library'
    _VALID_URL = r'https?://(?:.+?\.)?audible\.com/lib\b'

    def _real_initialize(self):
        if not self._is_logged_in():
            raise ExtractorError('Not logged in.', expected=True)

    def _real_extract(self, url):
        entries = []

        last_page = None
        page_num = 0
        while True:
            page_num += 1
            page_id = "Page%d" % page_num

            # update url to current page number
            parsed_url = compat_urlparse.urlparse(url)
            qs = compat_urlparse.parse_qs(parsed_url.query)
            qs['page'] = page_num
            page_url = compat_urlparse.urlunparse(
                parsed_url._replace(query=compat_urllib_parse_urlencode(qs, True)))

            webpage = self._download_webpage(page_url, page_id)

            for book_link in re.findall(r'(<a[^>]+aria-describedby=["\']product-list-flyout-[^"\'][^>]*>)', webpage):
                book_link_attrs = extract_attributes(book_link)
                if book_link_attrs.get('href'):
                    entries.append(self.url_result(
                        self._BASE_URL + book_link_attrs.get('href'),
                        ie=AudibleIE.ie_key()))

            if last_page is None:
                pages = get_elements_by_class('pageNumberElement', webpage)
                if pages:
                    last_page = int(pages[-1])

            if page_num >= last_page:
                break

        return self.playlist_result(entries)
