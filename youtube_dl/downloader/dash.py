from __future__ import unicode_literals

import os
import re
import math

from .fragment import FragmentFD
from ..compat import (
    compat_urllib_error,
    compat_etree_fromstring,
)
from ..utils import (
    sanitize_open,
    encodeFilename,
    xpath_with_ns,
    parse_duration,
)


class DashSegmentsFD(FragmentFD):
    """
    Download segments in a DASH manifest
    """

    FD_NAME = 'dashsegments'

    def _extract_multisegment_info(self, mpd_doc, mpd_url, representation_id):
        mobj = re.search(r'(?i)^{([^}]+)?}MPD$', mpd_doc.tag)
        namespace = mobj.group(1) if mobj else None
        ns_map = {'mpd': namespace} if namespace else {}

        def _add_ns(path):
            return xpath_with_ns(path, ns_map) if ns_map else path

        period, adaptation_set, representation = None, None, None
        found = False
        for p in mpd_doc.findall(_add_ns('mpd:Period')):
            for a in p.findall(_add_ns('mpd:AdaptationSet')):
                for r in a.findall(_add_ns('mpd:Representation')):
                    if r.get('id') == representation_id:
                        period, adaptation_set, representation = p, a, r
                        found = True
                        break
                if found:
                    break
            if found:
                break

        mpd_duration = parse_duration(mpd_doc.get('mediaPresentationDuration'))
        period_duration = parse_duration(period.get('duration')) or mpd_duration

        mpd_base_url = mpd_url.rpartition('/')[0]
        base_url = ''
        for element in (representation, adaptation_set, period, mpd_doc):
            base_url_e = element.find(_add_ns('mpd:BaseURL'))
            if base_url_e is not None:
                base_url = base_url_e.text + base_url
                if re.match(r'^https?://', base_url):
                    break
        if mpd_base_url and not re.match(r'^https?://', base_url):
            if not mpd_base_url.endswith('/') and not base_url.startswith('/'):
                mpd_base_url += '/'
            base_url = mpd_base_url + base_url

        ms_info = {
            'base_url': base_url,
            'start_number': 1,
            'timescale': 1,
        }

        for element in (period, adaptation_set, representation):
            segment_list = element.find(_add_ns('mpd:SegmentList'))
            if segment_list is not None:
                segment_urls_e = segment_list.findall(_add_ns('mpd:SegmentURL'))
                if segment_urls_e:
                    ms_info['segment_urls'] = [segment.attrib['media'] for segment in segment_urls_e]
                initialization = segment_list.find(_add_ns('mpd:Initialization'))
                if initialization is not None:
                    ms_info['initialization_url'] = initialization.attrib['sourceURL']
            else:
                segment_template = element.find(_add_ns('mpd:SegmentTemplate'))
                if segment_template is not None:
                    start_number = segment_template.get('startNumber')
                    if start_number:
                        ms_info['start_number'] = int(start_number)
                    timescale = segment_template.get('timescale')
                    if timescale:
                        ms_info['timescale'] = int(timescale)
                    segment_timeline = segment_template.find(_add_ns('mpd:SegmentTimeline'))
                    if segment_timeline is not None:
                        s_e = segment_timeline.findall(_add_ns('mpd:S'))
                        if s_e:
                            current_start_time = 0
                            ms_info['segment_start_times'] = []
                            for s in s_e:
                                for i in int(s.get('r', '0')) + 1:
                                    ms_info['segment_start_times'].append(current_start_time)
                                    current_start_time += int(s['d']) / ms_info['timescale']
                    else:
                        segment_duration = segment_template.get('duration')
                        if segment_duration:
                            ms_info['segment_duration'] = int(segment_duration)
                    media_template = segment_template.get('media')
                    if media_template:
                        ms_info['media_template'] = media_template
                    initialization = segment_template.get('initialization')
                    if initialization:
                        ms_info['initialization_url'] = initialization
                    else:
                        initialization = segment_template.find(_add_ns('mpd:Initialization'))
                        if initialization is not None:
                            ms_info['initialization_url'] = initialization.attrib['sourceURL']

        if 'segment_urls' not in ms_info and 'media_template' in ms_info:
            if 'segment_start_times' not in ms_info and 'segment_duration':
                segment_duration = float(ms_info['segment_duration']) / float(ms_info['timescale'])
                ms_info['segment_start_times'] = [i * segment_duration for i in range(
                    int(math.ceil(float(period_duration) / segment_duration)))]
            media_template = ms_info['media_template']
            media_template = media_template.replace('$RepresentationID$', representation_id)
            media_template = re.sub(r'\$(Time|Number|Bandwidth)\$', r'%(\1)d', media_template)
            media_template = re.sub(r'\$(Time|Number|Bandwidth)%(\d+)d\$', r'%(\1)\2d', media_template)
            media_template.replace('$$', '$')
            ms_info['segment_urls'] = [
                media_template % {
                    'Number': segment_number,
                    'Bandwidth': representation.attrib.get('bandwidth'),
                    'Time': segement_start_time,
                } for segment_number, segement_start_time in enumerate(
                    ms_info['segment_start_times'],
                    ms_info['start_number'])]
        return ms_info

    def real_download(self, filename, info_dict):
        mpd_url = info_dict['url']
        params = info_dict['_downloader_params']
        mpd_doc = params.get('mpd')
        is_live = mpd_doc is None
        if is_live:
            self.to_screen('[%s] Downloading MPD manifest' % self.FD_NAME)
            urlh = self.ydl.urlopen(mpd_url)
            mpd_url = urlh.geturl()
            mpd_doc = compat_etree_fromstring(urlh.read().decode('utf-8'))

        representation_id = params.get('representation_id')
        ms_info = self._extract_multisegment_info(mpd_doc, mpd_url, representation_id)
        segment_urls = [ms_info['segment_urls'][0]] if self.params.get('test', False) else ms_info['segment_urls']
        initialization_url = ms_info.get('initialization_url')
        base_url = ms_info.get('base_url')

        ctx = {
            'filename': filename,
            'total_frags': len(segment_urls) + (1 if initialization_url else 0),
        }

        self._prepare_and_start_frag_download(ctx)

        def combine_url(base_url, target_url):
            if re.match(r'^https?://', target_url):
                return target_url
            return '%s%s%s' % (base_url, '' if base_url.endswith('/') else '/', target_url)

        segments_filenames = []

        fragment_retries = self.params.get('fragment_retries', 0)

        def append_url_to_file(target_url, tmp_filename, segment_name):
            target_filename = '%s-%s' % (tmp_filename, segment_name)
            count = 0
            while count <= fragment_retries:
                try:
                    success = ctx['dl'].download(target_filename, {'url': combine_url(base_url, target_url)})
                    if not success:
                        return False
                    down, target_sanitized = sanitize_open(target_filename, 'rb')
                    ctx['dest_stream'].write(down.read())
                    down.close()
                    segments_filenames.append(target_sanitized)
                    break
                except (compat_urllib_error.HTTPError, ) as err:
                    # YouTube may often return 404 HTTP error for a fragment causing the
                    # whole download to fail. However if the same fragment is immediately
                    # retried with the same request data this usually succeeds (1-2 attemps
                    # is usually enough) thus allowing to download the whole file successfully.
                    # So, we will retry all fragments that fail with 404 HTTP error for now.
                    if err.code != 404:
                        raise
                    # Retry fragment
                    count += 1
                    if count <= fragment_retries:
                        self.report_retry_fragment(segment_name, count, fragment_retries)
            if count > fragment_retries:
                self.report_error('giving up after %s fragment retries' % fragment_retries)
                return False

        if initialization_url:
            append_url_to_file(initialization_url, ctx['tmpfilename'], 'Init')
        for i, segment_url in enumerate(segment_urls):
            append_url_to_file(segment_url, ctx['tmpfilename'], 'Seg%d' % i)

        self._finish_frag_download(ctx)

        for segment_file in segments_filenames:
            os.remove(encodeFilename(segment_file))

        return True
