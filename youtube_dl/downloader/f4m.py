from __future__ import unicode_literals

import base64
import io
import itertools
import os
import time
import xml.etree.ElementTree as etree

from .common import FileDownloader
from .http import HttpFD
from ..utils import (
    struct_pack,
    struct_unpack,
    compat_urlparse,
    format_bytes,
    encodeFilename,
    sanitize_open,
)


class FlvReader(io.BytesIO):
    """
    Reader for Flv files
    The file format is documented in https://www.adobe.com/devnet/f4v.html
    """

    # Utility functions for reading numbers and strings
    def read_unsigned_long_long(self):
        return struct_unpack('!Q', self.read(8))[0]

    def read_unsigned_int(self):
        return struct_unpack('!I', self.read(4))[0]

    def read_unsigned_char(self):
        return struct_unpack('!B', self.read(1))[0]

    def read_string(self):
        res = b''
        while True:
            char = self.read(1)
            if char == b'\x00':
                break
            res += char
        return res

    def read_box_info(self):
        """
        Read a box and return the info as a tuple: (box_size, box_type, box_data)
        """
        real_size = size = self.read_unsigned_int()
        box_type = self.read(4)
        header_end = 8
        if size == 1:
            real_size = self.read_unsigned_long_long()
            header_end = 16
        return real_size, box_type, self.read(real_size-header_end)

    def read_asrt(self):
        # version
        self.read_unsigned_char()
        # flags
        self.read(3)
        quality_entry_count = self.read_unsigned_char()
        # QualityEntryCount
        for i in range(quality_entry_count):
            self.read_string()

        segment_run_count = self.read_unsigned_int()
        segments = []
        for i in range(segment_run_count):
            first_segment = self.read_unsigned_int()
            fragments_per_segment = self.read_unsigned_int()
            segments.append((first_segment, fragments_per_segment))

        return {
            'segment_run': segments,
        }

    def read_afrt(self):
        # version
        self.read_unsigned_char()
        # flags
        self.read(3)
        # time scale
        self.read_unsigned_int()

        quality_entry_count = self.read_unsigned_char()
        # QualitySegmentUrlModifiers
        for i in range(quality_entry_count):
            self.read_string()

        fragments_count = self.read_unsigned_int()
        fragments = []
        for i in range(fragments_count):
            first = self.read_unsigned_int()
            first_ts = self.read_unsigned_long_long()
            duration = self.read_unsigned_int()
            if duration == 0:
                discontinuity_indicator = self.read_unsigned_char()
            else:
                discontinuity_indicator = None
            fragments.append({
                'first': first,
                'ts': first_ts,
                'duration': duration,
                'discontinuity_indicator': discontinuity_indicator,
            })

        return {
            'fragments': fragments,
        }

    def read_abst(self):
        # version
        self.read_unsigned_char()
        # flags
        self.read(3)

        self.read_unsigned_int()  # BootstrapinfoVersion
        # Profile,Live,Update,Reserved
        self.read(1)
        # time scale
        self.read_unsigned_int()
        # CurrentMediaTime
        self.read_unsigned_long_long()
        # SmpteTimeCodeOffset
        self.read_unsigned_long_long()

        self.read_string()  # MovieIdentifier
        server_count = self.read_unsigned_char()
        # ServerEntryTable
        for i in range(server_count):
            self.read_string()
        quality_count = self.read_unsigned_char()
        # QualityEntryTable
        for i in range(quality_count):
            self.read_string()
        # DrmData
        self.read_string()
        # MetaData
        self.read_string()

        segments_count = self.read_unsigned_char()
        segments = []
        for i in range(segments_count):
            box_size, box_type, box_data = self.read_box_info()
            assert box_type == b'asrt'
            segment = FlvReader(box_data).read_asrt()
            segments.append(segment)
        fragments_run_count = self.read_unsigned_char()
        fragments = []
        for i in range(fragments_run_count):
            box_size, box_type, box_data = self.read_box_info()
            assert box_type == b'afrt'
            fragments.append(FlvReader(box_data).read_afrt())

        return {
            'segments': segments,
            'fragments': fragments,
        }

    def read_bootstrap_info(self):
        total_size, box_type, box_data = self.read_box_info()
        assert box_type == b'abst'
        return FlvReader(box_data).read_abst()


def read_bootstrap_info(bootstrap_bytes):
    return FlvReader(bootstrap_bytes).read_bootstrap_info()


def build_fragments_list(boot_info):
    """ Return a list of (segment, fragment) for each fragment in the video """
    res = []
    segment_run_table = boot_info['segments'][0]
    # I've only found videos with one segment
    segment_run_entry = segment_run_table['segment_run'][0]
    n_frags = segment_run_entry[1]
    fragment_run_entry_table = boot_info['fragments'][0]['fragments']
    first_frag_number = fragment_run_entry_table[0]['first']
    for (i, frag_number) in zip(range(1, n_frags+1), itertools.count(first_frag_number)):
        res.append((1, frag_number))
    return res


