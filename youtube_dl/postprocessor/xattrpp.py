import os
import subprocess
import sys

from .common import PostProcessor
from ..utils import (
    hyphenate_date,
    preferredencoding,
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

    def run(self, info):
        """ Set extended attributes on downloaded file (if xattr support is found). """

        # This mess below finds the best xattr tool for the job and creates a
        # "write_xattr" function.
        try:
            # try the pyxattr module...
            import xattr
            def write_xattr(path, key, value):
                return xattr.setxattr(path, key, value)

        except ImportError:

            if os.name == 'posix':
                def which(bin):
                    for dir in os.environ["PATH"].split(":"):
                        path = os.path.join(dir, bin)
                        if os.path.exists(path):
                            return path

                user_has_setfattr = which("setfattr")
                user_has_xattr    = which("xattr")

                if user_has_setfattr or user_has_xattr:

                    def write_xattr(path, key, value):
                        import errno
                        potential_errors = {
                            # setfattr: /tmp/blah: Operation not supported
                            "Operation not supported": errno.EOPNOTSUPP,
                            # setfattr: ~/blah: No such file or directory
                            # xattr: No such file: ~/blah
                            "No such file": errno.ENOENT,
                        }

                        if user_has_setfattr:
                            cmd = ['setfattr', '-n', key, '-v', value, path]
                        elif user_has_xattr:
                            cmd = ['xattr', '-w', key, value, path]

                        try:
                            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                        except subprocess.CalledProcessError as e:
                            errorstr = e.output.strip().decode()
                            for potential_errorstr, potential_errno in potential_errors.items():
                                if errorstr.find(potential_errorstr) > -1:
                                    e = OSError(potential_errno, potential_errorstr)
                                    e.__cause__ = None
                                    raise e
                            raise  # Reraise unhandled error

                else:
                    # On Unix, and can't find pyxattr, setfattr, or xattr.
                    if sys.platform.startswith('linux'):
                        self._downloader.report_error("Couldn't find a tool to set the xattrs. Install either the python 'pyxattr' or 'xattr' modules, or the GNU 'attr' package (which contains the 'setfattr' tool).")
                    elif sys.platform == 'darwin':
                        self._downloader.report_error("Couldn't find a tool to set the xattrs. Install either the python 'xattr' module, or the 'xattr' binary.")
            else:
                # Write xattrs to NTFS Alternate Data Streams: http://en.wikipedia.org/wiki/NTFS#Alternate_data_streams_.28ADS.29
                def write_xattr(path, key, value):
                    assert(key.find(":") < 0)
                    assert(path.find(":") < 0)
                    assert(os.path.exists(path))

                    ads_fn = path + ":" + key
                    with open(ads_fn, "w") as f:
                        f.write(value)

        # Write the metadata to the file's xattrs
        self._downloader.to_screen('[metadata] Writing metadata to file\'s xattrs...')

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
                    if infoname == "upload_date":
                        value = hyphenate_date(value)

                    byte_value = value.encode(preferredencoding())
                    write_xattr(filename, xattrname, byte_value)

            return True, info

        except OSError:
            self._downloader.report_error("This filesystem doesn't support extended attributes. (You may have to enable them in your /etc/fstab)")
            return False, info

