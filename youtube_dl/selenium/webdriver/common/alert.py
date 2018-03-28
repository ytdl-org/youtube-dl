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

"""
The Alert implementation.
"""

from selenium.webdriver.common.utils import keys_to_typing
from selenium.webdriver.remote.command import Command


class Alert(object):
    """
    Allows to work with alerts.

    Use this class to interact with alert prompts.  It contains methods for dismissing,
    accepting, inputting, and getting text from alert prompts.

    Accepting / Dismissing alert prompts::

        Alert(driver).accept()
        Alert(driver).dismiss()

    Inputting a value into an alert prompt:

        name_prompt = Alert(driver)
        name_prompt.send_keys("Willian Shakesphere")
        name_prompt.accept()


    Reading a the text of a prompt for verification:

        alert_text = Alert(driver).text
        self.assertEqual("Do you wish to quit?", alert_text)

    """

    def __init__(self, driver):
        """
        Creates a new Alert.

        :Args:
         - driver: The WebDriver instance which performs user actions.
        """
        self.driver = driver

    @property
    def text(self):
        """
        Gets the text of the Alert.
        """
        if self.driver.w3c:
            return self.driver.execute(Command.W3C_GET_ALERT_TEXT)["value"]
        else:
            return self.driver.execute(Command.GET_ALERT_TEXT)["value"]

    def dismiss(self):
        """
        Dismisses the alert available.
        """
        if self.driver.w3c:
            self.driver.execute(Command.W3C_DISMISS_ALERT)
        else:
            self.driver.execute(Command.DISMISS_ALERT)

    def accept(self):
        """
        Accepts the alert available.

        Usage::
        Alert(driver).accept() # Confirm a alert dialog.
        """
        if self.driver.w3c:
            self.driver.execute(Command.W3C_ACCEPT_ALERT)
        else:
            self.driver.execute(Command.ACCEPT_ALERT)

    def send_keys(self, keysToSend):
        """
        Send Keys to the Alert.

        :Args:
         - keysToSend: The text to be sent to Alert.


        """
        if self.driver.w3c:
            self.driver.execute(Command.W3C_SET_ALERT_VALUE, {'value': keys_to_typing(keysToSend),
                                                              'text': keysToSend})
        else:
            self.driver.execute(Command.SET_ALERT_VALUE, {'text': keysToSend})

    def authenticate(self, username, password):
        """
        Send the username / password to an Authenticated dialog (like with Basic HTTP Auth).
        Implicitly 'clicks ok'

        Usage::
        driver.switch_to.alert.authenticate('cheese', 'secretGouda')

        :Args:
         -username: string to be set in the username section of the dialog
         -password: string to be set in the password section of the dialog
        """
        self.driver.execute(
            Command.SET_ALERT_CREDENTIALS,
            {'username': username, 'password': password})
        self.accept()
