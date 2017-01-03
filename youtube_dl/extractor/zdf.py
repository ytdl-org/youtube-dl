# coding: utf-8
from __future__ import unicode_literals

import functools
import re

from .common import InfoExtractor
from ..utils import (
    OnDemandPagedList,
    determine_ext,
    parse_iso8601,
    ExtractorError
)
from ..compat import compat_str

class ZDFIE(InfoExtractor):
    _VALID_URL = r'https?://www\.zdf\.de/.*?/(?P<id>[^/?]*?)\.html'

    _TESTS = [{
        'url': 'https://www.zdf.de/service-und-hilfe/die-neue-zdf-mediathek/zdfmediathek-trailer-100.html',
        'info_dict': {
            'id': 'zdfmediathek-trailer-100',
            'ext': 'mp4',
            'title': 'Trailer ZDFmediathek Supermarkt',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        try:
            extr_player = ZDFExtractorPlayer(self, url, video_id)
            formats = extr_player._real_extract()
        except (ExtractorError, KeyError) as e:
            self._downloader.report_warning('%s: %s\nusing fallback method (mobile url)' % (type(e).__name__, compat_str(e)))
            extr_mobile = ZDFExtractorMobile(self, url, video_id)
            formats = extr_mobile._real_extract()
        return formats

class ZDFExtractor:
    """Super class for the 2 extraction methods"""
    def __init__(self, parent, url, video_id):
        self.parent = parent
        self.url = url
        self.video_id = video_id

    def _real_extract(self):
        formats = []
        for entry in self._fetch_entries():
            video_url = self._get_video_url(entry)
            if not video_url:
                continue
            format_id = self._get_format_id(entry)
            ext = determine_ext(video_url, None)
            if ext == 'meta':
                continue
            if ext == 'm3u8':
                formats.extend(self.parent._extract_m3u8_formats(
                    video_url, self.video_id, 'mp4', m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self.parent._extract_f4m_formats(
                    video_url, self.video_id, f4m_id=format_id, fatal=False))
            else:
                formats.append({
                    'format_id': format_id,
                    'url': video_url,
                    'format_note': self._get_format_note(entry)
                })
        self.parent._sort_formats(formats)

        return {
            'id': self.video_id,
            'title': self._get_title(),
            'formats': formats,
            'subtitles': self._get_subtitles(),
            'thumbnail': self._get_thumbnail(),
            'description': self._get_description(),
            'timestamp': self._get_timestamp()
        }

class ZDFExtractorMobile(ZDFExtractor):
    """Simple URL extraction method. Disadvantage: fewer formats, no subtitles"""
    def __init__(self, parent, url, video_id):
        ZDFExtractor.__init__(self, parent, url, video_id)

    def _fetch_entries(self):
        meta_data_url = 'https://zdf-cdn.live.cellular.de/mediathekV2/document/' + self.video_id
        self.meta_data = self.parent._download_json(meta_data_url, self.video_id, note='Downloading meta data')
        return self.meta_data['document']['formitaeten']

    def _get_title(self):
        return self.meta_data['document']['titel']

    def _get_video_url(self, entry):
        return entry['url']

    def _get_format_id(self, entry):
        format_id = entry['type']
        if 'quality' in entry:
            format_id += '-' + entry['quality']
        return format_id

    def _get_format_note(self, entry):
        return None

    def _get_subtitles(self):
        return None

    def _get_description(self):
        return self.meta_data['document'].get('beschreibung')

    def _get_timestamp(self):
        meta = self.meta_data['meta']
        if meta:
            return parse_iso8601(meta.get('editorialDate'))

    def _get_thumbnail(self):
        teaser_images = self.meta_data['document'].get('teaserBild')
        if teaser_images:
            max_res = max(teaser_images, key=int)
            return teaser_images[max_res].get('url')

class ZDFExtractorPlayer(ZDFExtractor):
    """Extraction method that requires downloads of several pages.

    Follows the requests of the website."""
    def __init__(self, parent, url, video_id):
        ZDFExtractor.__init__(self, parent, url, video_id)

    def _fetch_entries(self):
        webpage = self.parent._download_webpage(self.url, self.video_id)

        jsb = self.parent._search_regex(r"data-zdfplayer-jsb='([^']*)'", webpage, 'zdfplayer jsb data')
        jsb_json = self.parent._parse_json(jsb, self.video_id)

        configuration_url = 'https://www.zdf.de' + jsb_json['config']
        configuration_json = self.parent._download_json(configuration_url, self.video_id, note='Downloading player configuration')
        api_token = configuration_json['apiToken']

        player_js = self.parent._download_webpage('https://www.zdf.de/ZDFplayer/latest-v2/skins/zdf/zdf-player.js', self.video_id, fatal=False, note='Downloading player script')
        if player_js:
            player_id = self.parent._search_regex(r'this\.ptmd_player_id="([^"]*)"', player_js, 'player id', fatal=False)
        else:
            player_id = None

        self.content_json = self.parent._download_json(jsb_json['content'], self.video_id, headers={'Api-Auth': 'Bearer %s' % api_token}, note='Downloading content description')

        main_video_content = self.content_json['mainVideoContent']['http://zdf.de/rels/target']
        meta_data_url = None
        if not player_id:
            # could not determine player_id => try alternativ generic URL
            meta_data_url = main_video_content.get('http://zdf.de/rels/streams/ptmd')
            if meta_data_url:
                meta_data_url = 'https://api.zdf.de' + meta_data_url
            else:
                # no generic URL found => 2nd fallback: hardcoded player_id
                player_id = 'ngplayer_2_3'
        if not meta_data_url:
            meta_data_url_template = main_video_content['http://zdf.de/rels/streams/ptmd-template']
            meta_data_url = 'https://api.zdf.de' + meta_data_url_template.replace('{playerId}', player_id)

        self.meta_data = self.parent._download_json(meta_data_url, self.video_id, note='Downloading meta data')

        formats = []
        for p_list_entry in self.meta_data['priorityList']:
            for formitaet in p_list_entry['formitaeten']:
                for entry in formitaet['qualities']:
                    yield (formitaet, entry)

    def _get_title(self):
        return self.content_json['title']

    def _get_video_url(self, entry_tuple):
        (formitaet, entry) = entry_tuple
        tracks = entry['audio'].get('tracks')
        if not tracks:
            return
        if len(tracks) > 1:
            self._downloader.report_warning('unexpected input: multiple tracks')
        track = tracks[0]
        return track['uri']

    def _get_format_id(self, entry_tuple):
        (formitaet, entry) = entry_tuple
        facets = self._get_facets(formitaet)
        add = ''
        if 'adaptive' in facets:
            add += 'a'
        if 'restriction_useragent' in facets:
            add += 'b'
        if 'progressive' in facets:
            add += 'p'
        type_ = formitaet['type']
        format_id = type_ + '-'
        if add:
            format_id += add + '-'
        # named qualities are not very useful for sorting the formats:
        # a 'high' m3u8 entry can be better quality than a 'veryhigh' direct mp4 download
        format_id += entry['quality']
        return format_id

    def _get_facets(self, formitaet):
        facets = formitaet.get('facets') or []
        if formitaet.get('isAdaptive'):
            facets.append('adaptive')
        return facets

    def _get_format_note(self, entry_tuple):
        (formitaet, entry) = entry_tuple
        return ', '.join(self._get_facets(formitaet))

    def _get_subtitles(self):
        subtitles = {}
        if 'captions' in self.meta_data:
            for caption in self.meta_data['captions']:
                lang = caption.get('language')
                if not lang:
                    continue
                if lang == 'deu':
                    lang = 'de'
                subformat = {'url': caption.get('uri')}
                if caption.get('format') == 'webvtt':
                    subformat['ext'] = 'vtt'
                elif caption.get('format') == 'ebu-tt-d-basic-de':
                    subformat['ext'] = 'ttml'
                if not lang in subtitles:
                    subtitles[lang] = []
                subtitles[lang].append(subformat)
        return subtitles

    def _get_description(self):
        return self.content_json.get('teasertext')

    def _get_timestamp(self):
        return parse_iso8601(self.content_json.get('editorialDate'))

    def _get_thumbnail(self):
        teaser_images = self.content_json.get('teaserImageRef')
        if teaser_images:
            teaser_images_layouts = teaser_images.get('layouts')
            if teaser_images_layouts:
                if 'original' in teaser_images_layouts:
                    return teaser_images_layouts['original']
                teasers = {}
                for key in teaser_images_layouts:
                    width = self.parent._search_regex(r'(\d+)x\d+', key, 'teaser width', fatal=False)
                    if width:
                        teasers[int(width)] = teaser_images_layouts[key]
                if teasers:
                    best = max(teasers)
                    return teasers[best]

class ZDFChannelIE(InfoExtractor):
    _WORKING = False
    _VALID_URL = r'(?:zdf:topic:|https?://www\.zdf\.de/ZDFmediathek(?:#)?/.*kanaluebersicht/(?:[^/]+/)?)(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.zdf.de/ZDFmediathek#/kanaluebersicht/1586442/sendung/Titanic',
        'info_dict': {
            'id': '1586442',
        },
        'playlist_count': 3,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/aktuellste/332',
        'only_matching': True,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/meist-gesehen/332',
        'only_matching': True,
    }, {
        'url': 'http://www.zdf.de/ZDFmediathek/kanaluebersicht/_/1798716?bc=nrt;nrm?flash=off',
        'only_matching': True,
    }]
    _PAGE_SIZE = 50

    def _fetch_page(self, channel_id, page):
        offset = page * self._PAGE_SIZE
        xml_url = (
            'http://www.zdf.de/ZDFmediathek/xmlservice/web/aktuellste?ak=web&offset=%d&maxLength=%d&id=%s'
            % (offset, self._PAGE_SIZE, channel_id))
        doc = self._download_xml(
            xml_url, channel_id,
            note='Downloading channel info',
            errnote='Failed to download channel info')

        title = doc.find('.//information/title').text
        description = doc.find('.//information/detail').text
        for asset in doc.findall('.//teasers/teaser'):
            a_type = asset.find('./type').text
            a_id = asset.find('./details/assetId').text
            if a_type not in ('video', 'topic'):
                continue
            yield {
                '_type': 'url',
                'playlist_title': title,
                'playlist_description': description,
                'url': 'zdf:%s:%s' % (a_type, a_id),
            }

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        entries = OnDemandPagedList(
            functools.partial(self._fetch_page, channel_id), self._PAGE_SIZE)

        return {
            '_type': 'playlist',
            'id': channel_id,
            'entries': entries,
        }
