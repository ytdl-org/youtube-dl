from __future__ import unicode_literals
from sys import version_info
from .common import PostProcessor
from ..compat import compat_os_name
from ..utils import (
    hyphenate_date,
    write_xattr,
    XAttrMetadataError,
    XAttrUnavailableError,
)


class XAttrMetadataPP(PostProcessor):

    #
    # More info about extended attributes for media:
    #   http://freedesktop.org/wiki/CommonExtendedAttributes/
    #   http://www.freedesktop.org/wiki/PhreedomDraft/
    #   http://dublincore.org/documents/usageguide/elements.shtml
    #
    # TODO:
    #  * capture youtube keywords and put them in 'user.dublincore.subject' (comma-separated)
    #  * figure out which xattrs can be used for 'duration', 'thumbnail', 'resolution'
    #

    @staticmethod
    def write_xattr(path, key, value):
        """ proxy to make it easier to mockup and run unit tests. """
        write_xattr(path, key, value)

    @staticmethod
    def get_tags(info):
        """ Get comma-separated and non-duplicated keywords from tags and categories. """

        mixed = []
        tags = info.get('tags')
        if tags is not None and len(tags) > 0:
            mixed += tags

        categories = info.get('categories')
        if categories is not None and len(categories) > 0:
            mixed += categories

        if len(mixed) > 0:
            if version_info.major < 3:
                mixed = map(lambda x: x.decode('utf-8'), mixed)

            mixed = set(map(lambda x: x.lower(), mixed))
            mixed = sorted(mixed)
            return ','.join(mixed).encode('utf-8')

        return None

    def run(self, info):
        """ Set extended attributes on downloaded file (if xattr support is found). """

        # Write the metadata to the file's xattrs
        self._downloader.to_screen('[metadata] Writing metadata to file\'s xattrs')

        filename = info['filepath']

        try:
            xattr_mapping = {
                'user.xdg.origin.url': 'webpage_url',
                'user.xdg.referrer.url': 'webpage_url',
                # 'user.xdg.comment':            'description',
                'user.dublincore.title': 'title',
                'user.dublincore.date': 'upload_date',
                'user.dublincore.description': 'description',
                'user.dublincore.contributor': 'uploader',
                'user.dublincore.format': 'format',
            }

            num_written = 0
            for xattrname, infoname in xattr_mapping.items():

                value = info.get(infoname)

                if value:
                    if infoname == 'upload_date':
                        value = hyphenate_date(value)

                    byte_value = value.encode('utf-8')
                    self.write_xattr(filename, xattrname, byte_value)
                    num_written += 1

            tags = self.get_tags(info)
            if tags is not None and len(tags) > 0:
                self.write_xattr(filename, 'user.xdg.tags', tags)
                self.write_xattr(filename, 'user.dublincore.subject', tags)
                num_written += 2

            if info.get('age_limit') is not None and info.get('age_limit') >= 18:
                self.write_xattr(filename, 'user.dublincore.audience', 'adults'.encode('utf-8'))
                num_written += 1
            else:
                self.write_xattr(filename, 'user.dublincore.audience', 'everybody'.encode('utf-8'))
                num_written += 1

            self.write_xattr(filename, 'user.dublincore.type', 'MovingImage'.encode('utf-8'))
            self.write_xattr(filename, 'user.creator', 'youtube-dl'.encode('utf-8'))
            num_written += 2

            return [], info

        except XAttrUnavailableError as e:
            self._downloader.report_error(str(e))
            return [], info

        except XAttrMetadataError as e:
            if e.reason == 'NO_SPACE':
                self._downloader.report_warning(
                    'There\'s no disk space left, disk quota exceeded or filesystem xattr limit exceeded. ' +
                    (('Some ' if num_written else '') + 'extended attributes are not written.').capitalize())
            elif e.reason == 'VALUE_TOO_LONG':
                self._downloader.report_warning(
                    'Unable to write extended attributes due to too long values.')
            else:
                msg = 'This filesystem doesn\'t support extended attributes. '
                if compat_os_name == 'nt':
                    msg += 'You need to use NTFS.'
                else:
                    msg += '(You may have to enable them in your /etc/fstab)'
                self._downloader.report_error(msg)
            return [], info
