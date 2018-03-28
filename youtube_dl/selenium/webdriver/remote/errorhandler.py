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

from selenium.common.exceptions import (ElementClickInterceptedException,
                                        ElementNotInteractableException,
                                        ElementNotSelectableException,
                                        ElementNotVisibleException,
                                        ErrorInResponseException,
                                        InsecureCertificateException,
                                        InvalidCoordinatesException,
                                        InvalidElementStateException,
                                        InvalidSessionIdException,
                                        InvalidSelectorException,
                                        ImeNotAvailableException,
                                        ImeActivationFailedException,
                                        InvalidArgumentException,
                                        InvalidCookieDomainException,
                                        JavascriptException,
                                        MoveTargetOutOfBoundsException,
                                        NoSuchCookieException,
                                        NoSuchElementException,
                                        NoSuchFrameException,
                                        NoSuchWindowException,
                                        NoAlertPresentException,
                                        ScreenshotException,
                                        SessionNotCreatedException,
                                        StaleElementReferenceException,
                                        TimeoutException,
                                        UnableToSetCookieException,
                                        UnexpectedAlertPresentException,
                                        UnknownMethodException,
                                        WebDriverException)

try:
    basestring
except NameError:  # Python 3.x
    basestring = str


class ErrorCode(object):
    """
    Error codes defined in the WebDriver wire protocol.
    """
    # Keep in sync with org.openqa.selenium.remote.ErrorCodes and errorcodes.h
    SUCCESS = 0
    NO_SUCH_ELEMENT = [7, 'no such element']
    NO_SUCH_FRAME = [8, 'no such frame']
    UNKNOWN_COMMAND = [9, 'unknown command']
    STALE_ELEMENT_REFERENCE = [10, 'stale element reference']
    ELEMENT_NOT_VISIBLE = [11, 'element not visible']
    INVALID_ELEMENT_STATE = [12, 'invalid element state']
    UNKNOWN_ERROR = [13, 'unknown error']
    ELEMENT_IS_NOT_SELECTABLE = [15, 'element not selectable']
    JAVASCRIPT_ERROR = [17, 'javascript error']
    XPATH_LOOKUP_ERROR = [19, 'invalid selector']
    TIMEOUT = [21, 'timeout']
    NO_SUCH_WINDOW = [23, 'no such window']
    INVALID_COOKIE_DOMAIN = [24, 'invalid cookie domain']
    UNABLE_TO_SET_COOKIE = [25, 'unable to set cookie']
    UNEXPECTED_ALERT_OPEN = [26, 'unexpected alert open']
    NO_ALERT_OPEN = [27, 'no such alert']
    SCRIPT_TIMEOUT = [28, 'script timeout']
    INVALID_ELEMENT_COORDINATES = [29, 'invalid element coordinates']
    IME_NOT_AVAILABLE = [30, 'ime not available']
    IME_ENGINE_ACTIVATION_FAILED = [31, 'ime engine activation failed']
    INVALID_SELECTOR = [32, 'invalid selector']
    SESSION_NOT_CREATED = [33, 'session not created']
    MOVE_TARGET_OUT_OF_BOUNDS = [34, 'move target out of bounds']
    INVALID_XPATH_SELECTOR = [51, 'invalid selector']
    INVALID_XPATH_SELECTOR_RETURN_TYPER = [52, 'invalid selector']

    ELEMENT_NOT_INTERACTABLE = [60, 'element not interactable']
    INSECURE_CERTIFICATE = ['insecure certificate']
    INVALID_ARGUMENT = [61, 'invalid argument']
    INVALID_COORDINATES = ['invalid coordinates']
    INVALID_SESSION_ID = ['invalid session id']
    NO_SUCH_COOKIE = [62, 'no such cookie']
    UNABLE_TO_CAPTURE_SCREEN = [63, 'unable to capture screen']
    ELEMENT_CLICK_INTERCEPTED = [64, 'element click intercepted']
    UNKNOWN_METHOD = ['unknown method exception']

    METHOD_NOT_ALLOWED = [405, 'unsupported operation']


