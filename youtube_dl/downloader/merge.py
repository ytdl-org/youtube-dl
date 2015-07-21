from __future__ import unicode_literals, division

import threading

from .common import FileDownloader, StopDownload
import youtube_dl
from ..utils import prepend_extension


def _join_threads(threads, timeout=None):
    for t in threads:
        t.join(timeout=timeout)


class MergeFD(FileDownloader):
    def _normal_download(self, filename, infos):
        success = True
        for fname, info in infos:
            params = dict(self.params)
            params.update({
                'quiet': True,
                'noprogress': True,
            })
            fd = youtube_dl.downloader.get_suitable_downloader(info, self.params)(self.ydl, params)

            def hook(status):
                self._hook_progress(status)

            fd.add_progress_hook(hook)
            self.report_destination(fname)
            partial_success = fd.download(fname, info)
            success = success and partial_success
        return success

    def _parallel_download(self, filename, infos):
        self.report_warning('Downloading DASH formats in parallel is an experimental feature, some things may not work as expected')
        threads = []
        statuses = []
        downloaders = []
        lock = threading.Lock()
        stop_event = threading.Event()
        for fname, info in infos:
            params = dict(self.params)
            params.update({
                'quiet': True,
                'noprogress': True,
            })
            FD = youtube_dl.downloader.get_suitable_downloader(info, self.params)
            fd = FD(self.ydl, params)
            downloaders.append(fd)

            status = {}
            statuses.append(status)

            def hook(s, status=status):
                with lock:
                    status.update(s)
                    s['_skip_report_progress'] = True
                    self._hook_progress(s)

                    global_status = {'filename': filename}
                    if any(s.get('status') == 'downloading' for s in statuses):
                        global_status['status'] = 'downloading'
                    elif all(s.get('status') == 'finished' for s in statuses):
                        global_status['status'] = 'finished'
                    else:
                        global_status['status'] = None
                    for s in statuses:
                        for key in ['total_bytes', 'downloaded_bytes', 'eta', 'elapsed', 'speed']:
                            if s.get(key) is not None:
                                global_status.setdefault(key, 0)
                                global_status[key] += s[key]
                    # Don't call _hook_progress because it's not a real file
                    self.report_progress(global_status)
                if stop_event.is_set():
                    raise StopDownload()

            fd.add_progress_hook(hook)
            self.report_destination(fname)

            def dl(fd, *args):
                fd._error = None
                try:
                    return fd.download(*args)
                except StopDownload:
                    pass
                except Exception as err:
                    fd._error = err

            thread = threading.Thread(target=dl, args=(fd, fname, info))
            threads.append(thread)
        try:
            for t in threads:
                t.start()
            while True:
                # the timeout seems to be required so that the main thread can
                # catch the exceptions in python 2.x
                _join_threads(threads, timeout=1)
                if not any(t.is_alive() for t in threads):
                    break
        except BaseException:
            stop_event.set()
            _join_threads(threads)
            raise

        for fd in downloaders:
            if fd._error is not None:
                raise fd._error
        return True

    def real_download(self, filename, info_dict):
        infos = []
        for f in info_dict['requested_formats']:
            new_info = dict(info_dict)
            del new_info['requested_formats']
            new_info.update(f)
            fname = self.ydl.prepare_filename(new_info)
            fname = prepend_extension(fname, 'f%s' % f['format_id'], new_info['ext'])
            infos.append((fname, new_info))

        info_dict['__files_to_merge'] = [name for name, _ in infos]

        if self.params.get('parallel_dash_downloads', False):
            return self._parallel_download(filename, infos)
        else:
            return self._normal_download(filename, infos)
