from __future__ import unicode_literals

from ..utils import PostProcessingError


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
    """

    _downloader = None

    def __init__(self, downloader=None):
        self._downloader = downloader

    def set_downloader(self, downloader):
        """Sets the downloader for this PP."""
        self._downloader = downloader

    def run(self, information):
        """Run the PostProcessor.

        The "information" argument is a dictionary like the ones
        composed by InfoExtractors. The only difference is that this
        one has an extra field called "filepath" that points to the
        downloaded file.

        This method returns a tuple, the first element of which describes
        whether the original file should be kept (i.e. not deleted - None for
        no preference), and the second of which is the updated information.

        In addition, this method may raise a PostProcessingError
        exception if post processing fails.
        """
        return None, information  # by default, keep file and do nothing


class AudioConversionError(PostProcessingError):
    pass
