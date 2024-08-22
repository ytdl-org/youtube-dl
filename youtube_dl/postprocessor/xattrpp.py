from __future__ import unicode_literals

import plistlib
import subprocess
import sys

from xml.sax.saxutils import escape

from .common import PostProcessor
from ..compat import compat_os_name
from ..utils import (
    check_executable,
    encodeArgument,
    encodeFilename,
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

    def run(self, info):
        """ Set extended attributes on downloaded file (if xattr support is found). """

        # Write the metadata to the file's xattrs
        self._downloader.to_screen('[metadata] Writing metadata to file\'s xattrs')

        filename = info['filepath']

        try:
            if sys.platform != 'darwin':  # other than macOS
                xattr_mapping = {
                    'user.xdg.referrer.url': 'webpage_url',
                    # 'user.xdg.comment':            'description',
                    'user.dublincore.title': 'title',
                    'user.dublincore.date': 'upload_date',
                    'user.dublincore.description': 'description',
                    'user.dublincore.contributor': 'uploader',
                    'user.dublincore.format': 'format',
                }
            else:  # macOS
                xattr_mapping = {
                    'com.apple.metadata:kMDItemWhereFroms': 'webpage_url',
                    # 'user.xdg.comment': 'description',
                    'com.apple.metadata:kMDItemTitle': 'title',
                    'user.dublincore.date': 'upload_date',  # no corresponding attr
                    'com.apple.metadata:kMDItemDescription': 'description',
                    'com.apple.metadata:kMDItemContributors': 'uploader',
                    'user.dublincore.format': 'format',  # no corresponding attr
                }

            num_written = 0
            for xattrname, infoname in xattr_mapping.items():

                value = info.get(infoname)

                if value:
                    if not xattrname.startswith('com.apple.metadata:'):
                        if infoname == 'upload_date':
                            value = hyphenate_date(value)

                        byte_value = value.encode('utf-8')

                    else:  # macOS Spotlight metadata
                        byte_value = self.make_mditem(xattrname, value)

                    write_xattr(filename, xattrname, byte_value)
                    num_written += 1

            return [], info

        except XAttrUnavailableError as e:
            self._downloader.report_error(str(e))
            return [], info

        except XAttrMetadataError as e:
            if e.reason == 'NO_SPACE':
                self._downloader.report_warning(
                    'There\'s no disk space left, disk quota exceeded or filesystem xattr limit exceeded. '
                    + (('Some ' if num_written else '') + 'extended attributes are not written.').capitalize())
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

    def make_mditem(self, attrname, value):
        # Info about macOS Spotlight metadata:
        #   https://developer.apple.com/library/archive/documentation/CoreServices/Reference/MetadataAttributesRef/Reference/CommonAttrs.html

        attr_is_cfarray = attrname in (
            'com.apple.metadata:kMDItemContributors',
            'com.apple.metadata:kMDItemWhereFroms')

        if hasattr(plistlib, 'dumps'):  # Python >= 3.4, need new api to make binary plist
            if attr_is_cfarray:
                value = [value]
            return plistlib.dumps(value, fmt=plistlib.FMT_BINARY)

        else:
            # try PyObjC (or pyobjc-framework-Cocoa)
            try:
                from Foundation import NSPropertyListSerialization, NSPropertyListBinaryFormat_v1_0

                if attr_is_cfarray:
                    data = [value]
                else:
                    data = value
                plist, err = NSPropertyListSerialization.dataWithPropertyList_format_options_error_(
                    data, NSPropertyListBinaryFormat_v1_0, 0, None)
                if not err and plist:
                    return bytes(plist)
            except (ImportError, ValueError):
                pass  # go on to try plutil command

            # make xml plist first to convert to binary plist with plutil command,
            # or to use as a fallback if conversion failed
            plist = '<string>' + escape(value) + '</string>\n'
            if attr_is_cfarray:
                plist = '<array>\n\t' + plist + '</array>\n'
            plist = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                '<plist version="1.0">\n') + plist + '</plist>'
            xmlplist = plist.encode('utf-8')

            # try plutil command (like `cat xmlplist | plutil -convert binary1 -o - -`)
            plutil = check_executable('plutil', ['-help'])
            if plutil:
                cmd = ([encodeFilename(plutil, True)]
                       + [encodeArgument(o) for o in ['-convert', 'binary1', '-o', '-', '-']])
                try:
                    p = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    stdout, stderr = p.communicate(input=xmlplist)
                    if p.returncode == 0:
                        return bytes(stdout)
                except EnvironmentError:
                    pass  # fallback to xml plist

            return xmlplist
