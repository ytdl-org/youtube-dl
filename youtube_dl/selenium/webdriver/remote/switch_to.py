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

from .command import Command
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, NoSuchFrameException, NoSuchWindowException

try:
    basestring
except NameError:
    basestring = str


class SwitchTo:
    def __init__(self, driver):
        self._driver = driver

    @property
    def active_element(self):
        """
        Returns the element with focus, or BODY if nothing has focus.

        :Usage:
            element = driver.switch_to.active_element
        """
        if self._driver.w3c:
            return self._driver.execute(Command.W3C_GET_ACTIVE_ELEMENT)['value']
        else:
            return self._driver.execute(Command.GET_ACTIVE_ELEMENT)['value']

    @property
    def alert(self):
        """
        Switches focus to an alert on the page.

        :Usage:
            alert = driver.switch_to.alert
        """
        alert = Alert(self._driver)
        alert.text
        return alert

    def default_content(self):
        """
        Switch focus to the default frame.

        :Usage:
            driver.switch_to.default_content()
        """
        self._driver.execute(Command.SWITCH_TO_FRAME, {'id': None})

    def frame(self, frame_reference):
        """
        Switches focus to the specified frame, by index, name, or webelement.

        :Args:
         - frame_reference: The name of the window to switch to, an integer representing the index,
                            or a webelement that is an (i)frame to switch to.

        :Usage:
            driver.switch_to.frame('frame_name')
            driver.switch_to.frame(1)
            driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
        """
        if isinstance(frame_reference, basestring) and self._driver.w3c:
            try:
                frame_reference = self._driver.find_element(By.ID, frame_reference)
            except NoSuchElementException:
                try:
                    frame_reference = self._driver.find_element(By.NAME, frame_reference)
                except NoSuchElementException:
                    raise NoSuchFrameException(frame_reference)

        self._driver.execute(Command.SWITCH_TO_FRAME, {'id': frame_reference})

    def parent_frame(self):
        """
        Switches focus to the parent context. If the current context is the top
        level browsing context, the context remains unchanged.

        :Usage:
            driver.switch_to.parent_frame()
        """
        self._driver.execute(Command.SWITCH_TO_PARENT_FRAME)

    def window(self, window_name):
        """
        Switches focus to the specified window.

        :Args:
         - window_name: The name or window handle of the window to switch to.

        :Usage:
            driver.switch_to.window('main')
        """
        if self._driver.w3c:
            self._w3c_window(window_name)
            return
        data = {'name': window_name}
        self._driver.execute(Command.SWITCH_TO_WINDOW, data)

    def _w3c_window(self, window_name):
        def send_handle(h):
            self._driver.execute(Command.SWITCH_TO_WINDOW, {'handle': h})

        try:
            # Try using it as a handle first.
            send_handle(window_name)
        except NoSuchWindowException as e:
            # Check every window to try to find the given window name.
            original_handle = self._driver.current_window_handle
            handles = self._driver.window_handles
            for handle in handles:
                send_handle(handle)
                current_name = self._driver.execute_script('return window.name')
                if window_name == current_name:
                    return
            send_handle(original_handle)
            raise e