def write_flv_header(stream, metadata):
    """Writes the FLV header and the metadata to stream"""
    # FLV header
    stream.write(b'FLV\x01')
    stream.write(b'\x05')
    stream.write(b'\x00\x00\x00\x09')
    # FLV File body
    stream.write(b'\x00\x00\x00\x00')
    # FLVTAG
    # Script data
    stream.write(b'\x12')
    # Size of the metadata with 3 bytes
    stream.write(struct_pack('!L', len(metadata))[1:])
    stream.write(b'\x00\x00\x00\x00\x00\x00\x00')
    stream.write(metadata)
    # Magic numbers extracted from the output files produced by AdobeHDS.php
    #(https://github.com/K-S-V/Scripts)
    stream.write(b'\x00\x00\x01\x73')


def _add_ns(prop):
    return '{http://ns.adobe.com/f4m/1.0}%s' % prop


class HttpQuietDownloader(HttpFD):
    def to_screen(self, *args, **kargs):
        pass


class F4mFD(FileDownloader):
    """
    A downloader for f4m manifests or AdobeHDS.
    """

    def real_download(self, filename, info_dict):
        man_url = info_dict['url']
        self.to_screen('[download] Downloading f4m manifest')
        manifest = self.ydl.urlopen(man_url).read()
        self.report_destination(filename)
        http_dl = HttpQuietDownloader(self.ydl,
            {
                'continuedl': True,
                'quiet': True,
                'noprogress': True,
                'test': self.params.get('test', False),
            })

        doc = etree.fromstring(manifest)
        formats = [(int(f.attrib.get('bitrate', -1)), f) for f in doc.findall(_add_ns('media'))]
        formats = sorted(formats, key=lambda f: f[0])
        rate, media = formats[-1]
        base_url = compat_urlparse.urljoin(man_url, media.attrib['url'])
        bootstrap = base64.b64decode(doc.find(_add_ns('bootstrapInfo')).text)
        metadata = base64.b64decode(media.find(_add_ns('metadata')).text)
        boot_info = read_bootstrap_info(bootstrap)
        fragments_list = build_fragments_list(boot_info)
        if self.params.get('test', False):
            # We only download the first fragment
            fragments_list = fragments_list[:1]
        total_frags = len(fragments_list)

        tmpfilename = self.temp_name(filename)
        (dest_stream, tmpfilename) = sanitize_open(tmpfilename, 'wb')
        write_flv_header(dest_stream, metadata)

        # This dict stores the download progress, it's updated by the progress
        # hook
        state = {
            'downloaded_bytes': 0,
            'frag_counter': 0,
        }
        start = time.time()

        def frag_progress_hook(status):
            frag_total_bytes = status.get('total_bytes', 0)
            estimated_size = (state['downloaded_bytes'] +
                (total_frags - state['frag_counter']) * frag_total_bytes)
            if status['status'] == 'finished':
                state['downloaded_bytes'] += frag_total_bytes
                state['frag_counter'] += 1
                progress = self.calc_percent(state['frag_counter'], total_frags)
                byte_counter = state['downloaded_bytes']
            else:
                frag_downloaded_bytes = status['downloaded_bytes']
                byte_counter = state['downloaded_bytes'] + frag_downloaded_bytes
                frag_progress = self.calc_percent(frag_downloaded_bytes,
                    frag_total_bytes)
                progress = self.calc_percent(state['frag_counter'], total_frags)
                progress += frag_progress / float(total_frags)

            eta = self.calc_eta(start, time.time(), estimated_size, byte_counter)
            self.report_progress(progress, format_bytes(estimated_size),
                status.get('speed'), eta)
        http_dl.add_progress_hook(frag_progress_hook)

        frags_filenames = []
        for (seg_i, frag_i) in fragments_list:
            name = 'Seg%d-Frag%d' % (seg_i, frag_i)
            url = base_url + name
            frag_filename = '%s-%s' % (tmpfilename, name)
            success = http_dl.download(frag_filename, {'url': url})
            if not success:
                return False
            with open(frag_filename, 'rb') as down:
                down_data = down.read()
                reader = FlvReader(down_data)
                while True:
                    _, box_type, box_data = reader.read_box_info()
                    if box_type == b'mdat':
                        dest_stream.write(box_data)
                        break
            frags_filenames.append(frag_filename)

        self.report_finish(format_bytes(state['downloaded_bytes']), time.time() - start)

        self.try_rename(tmpfilename, filename)
        for frag_file in frags_filenames:
            os.remove(frag_file)

        fsize = os.path.getsize(encodeFilename(filename))
        self._hook_progress({
            'downloaded_bytes': fsize,
            'total_bytes': fsize,
            'filename': filename,
            'status': 'finished',
        })

        return True
