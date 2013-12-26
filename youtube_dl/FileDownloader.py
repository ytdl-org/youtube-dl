# Legacy file for backwards compatibility, use youtube_dl.downloader instead!
from .downloader import FileDownloader as RealFileDownloader
from .downloader import get_suitable_downloader


# This class reproduces the old behaviour of FileDownloader
class FileDownloader(RealFileDownloader):
    def _do_download(self, filename, info_dict):
        real_fd = get_suitable_downloader(info_dict)(self.ydl, self.params)
        for ph in self._progress_hooks:
            real_fd.add_progress_hook(ph)
        return real_fd.download(filename, info_dict)
