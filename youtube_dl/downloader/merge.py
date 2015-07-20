from __future__ import unicode_literals

from .common import FileDownloader
import youtube_dl
from ..utils import prepend_extension


class MergeFD(FileDownloader):
    def real_download(self, filename, info_dict):
        infos = []
        for f in info_dict['requested_formats']:
            new_info = dict(info_dict)
            del new_info['requested_formats']
            new_info.update(f)
            fname = self.ydl.prepare_filename(new_info)
            fname = prepend_extension(fname, 'f%s' % f['format_id'], new_info['ext'])
            infos.append((fname, new_info))
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

        info_dict['__files_to_merge'] = [fname for fname, _ in infos]

        return True
