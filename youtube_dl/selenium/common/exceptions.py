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
Exceptions that may happen in all the webdriver code.
"""


class WebDriverException(Exception):
    """
    Base webdriver exception.
    """

    def __init__(self, msg=None, screen=None, stacktrace=None):
        self.msg = msg
        self.screen = screen
        self.stacktrace = stacktrace

    def __str__(self):
        exception_msg = "Message: %s\n" % self.msg
        if self.screen is not None:
            exception_msg += "Screenshot: available via screen\n"
        if self.stacktrace is not None:
            stacktrace = "\n".join(self.stacktrace)
            exception_msg += "Stacktrace:\n%s" % stacktrace
        return exception_msg


class ErrorInResponseException(WebDriverException):
    """
    Thrown when an error has occurred on the server side.

    This may happen when communicating with the firefox extension
    or the remote driver server.
    """
    def __init__(self, response, msg):
        WebDriverException.__init__(self, msg)
        self.response = response


class InvalidSwitchToTargetException(WebDriverException):
    """
    Thrown when frame or window target to be switched doesn't exist.
    """
    pass


class NoSuchFrameException(InvalidSwitchToTargetException):
    """
    Thrown when frame target to be switched doesn't exist.
    """
    pass


class NoSuchWindowException(InvalidSwitchToTargetException):
    """
    Thrown when window target to be switched doesn't exist.

    To find the current set of active window handles, you can get a list
    of the active window handles in the following way::

        print driver.window_handles

    """
    pass


class NoSuchElementException(WebDriverException):
    """
    Thrown when element could not be found.

    If you encounter this exception, you may want to check the following:
        * Check your selector used in your find_by...
        * Element may not yet be on the screen at the time of the find operation,
          (webpage is still loading) see selenium.webdriver.support.wait.WebDriverWait()
          for how to write a wait wrapper to wait for an element to appear.
    """
    pass


class NoSuchAttributeException(WebDriverException):
    """
    Thrown when the attribute of element could not be found.

    You may want to check if the attribute exists in the particular browser you are
    testing against.  Some browsers may have different property names for the same
    property.  (IE8's .innerText vs. Firefox .textContent)
    """
    pass


class StaleElementReferenceException(WebDriverException):
    """
    Thrown when a reference to an element is now "stale".

    Stale means the element no longer appears on the DOM of the page.


    Possible causes of StaleElementReferenceException include, but not limited to:
        * You are no longer on the same page, or the page may have refreshed since the element
          was located.
        * The element may have been removed and re-added to the screen, since it was located.
          Such as an element being relocated.
          This can happen typically with a javascript framework when values are updated and the
          node is rebuilt.
        * Element may have been inside an iframe or another context which was refreshed.
    """
    pass


class InvalidElementStateException(WebDriverException):
    """
    Thrown when a command could not be completed because the element is in an invalid state.

    This can be caused by attempting to clear an element that isn't both editable and resettable.
    """
    pass


class UnexpectedAlertPresentException(WebDriverException):
    """
    Thrown when an unexpected alert is appeared.

    Usually raised when when an expected modal is blocking webdriver form executing any
    more commands.
    """
    def __init__(self, msg=None, screen=None, stacktrace=None, alert_text=None):
        super(UnexpectedAlertPresentException, self).__init__(msg, screen, stacktrace)
        self.alert_text = alert_text

    def __str__(self):
        return "Alert Text: %s\n%s" % (self.alert_text, super(UnexpectedAlertPresentException, self).__str__())


class NoAlertPresentException(WebDriverException):
    """
    Thrown when switching to no presented alert.

    This can be caused by calling an operation on the Alert() class when an alert is
    not yet on the screen.
    """
    pass


class ElementNotVisibleException(InvalidElementStateException):
    """
    Thrown when an element is present on the DOM, but
    it is not visible, and so is not able to be interacted with.

    Most commonly encountered when trying to click or read text
    of an element that is hidden from view.
    """
    pass


class ElementNotInteractableException(InvalidElementStateException):
    """
    Thrown when an element is present in the DOM but interactions
    with that element will hit another element do to paint order
    """
    pass


class ElementNotSelectableException(InvalidElementStateException):
    """
    Thrown when trying to select an unselectable element.

    For example, selecting a 'script' element.
    """
    pass


class InvalidCookieDomainException(WebDriverException):
    """
    Thrown when attempting to add a cookie under a different domain
    than the current URL.
    """
    pass


class UnableToSetCookieException(WebDriverException):
    """
    Thrown when a driver fails to set a cookie.
    """
    pass


class RemoteDriverServerException(WebDriverException):
    """
    """
    pass


class TimeoutException(WebDriverException):
    """
    Thrown when a command does not complete in enough time.
    """
    pass


class MoveTargetOutOfBoundsException(WebDriverException):
    """
    Thrown when the target provided to the `ActionsChains` move()
    method is invalid, i.e. out of document.
    """
    pass


class UnexpectedTagNameException(WebDriverException):
    """
    Thrown when a support class did not get an expected web element.
    """
    pass


class InvalidSelectorException(NoSuchElementException):
    """
    Thrown when the selector which is used to find an element does not return
    a WebElement. Currently this only happens when the selector is an xpath
    expression and it is either syntactically invalid (i.e. it is not a
    xpath expression) or the expression does not select WebElements
    (e.g. "count(//input)").
    """
    pass


class ImeNotAvailableException(WebDriverException):
    """
    Thrown when IME support is not available. This exception is thrown for every IME-related
    method call if IME support is not available on the machine.
    """
    pass


class ImeActivationFailedException(WebDriverException):
    """
    Thrown when activating an IME engine has failed.
    """
    pass


class InvalidArgumentException(WebDriverException):
    """
    The arguments passed to a command are either invalid or malformed.
    """
    pass


class JavascriptException(WebDriverException):
    """
    An error occurred while executing JavaScript supplied by the user.
    """
    pass


class NoSuchCookieException(WebDriverException):
    """
    No cookie matching the given path name was found amongst the associated cookies of the
    current browsing context's active document.
    """
    pass


class ScreenshotException(WebDriverException):
    """
    A screen capture was made impossible.
    """
    pass


class ElementClickInterceptedException(WebDriverException):
    """
    The Element Click command could not be completed because the element receiving the events
    is obscuring the element that was requested clicked.
    """
    pass


class InsecureCertificateException(WebDriverException):
    """
    Navigation caused the user agent to hit a certificate warning, which is usually the result
    of an expired or invalid TLS certificate.
    """
    pass


class InvalidCoordinatesException(WebDriverException):
    """
    The coordinates provided to an interactions operation are invalid.
    """
    pass


class InvalidSessionIdException(WebDriverException):
    """
    Occurs if the given session id is not in the list of active sessions, meaning the session
    either does not exist or that it's not active.
    """
    pass


class SessionNotCreatedException(WebDriverException):
    """
    A new session could not be created.
    """
    pass


class UnknownMethodException(WebDriverException):
    """
    The requested command matched a known URL but did not match an method for that URL.
    """
    pass
