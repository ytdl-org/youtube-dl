from __future__ import unicode_literals

import itertools
import re
import time
import xml.etree.ElementTree as etree

from .common import FileDownloader
from ..compat import (
    compat_str,
    compat_urllib_request,
)
from ..utils import (
    parse_iso8601,
    xpath_with_ns,
)


class DashSegmentsFD(FileDownloader):
    """
    Download segments in a DASH manifest
    """
    def real_download(self, filename, info_dict):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        is_test = self.params.get('test', False)
        remaining_bytes = self._TEST_FILE_SIZE if is_test else None
        byte_counter = 0

        def append_url_to_file(outf, target_url, target_name, remaining_bytes=None):
            self.to_screen('[DashSegments] %s: Downloading %s' % (info_dict['id'], target_name))
            req = compat_urllib_request.Request(target_url)
            if remaining_bytes is not None:
                req.add_header('Range', 'bytes=0-%d' % (remaining_bytes - 1))

            data = self.ydl.urlopen(req).read()

            if remaining_bytes is not None:
                data = data[:remaining_bytes]

            outf.write(data)
            return len(data)

        if not info_dict.get('is_live'):
            base_url = info_dict['url']
            segment_urls = info_dict['segment_urls']

            def combine_url(base_url, target_url):
                if re.match(r'^https?://', target_url):
                    return target_url
                return '%s/%s' % (base_url, target_url)

            init_url = combine_url(base_url, info_dict['initialization_url'])
            segment_urls = [combine_url(base_url, segment_url) for segment_url in segment_urls]

        else:
            manifest_url = info_dict['url']
            manifest_xml = self.ydl.urlopen(manifest_url).read()
            manifest = etree.fromstring(manifest_xml)
            _x = lambda p: xpath_with_ns(p, {'ns': 'urn:mpeg:DASH:schema:MPD:2011'})
            ad = [e for e in manifest.findall(_x('ns:Period/ns:AdaptationSet')) if e.attrib['id'] == info_dict['mpd_set_id']][0]
            segment_template = ad.find(_x('ns:SegmentTemplate'))

            def subs_url_template(url_template, repr_id, number=None):
                result = url_template.replace('$RepresentationID$', repr_id)
                if number is not None:
                    result = result.replace('$Number$', compat_str(number))
                return result

            start_time = parse_iso8601(manifest.attrib['availabilityStartTime'])
            segment_duration = (int(segment_template.attrib['duration']) / int(segment_template.attrib['timescale']))  # in seconds
            first_segment = int((int(time.time()) - start_time) / segment_duration)
            init_url = subs_url_template(segment_template.attrib['initialization'], '1')

            def build_live_segment_urls():
                for nr in itertools.count(first_segment):
                    # We have to avoid requesting a segment before its start time
                    expected_time = start_time + nr * segment_duration
                    wait_time = expected_time - time.time()
                    if wait_time > 0:
                        time.sleep(wait_time)
                    yield subs_url_template(segment_template.attrib['media'], '1', nr)
            segment_urls = build_live_segment_urls()

        with open(tmpfilename, 'wb') as outf:
            append_url_to_file(
                outf, init_url,
                'initialization segment')
            for i, segment_url in enumerate(segment_urls):
                note = 'segment %d' % (i + 1)
                if not info_dict.get('is_live'):
                    note += ' / %d' % len(segment_urls)
                segment_len = append_url_to_file(
                    outf, segment_url, note, remaining_bytes)
                byte_counter += segment_len
                self._hook_progress({
                    'status': 'downloading',
                    'downloaded_bytes': byte_counter,
                    'filename': filename,
                })
                if remaining_bytes is not None:
                    remaining_bytes -= segment_len
                    if remaining_bytes <= 0:
                        break

        self.try_rename(tmpfilename, filename)

        self._hook_progress({
            'downloaded_bytes': byte_counter,
            'total_bytes': byte_counter,
            'filename': filename,
            'status': 'finished',
        })

        return True
