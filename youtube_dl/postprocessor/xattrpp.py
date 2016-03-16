from __future__ import unicode_literals

import os
import subprocess
import sys
import errno

from .common import PostProcessor
from ..compat import compat_os_name
from ..utils import (
    check_executable,
    hyphenate_date,
    version_tuple,
    PostProcessingError,
    encodeArgument,
    encodeFilename,
)


class XAttrMetadataError(PostProcessingError):
    def __init__(self, code=None, msg='Unknown error'):
        super(XAttrMetadataError, self).__init__(msg)
        self.code = code

        # Parsing code and msg
        if (self.code in (errno.ENOSPC, errno.EDQUOT) or
                'No space left' in self.msg or 'Disk quota excedded' in self.msg):
            self.reason = 'NO_SPACE'
        elif self.code == errno.E2BIG or 'Argument list too long' in self.msg:
            self.reason = 'VALUE_TOO_LONG'
        else:
            self.reason = 'NOT_SUPPORTED'


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

    def run(self, info):
        """ Set extended attributes on downloaded file (if xattr support is found). """

        # This mess below finds the best xattr tool for the job and creates a
        # "write_xattr" function.
        try:
            # try the pyxattr module...
            import xattr

            # Unicode arguments are not supported in python-pyxattr until
            # version 0.5.0
            # See https://github.com/rg3/youtube-dl/issues/5498
            pyxattr_required_version = '0.5.0'
            if version_tuple(xattr.__version__) < version_tuple(pyxattr_required_version):
                self._downloader.report_warning(
                    'python-pyxattr is detected but is too old. '
                    'youtube-dl requires %s or above while your version is %s. '
                    'Falling back to other xattr implementations' % (
                        pyxattr_required_version, xattr.__version__))

                raise ImportError

            def write_xattr(path, key, value):
                try:
                    xattr.set(path, key, value)
                except EnvironmentError as e:
                    raise XAttrMetadataError(e.errno, e.strerror)

        except ImportError:
            if compat_os_name == 'nt':
                # Write xattrs to NTFS Alternate Data Streams:
                # http://en.wikipedia.org/wiki/NTFS#Alternate_data_streams_.28ADS.29
                def write_xattr(path, key, value):
                    assert ':' not in key
                    assert os.path.exists(path)

                    ads_fn = path + ':' + key
                    try:
                        with open(ads_fn, 'wb') as f:
                            f.write(value)
                    except EnvironmentError as e:
                        raise XAttrMetadataError(e.errno, e.strerror)
            else:
                user_has_setfattr = check_executable('setfattr', ['--version'])
                user_has_xattr = check_executable('xattr', ['-h'])

                if user_has_setfattr or user_has_xattr:

                    def write_xattr(path, key, value):
                        value = value.decode('utf-8')
                        if user_has_setfattr:
                            executable = 'setfattr'
                            opts = ['-n', key, '-v', value]
                        elif user_has_xattr:
                            executable = 'xattr'
                            opts = ['-w', key, value]

                        cmd = ([encodeFilename(executable, True)] +
                               [encodeArgument(o) for o in opts] +
                               [encodeFilename(path, True)])

                        try:
                            p = subprocess.Popen(
                                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                        except EnvironmentError as e:
                            raise XAttrMetadataError(e.errno, e.strerror)
                        stdout, stderr = p.communicate()
                        stderr = stderr.decode('utf-8', 'replace')
                        if p.returncode != 0:
                            raise XAttrMetadataError(p.returncode, stderr)

                else:
                    # On Unix, and can't find pyxattr, setfattr, or xattr.
                    if sys.platform.startswith('linux'):
                        self._downloader.report_error(
                            "Couldn't find a tool to set the xattrs. "
                            "Install either the python 'pyxattr' or 'xattr' "
                            "modules, or the GNU 'attr' package "
                            "(which contains the 'setfattr' tool).")
                    else:
                        self._downloader.report_error(
                            "Couldn't find a tool to set the xattrs. "
                            "Install either the python 'xattr' module, "
                            "or the 'xattr' binary.")

        # Write the metadata to the file's xattrs
        self._downloader.to_screen('[metadata] Writing metadata to file\'s xattrs')

        filename = info['filepath']

        try:
            xattr_mapping = {
                'user.xdg.referrer.url': 'webpage_url',
                # 'user.xdg.comment':            'description',
                'user.dublincore.title': 'title',
                'user.dublincore.date': 'upload_date',
                'user.dublincore.description': 'description',
                'user.dublincore.contributor': 'uploader',
                'user.dublincore.format': 'format',
            }

            for xattrname, infoname in xattr_mapping.items():

                value = info.get(infoname)

                if value:
                    if infoname == 'upload_date':
                        value = hyphenate_date(value)

                    byte_value = value.encode('utf-8')
                    write_xattr(filename, xattrname, byte_value)

            return [], info

        except XAttrMetadataError as e:
            if e.reason == 'NO_SPACE':
                self._downloader.report_warning(
                    'There\'s no disk space left or disk quota exceeded. ' +
                    'Extended attributes are not written.')
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
