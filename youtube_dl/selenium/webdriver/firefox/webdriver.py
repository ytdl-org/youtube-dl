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
import warnings

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

try:
    basestring
except NameError:  # Python 3.x
    basestring = str

import shutil
import socket
import sys
from contextlib import contextmanager

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

from .extension_connection import ExtensionConnection
from .firefox_binary import FirefoxBinary
from .firefox_profile import FirefoxProfile
from .options import Options
from .remote_connection import FirefoxRemoteConnection
from .service import Service
from .webelement import FirefoxWebElement


class WebDriver(RemoteWebDriver):

    # There is no native event support on Mac
    NATIVE_EVENTS_ALLOWED = sys.platform != "darwin"

    CONTEXT_CHROME = "chrome"
    CONTEXT_CONTENT = "content"

    _web_element_cls = FirefoxWebElement

    def __init__(self, firefox_profile=None, firefox_binary=None,
                 timeout=30, capabilities=None, proxy=None,
                 executable_path="geckodriver", options=None,
                 log_path="geckodriver.log", firefox_options=None,
                 service_args=None):
        """Starts a new local session of Firefox.

        Based on the combination and specificity of the various keyword
        arguments, a capabilities dictionary will be constructed that
        is passed to the remote end.

        The keyword arguments given to this constructor are helpers to
        more easily allow Firefox WebDriver sessions to be customised
        with different options.  They are mapped on to a capabilities
        dictionary that is passed on to the remote end.

        As some of the options, such as `firefox_profile` and
        `options.profile` are mutually exclusive, precedence is
        given from how specific the setting is.  `capabilities` is the
        least specific keyword argument, followed by `options`,
        followed by `firefox_binary` and `firefox_profile`.

        In practice this means that if `firefox_profile` and
        `options.profile` are both set, the selected profile
        instance will always come from the most specific variable.
        In this case that would be `firefox_profile`.  This will result in
        `options.profile` to be ignored because it is considered
        a less specific setting than the top-level `firefox_profile`
        keyword argument.  Similarily, if you had specified a
        `capabilities["moz:firefoxOptions"]["profile"]` Base64 string,
        this would rank below `options.profile`.

        :param firefox_profile: Instance of ``FirefoxProfile`` object
            or a string.  If undefined, a fresh profile will be created
            in a temporary location on the system.
        :param firefox_binary: Instance of ``FirefoxBinary`` or full
            path to the Firefox binary.  If undefined, the system default
            Firefox installation will  be used.
        :param timeout: Time to wait for Firefox to launch when using
            the extension connection.
        :param capabilities: Dictionary of desired capabilities.
        :param proxy: The proxy settings to us when communicating with
            Firefox via the extension connection.
        :param executable_path: Full path to override which geckodriver
            binary to use for Firefox 47.0.1 and greater, which
            defaults to picking up the binary from the system path.
        :param options: Instance of ``options.Options``.
        :param log_path: Where to log information from the driver.

        """
        if firefox_options:
            warnings.warn('use options instead of firefox_options', DeprecationWarning)
            options = firefox_options
        self.binary = None
        self.profile = None
        self.service = None

        if capabilities is None:
            capabilities = DesiredCapabilities.FIREFOX.copy()
        if options is None:
            options = Options()

        capabilities = dict(capabilities)

        if capabilities.get("binary"):
            self.binary = capabilities["binary"]

        # options overrides capabilities
        if options is not None:
            if options.binary is not None:
                self.binary = options.binary
            if options.profile is not None:
                self.profile = options.profile

        # firefox_binary and firefox_profile
        # override options
        if firefox_binary is not None:
            if isinstance(firefox_binary, basestring):
                firefox_binary = FirefoxBinary(firefox_binary)
            self.binary = firefox_binary
            options.binary = firefox_binary
        if firefox_profile is not None:
            if isinstance(firefox_profile, basestring):
                firefox_profile = FirefoxProfile(firefox_profile)
            self.profile = firefox_profile
            options.profile = firefox_profile

        # W3C remote
        # TODO(ato): Perform conformance negotiation

        if capabilities.get("marionette"):
            capabilities.pop("marionette")
            self.service = Service(
                executable_path,
                service_args=service_args,
                log_path=log_path)
            self.service.start()

            capabilities.update(options.to_capabilities())

            executor = FirefoxRemoteConnection(
                remote_server_addr=self.service.service_url)
            RemoteWebDriver.__init__(
                self,
                command_executor=executor,
                desired_capabilities=capabilities,
                keep_alive=True)

        # Selenium remote
        else:
            if self.binary is None:
                self.binary = FirefoxBinary()
            if self.profile is None:
                self.profile = FirefoxProfile()

            # disable native events if globally disabled
            self.profile.native_events_enabled = (
                self.NATIVE_EVENTS_ALLOWED and self.profile.native_events_enabled)

            if proxy is not None:
                proxy.add_to_capabilities(capabilities)

            executor = ExtensionConnection("127.0.0.1", self.profile,
                                           self.binary, timeout)
            RemoteWebDriver.__init__(
                self,
                command_executor=executor,
                desired_capabilities=capabilities,
                keep_alive=True)

        self._is_remote = False

    def quit(self):
        """Quits the driver and close every associated window."""
        try:
            RemoteWebDriver.quit(self)
        except (http_client.BadStatusLine, socket.error):
            # Happens if Firefox shutsdown before we've read the response from
            # the socket.
            pass

        if self.w3c:
            self.service.stop()
        else:
            self.binary.kill()

        if self.profile is not None:
            try:
                shutil.rmtree(self.profile.path)
                if self.profile.tempfolder is not None:
                    shutil.rmtree(self.profile.tempfolder)
            except Exception as e:
                print(str(e))

    @property
    def firefox_profile(self):
        return self.profile

    # Extension commands:

    def set_context(self, context):
        self.execute("SET_CONTEXT", {"context": context})

    @contextmanager
    def context(self, context):
        """Sets the context that Selenium commands are running in using
        a `with` statement. The state of the context on the server is
        saved before entering the block, and restored upon exiting it.

        :param context: Context, may be one of the class properties
            `CONTEXT_CHROME` or `CONTEXT_CONTENT`.

        Usage example::

            with selenium.context(selenium.CONTEXT_CHROME):
                # chrome scope
                ... do stuff ...
        """
        initial_context = self.execute('GET_CONTEXT').pop('value')
        self.set_context(context)
        try:
            yield
        finally:
            self.set_context(initial_context)

    def install_addon(self, path, temporary=None):
        """
        Installs Firefox addon.

        Returns identifier of installed addon. This identifier can later
        be used to uninstall addon.

        :param path: Absolute path to the addon that will be installed.

        :Usage:
            driver.install_addon('/path/to/firebug.xpi')
        """
        payload = {"path": path}
        if temporary is not None:
            payload["temporary"] = temporary
        return self.execute("INSTALL_ADDON", payload)["value"]

    def uninstall_addon(self, identifier):
        """
        Uninstalls Firefox addon using its identifier.

        :Usage:
            driver.uninstall_addon('addon@foo.com')
        """
        self.execute("UNINSTALL_ADDON", {"id": identifier})
