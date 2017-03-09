from __future__ import division, unicode_literals

import os
import time

from .common import FileDownloader
from .http import HttpFD
from ..utils import (
    error_to_compat_str,
    encodeFilename,
    sanitize_open,
    sanitized_Request,
)


class HttpQuietDownloader(HttpFD):
    def to_screen(self, *args, **kargs):
        pass


class FragmentFD(FileDownloader):
    """
    A base file downloader class for fragmented media (e.g. f4m/m3u8 manifests).

    Available options:

    fragment_retries:   Number of times to retry a fragment for HTTP error (DASH
                        and hlsnative only)
    skip_unavailable_fragments:
                        Skip unavailable fragments (DASH and hlsnative only)
    """

    def report_retry_fragment(self, err, fragment_name, count, retries):
        self.to_screen(
            '[download] Got server HTTP error: %s. Retrying fragment %s (attempt %d of %s)...'
            % (error_to_compat_str(err), fragment_name, count, self.format_retries(retries)))

    def report_skip_fragment(self, fragment_name):
        self.to_screen('[download] Skipping fragment %s...' % fragment_name)

    def _prepare_url(self, info_dict, url):
        headers = info_dict.get('http_headers')
        return sanitized_Request(url, None, headers) if headers else url

    def _prepare_and_start_frag_download(self, ctx):
        self._prepare_frag_download(ctx)
        self._start_frag_download(ctx)

    def _prepare_frag_download(self, ctx):
        if 'live' not in ctx:
            ctx['live'] = False
        self.to_screen(
            '[%s] Total fragments: %s'
            % (self.FD_NAME, ctx['total_frags'] if not ctx['live'] else 'unknown (live)'))
        self.report_destination(ctx['filename'])
        dl = HttpQuietDownloader(
            self.ydl,
            {
                'continuedl': True,
                'quiet': True,
                'noprogress': True,
                'ratelimit': self.params.get('ratelimit'),
                'retries': self.params.get('retries', 0),
                'nopart': self.params.get('nopart', False),
                'test': self.params.get('test', False),
            }
        )
        tmpfilename = self.temp_name(ctx['filename'])
        dest_stream, tmpfilename = sanitize_open(tmpfilename, 'wb')
        ctx.update({
            'dl': dl,
            'dest_stream': dest_stream,
            'tmpfilename': tmpfilename,
        })

    def _start_frag_download(self, ctx):
        total_frags = ctx['total_frags']
        # This dict stores the download progress, it's updated by the progress
        # hook
        state = {
            'status': 'downloading',
            'downloaded_bytes': 0,
            'frag_index': 0,
            'frag_count': total_frags,
            'filename': ctx['filename'],
            'tmpfilename': ctx['tmpfilename'],
        }

        start = time.time()
        ctx.update({
            'started': start,
            # Total complete fragments downloaded so far in bytes
            'complete_frags_downloaded_bytes': 0,
            # Amount of fragment's bytes downloaded by the time of the previous
            # frag progress hook invocation
            'prev_frag_downloaded_bytes': 0,
        })

        def frag_progress_hook(s):
            if s['status'] not in ('downloading', 'finished'):
                return

            time_now = time.time()
            state['elapsed'] = time_now - start
            frag_total_bytes = s.get('total_bytes') or 0
            if not ctx['live']:
                estimated_size = (
                    (ctx['complete_frags_downloaded_bytes'] + frag_total_bytes) /
                    (state['frag_index'] + 1) * total_frags)
                state['total_bytes_estimate'] = estimated_size

            if s['status'] == 'finished':
                state['frag_index'] += 1
                state['downloaded_bytes'] += frag_total_bytes - ctx['prev_frag_downloaded_bytes']
                ctx['complete_frags_downloaded_bytes'] = state['downloaded_bytes']
                ctx['prev_frag_downloaded_bytes'] = 0
            else:
                frag_downloaded_bytes = s['downloaded_bytes']
                state['downloaded_bytes'] += frag_downloaded_bytes - ctx['prev_frag_downloaded_bytes']
                if not ctx['live']:
                    state['eta'] = self.calc_eta(
                        start, time_now, estimated_size,
                        state['downloaded_bytes'])
                state['speed'] = s.get('speed') or ctx.get('speed')
                ctx['speed'] = state['speed']
                ctx['prev_frag_downloaded_bytes'] = frag_downloaded_bytes
            self._hook_progress(state)

        ctx['dl'].add_progress_hook(frag_progress_hook)

        return start

    def _finish_frag_download(self, ctx):
        ctx['dest_stream'].close()
        elapsed = time.time() - ctx['started']
        self.try_rename(ctx['tmpfilename'], ctx['filename'])
        fsize = os.path.getsize(encodeFilename(ctx['filename']))

        self._hook_progress({
            'downloaded_bytes': fsize,
            'total_bytes': fsize,
            'filename': ctx['filename'],
            'status': 'finished',
            'elapsed': elapsed,
        })
