#!/usr/bin/env python
# coding: utf-8
import errno
import os

from youtube_dl.compat import compat_st_mtime
from youtube_dl.utils import locked_file


class Archive(object):
    """ Class that manages the download Archive. Provides optimizations to avoid
      excessive file parsing.

      Initializing options:
        filepath: str       The filepath of the archive.

      Properties:
        _data: set          Container for holding a cache of the archive
        _disabled: bool     When true, all functions are effectively void
        filepath: str       The filepath of the archive

      Methods:
        __contains__        Checks a video id (archive id) exists in archive
        _read_archive       Reads archive from disk
        record_download     Adds a new download to archive
    """

    def __init__(self, filepath):
        """ Instantiate Archive
        filepath: str or None. The filepath of the archive. If None or empty
                                string is provided instance can still be used
                                but it's effectively doing nothing."""

        self.filepath = None if filepath == "" else filepath
        self._disabled = self.filepath is None
        self._data = set()

    def record_download(self, archive_id):
        """ Records a new archive_id in the archive """
        if self._disabled:
            return

        with locked_file(self.filepath, "a", encoding="utf-8") as file_out:
            file_out.write(archive_id + "\n")
        self._data.add(archive_id)

    def _read_file(self):
        """ Reads the data from archive file """
        if self._disabled:
            return

        try:
            with locked_file(self.filepath, "r", encoding="utf-8") as file_in:
                self._data.update(line.strip() for line in file_in)
        except IOError as err:
            if err.errno != errno.ENOENT:
                raise

    def __contains__(self, item):
        if not isinstance(item, str):
            raise ValueError(
                "An archive contains only strings. Provided {}".format(type(item))
            )

        if item not in self._data:
            self._read_file()
        return item in self._data
