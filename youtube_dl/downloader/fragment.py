from __future__ import division, unicode_literals

import os
import time

from .common import FileDownloader
from .http import HttpFD
from ..utils import (
    encodeFilename,
    sanitize_open,
)


class HttpQuietDownloader(HttpFD):
    def to_screen(self, *args, **kargs):
        pass


class FragmentFD(FileDownloader):
    """
    A base file downloader class for fragmented media (e.g. f4m/m3u8 manifests).
    """

    def _prepare_and_start_frag_download(self, ctx):
        self._prepare_frag_download(ctx)
        self._start_frag_download(ctx)

    def _prepare_frag_download(self, ctx):
        self.to_screen('[%s] Total fragments: %d' % (self.FD_NAME, ctx['total_frags']))
        self.report_destination(ctx['filename'])
        dl = HttpQuietDownloader(
            self.ydl,
            {
                'continuedl': True,
                'quiet': True,
                'noprogress': True,
                'ratelimit': self.params.get('ratelimit', None),
                'retries': self.params.get('retries', 0),
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
        ctx['started'] = start

        def frag_progress_hook(s):
            if s['status'] not in ('downloading', 'finished'):
                return

            frag_total_bytes = s.get('total_bytes', 0)
            if s['status'] == 'finished':
                state['downloaded_bytes'] += frag_total_bytes
                state['frag_index'] += 1

            estimated_size = (
                (state['downloaded_bytes'] + frag_total_bytes) /
                (state['frag_index'] + 1) * total_frags)
            time_now = time.time()
            state['total_bytes_estimate'] = estimated_size
            state['elapsed'] = time_now - start

            if s['status'] == 'finished':
                progress = self.calc_percent(state['frag_index'], total_frags)
            else:
                frag_downloaded_bytes = s['downloaded_bytes']
                frag_progress = self.calc_percent(frag_downloaded_bytes,
                                                  frag_total_bytes)
                progress = self.calc_percent(state['frag_index'], total_frags)
                progress += frag_progress / float(total_frags)

                state['eta'] = self.calc_eta(
                    start, time_now, estimated_size, state['downloaded_bytes'] + frag_downloaded_bytes)
                state['speed'] = s.get('speed')
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
