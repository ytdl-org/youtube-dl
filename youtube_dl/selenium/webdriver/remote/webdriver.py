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

"""The WebDriver implementation."""

import base64
import copy
import warnings
from contextlib import contextmanager

from .command import Command
from .webelement import WebElement
from .remote_connection import RemoteConnection
from .errorhandler import ErrorHandler
from .switch_to import SwitchTo
from .mobile import Mobile
from .file_detector import FileDetector, LocalFileDetector
from selenium.common.exceptions import (InvalidArgumentException,
                                        WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.html5.application_cache import ApplicationCache

try:
    str = basestring
except NameError:
    pass


_W3C_CAPABILITY_NAMES = frozenset([
    'acceptInsecureCerts',
    'browserName',
    'browserVersion',
    'platformName',
    'pageLoadStrategy',
    'proxy',
    'setWindowRect',
    'timeouts',
    'unhandledPromptBehavior',
])

_OSS_W3C_CONVERSION = {
    'acceptSslCerts': 'acceptInsecureCerts',
    'version': 'browserVersion',
    'platform': 'platformName'
}


def _make_w3c_caps(caps):
    """Makes a W3C alwaysMatch capabilities object.

    Filters out capability names that are not in the W3C spec. Spec-compliant
    drivers will reject requests containing unknown capability names.

    Moves the Firefox profile, if present, from the old location to the new Firefox
    options object.

    :Args:
     - caps - A dictionary of capabilities requested by the caller.
    """
    caps = copy.deepcopy(caps)
    profile = caps.get('firefox_profile')
    always_match = {}
    if caps.get('proxy') and caps['proxy'].get('proxyType'):
        caps['proxy']['proxyType'] = caps['proxy']['proxyType'].lower()
    for k, v in caps.items():
        if v and k in _OSS_W3C_CONVERSION:
            always_match[_OSS_W3C_CONVERSION[k]] = v.lower() if k == 'platform' else v
        if k in _W3C_CAPABILITY_NAMES or ':' in k:
            always_match[k] = v
    if profile:
        moz_opts = always_match.get('moz:firefoxOptions', {})
        # If it's already present, assume the caller did that intentionally.
        if 'profile' not in moz_opts:
            # Don't mutate the original capabilities.
            new_opts = copy.deepcopy(moz_opts)
            new_opts['profile'] = profile
            always_match['moz:firefoxOptions'] = new_opts
    return {"firstMatch": [{}], "alwaysMatch": always_match}


class WebDriver(object):
    """
    Controls a browser by sending commands to a remote server.
    This server is expected to be running the WebDriver wire protocol
    as defined at
    https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol

    :Attributes:
     - session_id - String ID of the browser session started and controlled by this WebDriver.
     - capabilities - Dictionaty of effective capabilities of this browser session as returned
         by the remote server. See https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities
     - command_executor - remote_connection.RemoteConnection object used to execute commands.
     - error_handler - errorhandler.ErrorHandler object used to handle errors.
    """

    _web_element_cls = WebElement

    def __init__(self, command_executor='http://127.0.0.1:4444/wd/hub',
                 desired_capabilities=None, browser_profile=None, proxy=None,
                 keep_alive=False, file_detector=None, options=None):
        """
        Create a new driver that will issue commands using the wire protocol.

        :Args:
         - command_executor - Either a string representing URL of the remote server or a custom
             remote_connection.RemoteConnection object. Defaults to 'http://127.0.0.1:4444/wd/hub'.
         - desired_capabilities - A dictionary of capabilities to request when
             starting the browser session. Required parameter.
         - browser_profile - A selenium.webdriver.firefox.firefox_profile.FirefoxProfile object.
             Only used if Firefox is requested. Optional.
         - proxy - A selenium.webdriver.common.proxy.Proxy object. The browser session will
             be started with given proxy settings, if possible. Optional.
         - keep_alive - Whether to configure remote_connection.RemoteConnection to use
             HTTP keep-alive. Defaults to False.
         - file_detector - Pass custom file detector object during instantiation. If None,
             then default LocalFileDetector() will be used.
         - options - instance of a driver options.Options class
        """
        if desired_capabilities is None:
            raise WebDriverException("Desired Capabilities can't be None")
        if not isinstance(desired_capabilities, dict):
            raise WebDriverException("Desired Capabilities must be a dictionary")
        if proxy is not None:
            warnings.warn("Please use FirefoxOptions to set proxy",
                          DeprecationWarning)
            proxy.add_to_capabilities(desired_capabilities)
        if options is not None:
            desired_capabilities.update(options.to_capabilities())
        self.command_executor = command_executor
        if type(self.command_executor) is bytes or isinstance(self.command_executor, str):
            self.command_executor = RemoteConnection(command_executor, keep_alive=keep_alive)
        self._is_remote = True
        self.session_id = None
        self.capabilities = {}
        self.error_handler = ErrorHandler()
        self.start_client()
        if browser_profile is not None:
            warnings.warn("Please use FirefoxOptions to set browser profile",
                          DeprecationWarning)
        self.start_session(desired_capabilities, browser_profile)
        self._switch_to = SwitchTo(self)
        self._mobile = Mobile(self)
        self.file_detector = file_detector or LocalFileDetector()

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} (session="{1}")>'.format(
            type(self), self.session_id)

    @contextmanager
    def file_detector_context(self, file_detector_class, *args, **kwargs):
        """
        Overrides the current file detector (if necessary) in limited context.
        Ensures the original file detector is set afterwards.

        Example:

        with webdriver.file_detector_context(UselessFileDetector):
            someinput.send_keys('/etc/hosts')

        :Args:
         - file_detector_class - Class of the desired file detector. If the class is different
             from the current file_detector, then the class is instantiated with args and kwargs
             and used as a file detector during the duration of the context manager.
         - args - Optional arguments that get passed to the file detector class during
             instantiation.
         - kwargs - Keyword arguments, passed the same way as args.
        """
        last_detector = None
        if not isinstance(self.file_detector, file_detector_class):
            last_detector = self.file_detector
            self.file_detector = file_detector_class(*args, **kwargs)
        try:
            yield
        finally:
            if last_detector is not None:
                self.file_detector = last_detector

    @property
    def mobile(self):
        return self._mobile

    @property
    def name(self):
        """Returns the name of the underlying browser for this instance.

        :Usage:
            name = driver.name
        """
        if 'browserName' in self.capabilities:
            return self.capabilities['browserName']
        else:
            raise KeyError('browserName not specified in session capabilities')

    def start_client(self):
        """
        Called before starting a new session. This method may be overridden
        to define custom startup behavior.
        """
        pass

    def stop_client(self):
        """
        Called after executing a quit command. This method may be overridden
        to define custom shutdown behavior.
        """
        pass

    def start_session(self, capabilities, browser_profile=None):
        """
        Creates a new session with the desired capabilities.

        :Args:
         - browser_name - The name of the browser to request.
         - version - Which browser version to request.
         - platform - Which platform to request the browser on.
         - javascript_enabled - Whether the new session should support JavaScript.
         - browser_profile - A selenium.webdriver.firefox.firefox_profile.FirefoxProfile object. Only used if Firefox is requested.
        """
        if not isinstance(capabilities, dict):
            raise InvalidArgumentException("Capabilities must be a dictionary")
        if browser_profile:
            if "moz:firefoxOptions" in capabilities:
                capabilities["moz:firefoxOptions"]["profile"] = browser_profile.encoded
            else:
                capabilities.update({'firefox_profile': browser_profile.encoded})
        w3c_caps = _make_w3c_caps(capabilities)
        parameters = {"capabilities": w3c_caps,
                      "desiredCapabilities": capabilities}
        response = self.execute(Command.NEW_SESSION, parameters)
        if 'sessionId' not in response:
            response = response['value']
        self.session_id = response['sessionId']
        self.capabilities = response.get('value')

        # if capabilities is none we are probably speaking to
        # a W3C endpoint
        if self.capabilities is None:
            self.capabilities = response.get('capabilities')

        # Double check to see if we have a W3C Compliant browser
        self.w3c = response.get('status') is None
        self.command_executor.w3c = self.w3c

    def _wrap_value(self, value):
        if isinstance(value, dict):
            converted = {}
            for key, val in value.items():
                converted[key] = self._wrap_value(val)
            return converted
        elif isinstance(value, self._web_element_cls):
            return {'ELEMENT': value.id, 'element-6066-11e4-a52e-4f735466cecf': value.id}
        elif isinstance(value, list):
            return list(self._wrap_value(item) for item in value)
        else:
            return value

    def create_web_element(self, element_id):
        """Creates a web element with the specified `element_id`."""
        return self._web_element_cls(self, element_id, w3c=self.w3c)

    def _unwrap_value(self, value):
        if isinstance(value, dict):
            if 'ELEMENT' in value or 'element-6066-11e4-a52e-4f735466cecf' in value:
                wrapped_id = value.get('ELEMENT', None)
                if wrapped_id:
                    return self.create_web_element(value['ELEMENT'])
                else:
                    return self.create_web_element(value['element-6066-11e4-a52e-4f735466cecf'])
            else:
                for key, val in value.items():
                    value[key] = self._unwrap_value(val)
                return value
        elif isinstance(value, list):
            return list(self._unwrap_value(item) for item in value)
        else:
            return value

    def execute(self, driver_command, params=None):
        """
        Sends a command to be executed by a command.CommandExecutor.

        :Args:
         - driver_command: The name of the command to execute as a string.
         - params: A dictionary of named parameters to send with the command.

        :Returns:
          The command's JSON response loaded into a dictionary object.
        """
        if self.session_id is not None:
            if not params:
                params = {'sessionId': self.session_id}
            elif 'sessionId' not in params:
                params['sessionId'] = self.session_id

        params = self._wrap_value(params)
        response = self.command_executor.execute(driver_command, params)
        if response:
            self.error_handler.check_response(response)
            response['value'] = self._unwrap_value(
                response.get('value', None))
            return response
        # If the server doesn't send a response, assume the command was
        # a success
        return {'success': 0, 'value': None, 'sessionId': self.session_id}

    def get(self, url):
        """
        Loads a web page in the current browser session.
        """
        self.execute(Command.GET, {'url': url})

    @property
    def title(self):
        """Returns the title of the current page.

        :Usage:
            title = driver.title
        """
        resp = self.execute(Command.GET_TITLE)
        return resp['value'] if resp['value'] is not None else ""

    def find_element_by_id(self, id_):
        """Finds an element by id.

        :Args:
         - id\_ - The id of the element to be found.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_id('foo')
        """
        return self.find_element(by=By.ID, value=id_)

    def find_elements_by_id(self, id_):
        """
        Finds multiple elements by id.

        :Args:
         - id\_ - The id of the elements to be found.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_id('foo')
        """
        return self.find_elements(by=By.ID, value=id_)

    def find_element_by_xpath(self, xpath):
        """
        Finds an element by xpath.

        :Args:
         - xpath - The xpath locator of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_xpath('//div/td[1]')
        """
        return self.find_element(by=By.XPATH, value=xpath)

    def find_elements_by_xpath(self, xpath):
        """
        Finds multiple elements by xpath.

        :Args:
         - xpath - The xpath locator of the elements to be found.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_xpath("//div[contains(@class, 'foo')]")
        """
        return self.find_elements(by=By.XPATH, value=xpath)

    def find_element_by_link_text(self, link_text):
        """
        Finds an element by link text.

        :Args:
         - link_text: The text of the element to be found.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_link_text('Sign In')
        """
        return self.find_element(by=By.LINK_TEXT, value=link_text)

    def find_elements_by_link_text(self, text):
        """
        Finds elements by link text.

        :Args:
         - link_text: The text of the elements to be found.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = driver.find_elements_by_link_text('Sign In')
        """
        return self.find_elements(by=By.LINK_TEXT, value=text)

    def find_element_by_partial_link_text(self, link_text):
        """
        Finds an element by a partial match of its link text.

        :Args:
         - link_text: The text of the element to partially match on.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_partial_link_text('Sign')
        """
        return self.find_element(by=By.PARTIAL_LINK_TEXT, value=link_text)

    def find_elements_by_partial_link_text(self, link_text):
        """
        Finds elements by a partial match of their link text.

        :Args:
         - link_text: The text of the element to partial match on.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = driver.find_elements_by_partial_link_text('Sign')
        """
        return self.find_elements(by=By.PARTIAL_LINK_TEXT, value=link_text)

    def find_element_by_name(self, name):
        """
        Finds an element by name.

        :Args:
         - name: The name of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_name('foo')
        """
        return self.find_element(by=By.NAME, value=name)

    def find_elements_by_name(self, name):
        """
        Finds elements by name.

        :Args:
         - name: The name of the elements to find.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = driver.find_elements_by_name('foo')
        """
        return self.find_elements(by=By.NAME, value=name)

    def find_element_by_tag_name(self, name):
        """
        Finds an element by tag name.

        :Args:
         - name - name of html tag (eg: h1, a, span)

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_tag_name('h1')
        """
        return self.find_element(by=By.TAG_NAME, value=name)

    def find_elements_by_tag_name(self, name):
        """
        Finds elements by tag name.

        :Args:
         - name - name of html tag (eg: h1, a, span)

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_tag_name('h1')
        """
        return self.find_elements(by=By.TAG_NAME, value=name)

    def find_element_by_class_name(self, name):
        """
        Finds an element by class name.

        :Args:
         - name: The class name of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_class_name('foo')
        """
        return self.find_element(by=By.CLASS_NAME, value=name)

    def find_elements_by_class_name(self, name):
        """
        Finds elements by class name.

        :Args:
         - name: The class name of the elements to find.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_class_name('foo')
        """
        return self.find_elements(by=By.CLASS_NAME, value=name)

    def find_element_by_css_selector(self, css_selector):
        """
        Finds an element by css selector.

        :Args:
         - css_selector - CSS selector string, ex: 'a.nav#home'

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_css_selector('#foo')
        """
        return self.find_element(by=By.CSS_SELECTOR, value=css_selector)

    def find_elements_by_css_selector(self, css_selector):
        """
        Finds elements by css selector.

        :Args:
         - css_selector - CSS selector string, ex: 'a.nav#home'

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_css_selector('.foo')
        """
        return self.find_elements(by=By.CSS_SELECTOR, value=css_selector)

    def execute_script(self, script, *args):
        """
        Synchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \*args: Any applicable arguments for your JavaScript.

        :Usage:
            driver.execute_script('return document.title;')
        """
        converted_args = list(args)
        command = None
        if self.w3c:
            command = Command.W3C_EXECUTE_SCRIPT
        else:
            command = Command.EXECUTE_SCRIPT

        return self.execute(command, {
            'script': script,
            'args': converted_args})['value']

    def execute_async_script(self, script, *args):
        """
        Asynchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \*args: Any applicable arguments for your JavaScript.

        :Usage:
            script = "var callback = arguments[arguments.length - 1]; " \
                     "window.setTimeout(function(){ callback('timeout') }, 3000);"
            driver.execute_async_script(script)
        """
        converted_args = list(args)
        if self.w3c:
            command = Command.W3C_EXECUTE_SCRIPT_ASYNC
        else:
            command = Command.EXECUTE_ASYNC_SCRIPT

        return self.execute(command, {
            'script': script,
            'args': converted_args})['value']

    @property
    def current_url(self):
        """
        Gets the URL of the current page.

        :Usage:
            driver.current_url
        """
        return self.execute(Command.GET_CURRENT_URL)['value']

    @property
    def page_source(self):
        """
        Gets the source of the current page.

        :Usage:
            driver.page_source
        """
        return self.execute(Command.GET_PAGE_SOURCE)['value']

    def close(self):
        """
        Closes the current window.

        :Usage:
            driver.close()
        """
        self.execute(Command.CLOSE)

    def quit(self):
        """
        Quits the driver and closes every associated window.

        :Usage:
            driver.quit()
        """
        try:
            self.execute(Command.QUIT)
        finally:
            self.stop_client()

    @property
    def current_window_handle(self):
        """
        Returns the handle of the current window.

        :Usage:
            driver.current_window_handle
        """
        if self.w3c:
            return self.execute(Command.W3C_GET_CURRENT_WINDOW_HANDLE)['value']
        else:
            return self.execute(Command.GET_CURRENT_WINDOW_HANDLE)['value']

    @property
    def window_handles(self):
        """
        Returns the handles of all windows within the current session.

        :Usage:
            driver.window_handles
        """
        if self.w3c:
            return self.execute(Command.W3C_GET_WINDOW_HANDLES)['value']
        else:
            return self.execute(Command.GET_WINDOW_HANDLES)['value']

    def maximize_window(self):
        """
        Maximizes the current window that webdriver is using
        """
        command = Command.MAXIMIZE_WINDOW
        if self.w3c:
            command = Command.W3C_MAXIMIZE_WINDOW
        self.execute(command, {"windowHandle": "current"})

    def fullscreen_window(self):
        """
        Invokes the window manager-specific 'full screen' operation
        """
        self.execute(Command.FULLSCREEN_WINDOW)

    def minimize_window(self):
        """
        Invokes the window manager-specific 'minimize' operation
        """
        self.execute(Command.MINIMIZE_WINDOW)

    @property
    def switch_to(self):
        """
        :Returns:
            - SwitchTo: an object containing all options to switch focus into

        :Usage:
            element = driver.switch_to.active_element
            alert = driver.switch_to.alert
            driver.switch_to.default_content()
            driver.switch_to.frame('frame_name')
            driver.switch_to.frame(1)
            driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
            driver.switch_to.parent_frame()
            driver.switch_to.window('main')
        """
        return self._switch_to

    # Target Locators
    def switch_to_active_element(self):
        """ Deprecated use driver.switch_to.active_element
        """
        warnings.warn("use driver.switch_to.active_element instead", DeprecationWarning)
        return self._switch_to.active_element

    def switch_to_window(self, window_name):
        """ Deprecated use driver.switch_to.window
        """
        warnings.warn("use driver.switch_to.window instead", DeprecationWarning)
        self._switch_to.window(window_name)

    def switch_to_frame(self, frame_reference):
        """ Deprecated use driver.switch_to.frame
        """
        warnings.warn("use driver.switch_to.frame instead", DeprecationWarning)
        self._switch_to.frame(frame_reference)

    def switch_to_default_content(self):
        """ Deprecated use driver.switch_to.default_content
        """
        warnings.warn("use driver.switch_to.default_content instead", DeprecationWarning)
        self._switch_to.default_content()

    def switch_to_alert(self):
        """ Deprecated use driver.switch_to.alert
        """
        warnings.warn("use driver.switch_to.alert instead", DeprecationWarning)
        return self._switch_to.alert

    # Navigation
    def back(self):
        """
        Goes one step backward in the browser history.

        :Usage:
            driver.back()
        """
        self.execute(Command.GO_BACK)

    def forward(self):
        """
        Goes one step forward in the browser history.

        :Usage:
            driver.forward()
        """
        self.execute(Command.GO_FORWARD)

    def refresh(self):
        """
        Refreshes the current page.

        :Usage:
            driver.refresh()
        """
        self.execute(Command.REFRESH)

    # Options
    def get_cookies(self):
        """
        Returns a set of dictionaries, corresponding to cookies visible in the current session.

        :Usage:
            driver.get_cookies()
        """
        return self.execute(Command.GET_ALL_COOKIES)['value']

    def get_cookie(self, name):
        """
        Get a single cookie by name. Returns the cookie if found, None if not.

        :Usage:
            driver.get_cookie('my_cookie')
        """
        cookies = self.get_cookies()
        for cookie in cookies:
            if cookie['name'] == name:
                return cookie
        return None

    def delete_cookie(self, name):
        """
        Deletes a single cookie with the given name.

        :Usage:
            driver.delete_cookie('my_cookie')
        """
        self.execute(Command.DELETE_COOKIE, {'name': name})

    def delete_all_cookies(self):
        """
        Delete all cookies in the scope of the session.

        :Usage:
            driver.delete_all_cookies()
        """
        self.execute(Command.DELETE_ALL_COOKIES)

    def add_cookie(self, cookie_dict):
        """
        Adds a cookie to your current session.

        :Args:
         - cookie_dict: A dictionary object, with required keys - "name" and "value";
            optional keys - "path", "domain", "secure", "expiry"

        Usage:
            driver.add_cookie({'name' : 'foo', 'value' : 'bar'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/', 'secure':True})

        """
        self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})

    # Timeouts
    def implicitly_wait(self, time_to_wait):
        """
        Sets a sticky timeout to implicitly wait for an element to be found,
           or a command to complete. This method only needs to be called one
           time per session. To set the timeout for calls to
           execute_async_script, see set_script_timeout.

        :Args:
         - time_to_wait: Amount of time to wait (in seconds)

        :Usage:
            driver.implicitly_wait(30)
        """
        if self.w3c:
            self.execute(Command.SET_TIMEOUTS, {
                'implicit': int(float(time_to_wait) * 1000)})
        else:
            self.execute(Command.IMPLICIT_WAIT, {
                'ms': float(time_to_wait) * 1000})

    def set_script_timeout(self, time_to_wait):
        """
        Set the amount of time that the script should wait during an
           execute_async_script call before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait (in seconds)

        :Usage:
            driver.set_script_timeout(30)
        """
        if self.w3c:
            self.execute(Command.SET_TIMEOUTS, {
                'script': int(float(time_to_wait) * 1000)})
        else:
            self.execute(Command.SET_SCRIPT_TIMEOUT, {
                'ms': float(time_to_wait) * 1000})

    def set_page_load_timeout(self, time_to_wait):
        """
        Set the amount of time to wait for a page load to complete
           before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait

        :Usage:
            driver.set_page_load_timeout(30)
        """
        try:
            self.execute(Command.SET_TIMEOUTS, {
                'pageLoad': int(float(time_to_wait) * 1000)})
        except WebDriverException:
            self.execute(Command.SET_TIMEOUTS, {
                'ms': float(time_to_wait) * 1000,
                'type': 'page load'})

    def find_element(self, by=By.ID, value=None):
        """
        'Private' method used by the find_element_by_* methods.

        :Usage:
            Use the corresponding find_element_by_* instead of this.

        :rtype: WebElement
        """
        if self.w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value
        return self.execute(Command.FIND_ELEMENT, {
            'using': by,
            'value': value})['value']

    def find_elements(self, by=By.ID, value=None):
        """
        'Private' method used by the find_elements_by_* methods.

        :Usage:
            Use the corresponding find_elements_by_* instead of this.

        :rtype: list of WebElement
        """
        if self.w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        # Return empty list if driver returns null
        # See https://github.com/SeleniumHQ/selenium/issues/4555
        return self.execute(Command.FIND_ELEMENTS, {
            'using': by,
            'value': value})['value'] or []

    @property
    def desired_capabilities(self):
        """
        returns the drivers current desired capabilities being used
        """
        return self.capabilities

    def get_screenshot_as_file(self, filename):
        """
        Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            driver.get_screenshot_as_file('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)
        png = self.get_screenshot_as_png()
        try:
            with open(filename, 'wb') as f:
                f.write(png)
        except IOError:
            return False
        finally:
            del png
        return True

    def save_screenshot(self, filename):
        """
        Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            driver.save_screenshot('/Screenshots/foo.png')
        """
        return self.get_screenshot_as_file(filename)

    def get_screenshot_as_png(self):
        """
        Gets the screenshot of the current window as a binary data.

        :Usage:
            driver.get_screenshot_as_png()
        """
        return base64.b64decode(self.get_screenshot_as_base64().encode('ascii'))

    def get_screenshot_as_base64(self):
        """
        Gets the screenshot of the current window as a base64 encoded string
           which is useful in embedded images in HTML.

        :Usage:
            driver.get_screenshot_as_base64()
        """
        return self.execute(Command.SCREENSHOT)['value']

    def set_window_size(self, width, height, windowHandle='current'):
        """
        Sets the width and height of the current window. (window.resizeTo)

        :Args:
         - width: the width in pixels to set the window to
         - height: the height in pixels to set the window to

        :Usage:
            driver.set_window_size(800,600)
        """
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            self.set_window_rect(width=int(width), height=int(height))
        else:
            self.execute(Command.SET_WINDOW_SIZE, {
                'width': int(width),
                'height': int(height),
                'windowHandle': windowHandle})

    def get_window_size(self, windowHandle='current'):
        """
        Gets the width and height of the current window.

        :Usage:
            driver.get_window_size()
        """
        command = Command.GET_WINDOW_SIZE
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            size = self.get_window_rect()
        else:
            size = self.execute(command, {'windowHandle': windowHandle})

        if size.get('value', None) is not None:
            size = size['value']

        return {k: size[k] for k in ('width', 'height')}

    def set_window_position(self, x, y, windowHandle='current'):
        """
        Sets the x,y position of the current window. (window.moveTo)

        :Args:
         - x: the x-coordinate in pixels to set the window position
         - y: the y-coordinate in pixels to set the window position

        :Usage:
            driver.set_window_position(0,0)
        """
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            return self.set_window_rect(x=int(x), y=int(y))
        else:
            self.execute(Command.SET_WINDOW_POSITION,
                         {
                             'x': int(x),
                             'y': int(y),
                             'windowHandle': windowHandle
                         })

    def get_window_position(self, windowHandle='current'):
        """
        Gets the x,y position of the current window.

        :Usage:
            driver.get_window_position()
        """
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            position = self.get_window_rect()
        else:
            position = self.execute(Command.GET_WINDOW_POSITION,
                                    {'windowHandle': windowHandle})['value']

        return {k: position[k] for k in ('x', 'y')}

    def get_window_rect(self):
        """
        Gets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            driver.get_window_rect()
        """
        return self.execute(Command.GET_WINDOW_RECT)['value']

    def set_window_rect(self, x=None, y=None, width=None, height=None):
        """
        Sets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            driver.set_window_rect(x=10, y=10)
            driver.set_window_rect(width=100, height=200)
            driver.set_window_rect(x=10, y=10, width=100, height=200)
        """
        if (x is None and y is None) and (height is None and width is None):
            raise InvalidArgumentException("x and y or height and width need values")

        return self.execute(Command.SET_WINDOW_RECT, {"x": x, "y": y,
                                                      "width": width,
                                                      "height": height})['value']

    @property
    def file_detector(self):
        return self._file_detector

    @file_detector.setter
    def file_detector(self, detector):
        """
        Set the file detector to be used when sending keyboard input.
        By default, this is set to a file detector that does nothing.

        see FileDetector
        see LocalFileDetector
        see UselessFileDetector

        :Args:
         - detector: The detector to use. Must not be None.
        """
        if detector is None:
            raise WebDriverException("You may not set a file detector that is null")
        if not isinstance(detector, FileDetector):
            raise WebDriverException("Detector has to be instance of FileDetector")
        self._file_detector = detector

    @property
    def orientation(self):
        """
        Gets the current orientation of the device

        :Usage:
            orientation = driver.orientation
        """
        return self.execute(Command.GET_SCREEN_ORIENTATION)['value']

    @orientation.setter
    def orientation(self, value):
        """
        Sets the current orientation of the device

        :Args:
         - value: orientation to set it to.

        :Usage:
            driver.orientation = 'landscape'
        """
        allowed_values = ['LANDSCAPE', 'PORTRAIT']
        if value.upper() in allowed_values:
            self.execute(Command.SET_SCREEN_ORIENTATION, {'orientation': value})
        else:
            raise WebDriverException("You can only set the orientation to 'LANDSCAPE' and 'PORTRAIT'")

    @property
    def application_cache(self):
        """ Returns a ApplicationCache Object to interact with the browser app cache"""
        return ApplicationCache(self)

    @property
    def log_types(self):
        """
        Gets a list of the available log types

        :Usage:
            driver.log_types
        """
        return self.execute(Command.GET_AVAILABLE_LOG_TYPES)['value']

    def get_log(self, log_type):
        """
        Gets the log for a given log type

        :Args:
         - log_type: type of log that which will be returned

        :Usage:
            driver.get_log('browser')
            driver.get_log('driver')
            driver.get_log('client')
            driver.get_log('server')
        """
        return self.execute(Command.GET_LOG, {'type': log_type})['value']
