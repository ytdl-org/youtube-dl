from __future__ import unicode_literals

import os

from ..compat import compat_str
from ..utils import (
    PostProcessingError,
    encodeFilename,
)


class PostProcessor(object):
    """Post Processor class.

    PostProcessor objects can be added to downloaders with their
    add_post_processor() method. When the downloader has finished a
    successful download, it will take its internal chain of PostProcessors
    and start calling the run() method on each one of them, first with
    an initial argument and then with the returned value of the previous
    PostProcessor.

    The chain will be stopped if one of them ever returns None or the end
    of the chain is reached.

    PostProcessor objects follow a "mutual registration" process similar
    to InfoExtractor objects.

    Optionally PostProcessor can use a list of additional command-line arguments
    with self._configuration_args.
    """

    _downloader = None

    def __init__(self, downloader=None):
        self._downloader = downloader

    @classmethod
    def pp_key(cls):
        return compat_str(cls.__name__[:-2])

    def set_downloader(self, downloader):
        """Sets the downloader for this PP."""
        self._downloader = downloader

    def run(self, information):
        """Run the PostProcessor.

        The "information" argument is a dictionary like the ones
        composed by InfoExtractors. The only difference is that this
        one has an extra field called "filepath" that points to the
        downloaded file.

        This method returns a tuple, the first element is a list of the files
        that can be deleted, and the second of which is the updated
        information.

        In addition, this method may raise a PostProcessingError
        exception if post processing fails.
        """
        return [], information  # by default, keep file and do nothing

    def try_utime(self, path, atime, mtime, errnote='Cannot update utime of file'):
        try:
            os.utime(encodeFilename(path), (atime, mtime))
        except Exception:
            self._downloader.report_warning(errnote)

    def _configuration_args(self, default=[]):
        args = self._downloader.params.get('postprocessor_args', {})
        if isinstance(args, (list, tuple)) or args is None:  # for backward compatibility
            return args
        if args is None:
            return default
        if isinstance(args, (list, tuple)):  # for backward compatibility
            return args
        assert isinstance(args, dict)
        pp_args = args.get(self.pp_key().lower(), args.get('default', []))
        assert isinstance(pp_args, (list, tuple)) or pp_args is None
        return pp_args


class AudioConversionError(PostProcessingError):
    pass