class ErrorHandler(object):
    """
    Handles errors returned by the WebDriver server.
    """
    def check_response(self, response):
        """
        Checks that a JSON response from the WebDriver does not have an error.

        :Args:
         - response - The JSON response from the WebDriver server as a dictionary
           object.

        :Raises: If the response contains an error message.
        """
        status = response.get('status', None)
        if status is None or status == ErrorCode.SUCCESS:
            return
        value = None
        message = response.get("message", "")
        screen = response.get("screen", "")
        stacktrace = None
        if isinstance(status, int):
            value_json = response.get('value', None)
            if value_json and isinstance(value_json, basestring):
                import json
                try:
                    value = json.loads(value_json)
                    if len(value.keys()) == 1:
                        value = value['value']
                    status = value.get('error', None)
                    if status is None:
                        status = value["status"]
                        message = value["value"]
                        if not isinstance(message, basestring):
                            value = message
                            message = message.get('message')
                    else:
                        message = value.get('message', None)
                except ValueError:
                    pass

        exception_class = ErrorInResponseException
        if status in ErrorCode.NO_SUCH_ELEMENT:
            exception_class = NoSuchElementException
        elif status in ErrorCode.NO_SUCH_FRAME:
            exception_class = NoSuchFrameException
        elif status in ErrorCode.NO_SUCH_WINDOW:
            exception_class = NoSuchWindowException
        elif status in ErrorCode.STALE_ELEMENT_REFERENCE:
            exception_class = StaleElementReferenceException
        elif status in ErrorCode.ELEMENT_NOT_VISIBLE:
            exception_class = ElementNotVisibleException
        elif status in ErrorCode.INVALID_ELEMENT_STATE:
            exception_class = InvalidElementStateException
        elif status in ErrorCode.INVALID_SELECTOR \
                or status in ErrorCode.INVALID_XPATH_SELECTOR \
                or status in ErrorCode.INVALID_XPATH_SELECTOR_RETURN_TYPER:
            exception_class = InvalidSelectorException
        elif status in ErrorCode.ELEMENT_IS_NOT_SELECTABLE:
            exception_class = ElementNotSelectableException
        elif status in ErrorCode.ELEMENT_NOT_INTERACTABLE:
            exception_class = ElementNotInteractableException
        elif status in ErrorCode.INVALID_COOKIE_DOMAIN:
            exception_class = InvalidCookieDomainException
        elif status in ErrorCode.UNABLE_TO_SET_COOKIE:
            exception_class = UnableToSetCookieException
        elif status in ErrorCode.TIMEOUT:
            exception_class = TimeoutException
        elif status in ErrorCode.SCRIPT_TIMEOUT:
            exception_class = TimeoutException
        elif status in ErrorCode.UNKNOWN_ERROR:
            exception_class = WebDriverException
        elif status in ErrorCode.UNEXPECTED_ALERT_OPEN:
            exception_class = UnexpectedAlertPresentException
        elif status in ErrorCode.NO_ALERT_OPEN:
            exception_class = NoAlertPresentException
        elif status in ErrorCode.IME_NOT_AVAILABLE:
            exception_class = ImeNotAvailableException
        elif status in ErrorCode.IME_ENGINE_ACTIVATION_FAILED:
            exception_class = ImeActivationFailedException
        elif status in ErrorCode.MOVE_TARGET_OUT_OF_BOUNDS:
            exception_class = MoveTargetOutOfBoundsException
        elif status in ErrorCode.JAVASCRIPT_ERROR:
            exception_class = JavascriptException
        elif status in ErrorCode.SESSION_NOT_CREATED:
            exception_class = SessionNotCreatedException
        elif status in ErrorCode.INVALID_ARGUMENT:
            exception_class = InvalidArgumentException
        elif status in ErrorCode.NO_SUCH_COOKIE:
            exception_class = NoSuchCookieException
        elif status in ErrorCode.UNABLE_TO_CAPTURE_SCREEN:
            exception_class = ScreenshotException
        elif status in ErrorCode.ELEMENT_CLICK_INTERCEPTED:
            exception_class = ElementClickInterceptedException
        elif status in ErrorCode.INSECURE_CERTIFICATE:
            exception_class = InsecureCertificateException
        elif status in ErrorCode.INVALID_COORDINATES:
            exception_class = InvalidCoordinatesException
        elif status in ErrorCode.INVALID_SESSION_ID:
            exception_class = InvalidSessionIdException
        elif status in ErrorCode.UNKNOWN_METHOD:
            exception_class = UnknownMethodException
        else:
            exception_class = WebDriverException
        if value == '' or value is None:
            value = response['value']
        if isinstance(value, basestring):
            if exception_class == ErrorInResponseException:
                raise exception_class(response, value)
            raise exception_class(value)
        if message == "" and 'message' in value:
            message = value['message']

        screen = None
        if 'screen' in value:
            screen = value['screen']

        stacktrace = None
        if 'stackTrace' in value and value['stackTrace']:
            stacktrace = []
            try:
                for frame in value['stackTrace']:
                    line = self._value_or_default(frame, 'lineNumber', '')
                    file = self._value_or_default(frame, 'fileName', '<anonymous>')
                    if line:
                        file = "%s:%s" % (file, line)
                    meth = self._value_or_default(frame, 'methodName', '<anonymous>')
                    if 'className' in frame:
                        meth = "%s.%s" % (frame['className'], meth)
                    msg = "    at %s (%s)"
                    msg = msg % (meth, file)
                    stacktrace.append(msg)
            except TypeError:
                pass
        if exception_class == ErrorInResponseException:
            raise exception_class(response, message)
        elif exception_class == UnexpectedAlertPresentException:
            alert_text = None
            if 'data' in value:
                alert_text = value['data'].get('text')
            elif 'alert' in value:
                alert_text = value['alert'].get('text')
            raise exception_class(message, screen, stacktrace, alert_text)
        raise exception_class(message, screen, stacktrace)

    def _value_or_default(self, obj, key, default):
        return obj[key] if key in obj else default
