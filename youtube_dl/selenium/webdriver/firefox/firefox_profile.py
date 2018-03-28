# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import with_statement

import base64
import copy
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from xml.dom import minidom
from selenium.webdriver.common.proxy import ProxyType
from selenium.common.exceptions import WebDriverException


WEBDRIVER_EXT = "webdriver.xpi"
WEBDRIVER_PREFERENCES = "webdriver_prefs.json"
EXTENSION_NAME = "fxdriver@googlecode.com"


class AddonFormatError(Exception):
    """Exception for not well-formed add-on manifest files"""


class FirefoxProfile(object):
    ANONYMOUS_PROFILE_NAME = "WEBDRIVER_ANONYMOUS_PROFILE"
    DEFAULT_PREFERENCES = None

    def __init__(self, profile_directory=None):
        """
        Initialises a new instance of a Firefox Profile

        :args:
         - profile_directory: Directory of profile that you want to use.
           This defaults to None and will create a new
           directory when object is created.
        """
        if not FirefoxProfile.DEFAULT_PREFERENCES:
            with open(os.path.join(os.path.dirname(__file__),
                                   WEBDRIVER_PREFERENCES)) as default_prefs:
                FirefoxProfile.DEFAULT_PREFERENCES = json.load(default_prefs)

        self.default_preferences = copy.deepcopy(
            FirefoxProfile.DEFAULT_PREFERENCES['mutable'])
        self.native_events_enabled = True
        self.profile_dir = profile_directory
        self.tempfolder = None
        if self.profile_dir is None:
            self.profile_dir = self._create_tempfolder()
        else:
            self.tempfolder = tempfile.mkdtemp()
            newprof = os.path.join(self.tempfolder, "webdriver-py-profilecopy")
            shutil.copytree(self.profile_dir, newprof,
                            ignore=shutil.ignore_patterns("parent.lock", "lock", ".parentlock"))
            self.profile_dir = newprof
            os.chmod(self.profile_dir, 0o755)
            self._read_existing_userjs(os.path.join(self.profile_dir, "user.js"))
        self.extensionsDir = os.path.join(self.profile_dir, "extensions")
        self.userPrefs = os.path.join(self.profile_dir, "user.js")
        if os.path.isfile(self.userPrefs):
            os.chmod(self.userPrefs, 0o644)

    # Public Methods
    def set_preference(self, key, value):
        """
        sets the preference that we want in the profile.
        """
        self.default_preferences[key] = value

    def add_extension(self, extension=WEBDRIVER_EXT):
        self._install_extension(extension)

    def update_preferences(self):
        for key, value in FirefoxProfile.DEFAULT_PREFERENCES['frozen'].items():
            self.default_preferences[key] = value
        self._write_user_prefs(self.default_preferences)

    # Properties

    @property
    def path(self):
        """
        Gets the profile directory that is currently being used
        """
        return self.profile_dir

    @property
    def port(self):
        """
        Gets the port that WebDriver is working on
        """
        return self._port

    @port.setter
    def port(self, port):
        """
        Sets the port that WebDriver will be running on
        """
        if not isinstance(port, int):
            raise WebDriverException("Port needs to be an integer")
        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise WebDriverException("Port number must be in the range 1..65535")
        except (ValueError, TypeError):
            raise WebDriverException("Port needs to be an integer")
        self._port = port
        self.set_preference("webdriver_firefox_port", self._port)

    @property
    def accept_untrusted_certs(self):
        return self.default_preferences["webdriver_accept_untrusted_certs"]

    @accept_untrusted_certs.setter
    def accept_untrusted_certs(self, value):
        if value not in [True, False]:
            raise WebDriverException("Please pass in a Boolean to this call")
        self.set_preference("webdriver_accept_untrusted_certs", value)

    @property
    def assume_untrusted_cert_issuer(self):
        return self.default_preferences["webdriver_assume_untrusted_issuer"]

    @assume_untrusted_cert_issuer.setter
    def assume_untrusted_cert_issuer(self, value):
        if value not in [True, False]:
            raise WebDriverException("Please pass in a Boolean to this call")

        self.set_preference("webdriver_assume_untrusted_issuer", value)

    @property
    def native_events_enabled(self):
        return self.default_preferences['webdriver_enable_native_events']

    @native_events_enabled.setter
    def native_events_enabled(self, value):
        if value not in [True, False]:
            raise WebDriverException("Please pass in a Boolean to this call")
        self.set_preference("webdriver_enable_native_events", value)

    @property
    def encoded(self):
        """
        A zipped, base64 encoded string of profile directory
        for use with remote WebDriver JSON wire protocol
        """
        self.update_preferences()
        fp = BytesIO()
        zipped = zipfile.ZipFile(fp, 'w', zipfile.ZIP_DEFLATED)
        path_root = len(self.path) + 1  # account for trailing slash
        for base, dirs, files in os.walk(self.path):
            for fyle in files:
                filename = os.path.join(base, fyle)
                zipped.write(filename, filename[path_root:])
        zipped.close()
        return base64.b64encode(fp.getvalue()).decode('UTF-8')

    def set_proxy(self, proxy):
        import warnings

        warnings.warn(
            "This method has been deprecated. Please pass in the proxy object to the Driver Object",
            DeprecationWarning)
        if proxy is None:
            raise ValueError("proxy can not be None")

        if proxy.proxy_type is ProxyType.UNSPECIFIED:
            return

        self.set_preference("network.proxy.type", proxy.proxy_type['ff_value'])

        if proxy.proxy_type is ProxyType.MANUAL:
            self.set_preference("network.proxy.no_proxies_on", proxy.no_proxy)
            self._set_manual_proxy_preference("ftp", proxy.ftp_proxy)
            self._set_manual_proxy_preference("http", proxy.http_proxy)
            self._set_manual_proxy_preference("ssl", proxy.ssl_proxy)
            self._set_manual_proxy_preference("socks", proxy.socks_proxy)
        elif proxy.proxy_type is ProxyType.PAC:
            self.set_preference("network.proxy.autoconfig_url", proxy.proxy_autoconfig_url)

    def _set_manual_proxy_preference(self, key, setting):
        if setting is None or setting is '':
            return

        host_details = setting.split(":")
        self.set_preference("network.proxy.%s" % key, host_details[0])
        if len(host_details) > 1:
            self.set_preference("network.proxy.%s_port" % key, int(host_details[1]))

    def _create_tempfolder(self):
        """
        Creates a temp folder to store User.js and the extension
        """
        return tempfile.mkdtemp()

    def _write_user_prefs(self, user_prefs):
        """
        writes the current user prefs dictionary to disk
        """
        with open(self.userPrefs, "w") as f:
            for key, value in user_prefs.items():
                f.write('user_pref("%s", %s);\n' % (key, json.dumps(value)))

    def _read_existing_userjs(self, userjs):
        import warnings

        PREF_RE = re.compile(r'user_pref\("(.*)",\s(.*)\)')
        try:
            with open(userjs) as f:
                for usr in f:
                    matches = re.search(PREF_RE, usr)
                    try:
                        self.default_preferences[matches.group(1)] = json.loads(matches.group(2))
                    except Exception:
                        warnings.warn("(skipping) failed to json.loads existing preference: " +
                                      matches.group(1) + matches.group(2))
        except Exception:
            # The profile given hasn't had any changes made, i.e no users.js
            pass

    def _install_extension(self, addon, unpack=True):
        """
            Installs addon from a filepath, url
            or directory of addons in the profile.
            - path: url, absolute path to .xpi, or directory of addons
            - unpack: whether to unpack unless specified otherwise in the install.rdf
        """
        if addon == WEBDRIVER_EXT:
            addon = os.path.join(os.path.dirname(__file__), WEBDRIVER_EXT)

        tmpdir = None
        xpifile = None
        if addon.endswith('.xpi'):
            tmpdir = tempfile.mkdtemp(suffix='.' + os.path.split(addon)[-1])
            compressed_file = zipfile.ZipFile(addon, 'r')
            for name in compressed_file.namelist():
                if name.endswith('/'):
                    if not os.path.isdir(os.path.join(tmpdir, name)):
                        os.makedirs(os.path.join(tmpdir, name))
                else:
                    if not os.path.isdir(os.path.dirname(os.path.join(tmpdir, name))):
                        os.makedirs(os.path.dirname(os.path.join(tmpdir, name)))
                    data = compressed_file.read(name)
                    with open(os.path.join(tmpdir, name), 'wb') as f:
                        f.write(data)
            xpifile = addon
            addon = tmpdir

        # determine the addon id
        addon_details = self._addon_details(addon)
        addon_id = addon_details.get('id')
        assert addon_id, 'The addon id could not be found: %s' % addon

        # copy the addon to the profile
        addon_path = os.path.join(self.extensionsDir, addon_id)
        if not unpack and not addon_details['unpack'] and xpifile:
            if not os.path.exists(self.extensionsDir):
                os.makedirs(self.extensionsDir)
                os.chmod(self.extensionsDir, 0o755)
            shutil.copy(xpifile, addon_path + '.xpi')
        else:
            if not os.path.exists(addon_path):
                shutil.copytree(addon, addon_path, symlinks=True)

        # remove the temporary directory, if any
        if tmpdir:
            shutil.rmtree(tmpdir)

    def _addon_details(self, addon_path):
        """
        Returns a dictionary of details about the addon.

        :param addon_path: path to the add-on directory or XPI

        Returns::

            {'id':      u'rainbow@colors.org', # id of the addon
             'version': u'1.4',                # version of the addon
             'name':    u'Rainbow',            # name of the addon
             'unpack':  False }                # whether to unpack the addon
        """

        details = {
            'id': None,
            'unpack': False,
            'name': None,
            'version': None
        }

        def get_namespace_id(doc, url):
            attributes = doc.documentElement.attributes
            namespace = ""
            for i in range(attributes.length):
                if attributes.item(i).value == url:
                    if ":" in attributes.item(i).name:
                        # If the namespace is not the default one remove 'xlmns:'
                        namespace = attributes.item(i).name.split(':')[1] + ":"
                        break
            return namespace

        def get_text(element):
            """Retrieve the text value of a given node"""
            rc = []
            for node in element.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc).strip()

        if not os.path.exists(addon_path):
            raise IOError('Add-on path does not exist: %s' % addon_path)

        try:
            if zipfile.is_zipfile(addon_path):
                # Bug 944361 - We cannot use 'with' together with zipFile because
                # it will cause an exception thrown in Python 2.6.
                try:
                    compressed_file = zipfile.ZipFile(addon_path, 'r')
                    manifest = compressed_file.read('install.rdf')
                finally:
                    compressed_file.close()
            elif os.path.isdir(addon_path):
                with open(os.path.join(addon_path, 'install.rdf'), 'r') as f:
                    manifest = f.read()
            else:
                raise IOError('Add-on path is neither an XPI nor a directory: %s' % addon_path)
        except (IOError, KeyError) as e:
            raise AddonFormatError(str(e), sys.exc_info()[2])

        try:
            doc = minidom.parseString(manifest)

            # Get the namespaces abbreviations
            em = get_namespace_id(doc, 'http://www.mozilla.org/2004/em-rdf#')
            rdf = get_namespace_id(doc, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

            description = doc.getElementsByTagName(rdf + 'Description').item(0)
            if description is None:
                description = doc.getElementsByTagName('Description').item(0)
            for node in description.childNodes:
                # Remove the namespace prefix from the tag for comparison
                entry = node.nodeName.replace(em, "")
                if entry in details.keys():
                    details.update({entry: get_text(node)})
            if details.get('id') is None:
                for i in range(description.attributes.length):
                    attribute = description.attributes.item(i)
                    if attribute.name == em + 'id':
                        details.update({'id': attribute.value})
        except Exception as e:
            raise AddonFormatError(str(e), sys.exc_info()[2])

        # turn unpack into a true/false value
        if isinstance(details['unpack'], str):
            details['unpack'] = details['unpack'].lower() == 'true'

        # If no ID is set, the add-on is invalid
        if details.get('id') is None:
            raise AddonFormatError('Add-on id could not be found.')

        return details
