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


class Command(object):
    """
    Defines constants for the standard WebDriver commands.

    While these constants have no meaning in and of themselves, they are
    used to marshal commands through a service that implements WebDriver's
    remote wire protocol:

        https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol

    """

    # Keep in sync with org.openqa.selenium.remote.DriverCommand

    STATUS = "status"
    NEW_SESSION = "newSession"
    GET_ALL_SESSIONS = "getAllSessions"
    DELETE_SESSION = "deleteSession"
    CLOSE = "close"
    QUIT = "quit"
    GET = "get"
    GO_BACK = "goBack"
    GO_FORWARD = "goForward"
    REFRESH = "refresh"
    ADD_COOKIE = "addCookie"
    GET_COOKIE = "getCookie"
    GET_ALL_COOKIES = "getCookies"
    DELETE_COOKIE = "deleteCookie"
    DELETE_ALL_COOKIES = "deleteAllCookies"
    FIND_ELEMENT = "findElement"
    FIND_ELEMENTS = "findElements"
    FIND_CHILD_ELEMENT = "findChildElement"
    FIND_CHILD_ELEMENTS = "findChildElements"
    CLEAR_ELEMENT = "clearElement"
    CLICK_ELEMENT = "clickElement"
    SEND_KEYS_TO_ELEMENT = "sendKeysToElement"
    SEND_KEYS_TO_ACTIVE_ELEMENT = "sendKeysToActiveElement"
    SUBMIT_ELEMENT = "submitElement"
    UPLOAD_FILE = "uploadFile"
    GET_CURRENT_WINDOW_HANDLE = "getCurrentWindowHandle"
    W3C_GET_CURRENT_WINDOW_HANDLE = "w3cGetCurrentWindowHandle"
    GET_WINDOW_HANDLES = "getWindowHandles"
    W3C_GET_WINDOW_HANDLES = "w3cGetWindowHandles"
    GET_WINDOW_SIZE = "getWindowSize"
    W3C_GET_WINDOW_SIZE = "w3cGetWindowSize"
    W3C_GET_WINDOW_POSITION = "w3cGetWindowPosition"
    GET_WINDOW_POSITION = "getWindowPosition"
    SET_WINDOW_SIZE = "setWindowSize"
    W3C_SET_WINDOW_SIZE = "w3cSetWindowSize"
    SET_WINDOW_RECT = "setWindowRect"
    GET_WINDOW_RECT = "getWindowRect"
    SET_WINDOW_POSITION = "setWindowPosition"
    W3C_SET_WINDOW_POSITION = "w3cSetWindowPosition"
    SWITCH_TO_WINDOW = "switchToWindow"
    SWITCH_TO_FRAME = "switchToFrame"
    SWITCH_TO_PARENT_FRAME = "switchToParentFrame"
    GET_ACTIVE_ELEMENT = "getActiveElement"
    W3C_GET_ACTIVE_ELEMENT = "w3cGetActiveElement"
    GET_CURRENT_URL = "getCurrentUrl"
    GET_PAGE_SOURCE = "getPageSource"
    GET_TITLE = "getTitle"
    EXECUTE_SCRIPT = "executeScript"
    W3C_EXECUTE_SCRIPT = "w3cExecuteScript"
    W3C_EXECUTE_SCRIPT_ASYNC = "w3cExecuteScriptAsync"
    GET_ELEMENT_TEXT = "getElementText"
    GET_ELEMENT_VALUE = "getElementValue"
    GET_ELEMENT_TAG_NAME = "getElementTagName"
    SET_ELEMENT_SELECTED = "setElementSelected"
    IS_ELEMENT_SELECTED = "isElementSelected"
    IS_ELEMENT_ENABLED = "isElementEnabled"
    IS_ELEMENT_DISPLAYED = "isElementDisplayed"
    GET_ELEMENT_LOCATION = "getElementLocation"
    GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW = "getElementLocationOnceScrolledIntoView"
    GET_ELEMENT_SIZE = "getElementSize"
    GET_ELEMENT_RECT = "getElementRect"
    GET_ELEMENT_ATTRIBUTE = "getElementAttribute"
    GET_ELEMENT_PROPERTY = "getElementProperty"
    GET_ELEMENT_VALUE_OF_CSS_PROPERTY = "getElementValueOfCssProperty"
    ELEMENT_EQUALS = "elementEquals"
    SCREENSHOT = "screenshot"
    ELEMENT_SCREENSHOT = "elementScreenshot"
    IMPLICIT_WAIT = "implicitlyWait"
    EXECUTE_ASYNC_SCRIPT = "executeAsyncScript"
    SET_SCRIPT_TIMEOUT = "setScriptTimeout"
    SET_TIMEOUTS = "setTimeouts"
    MAXIMIZE_WINDOW = "windowMaximize"
    W3C_MAXIMIZE_WINDOW = "w3cMaximizeWindow"
    GET_LOG = "getLog"
    GET_AVAILABLE_LOG_TYPES = "getAvailableLogTypes"
    FULLSCREEN_WINDOW = "fullscreenWindow"
    MINIMIZE_WINDOW = "minimizeWindow"

    # Alerts
    DISMISS_ALERT = "dismissAlert"
    W3C_DISMISS_ALERT = "w3cDismissAlert"
    ACCEPT_ALERT = "acceptAlert"
    W3C_ACCEPT_ALERT = "w3cAcceptAlert"
    SET_ALERT_VALUE = "setAlertValue"
    W3C_SET_ALERT_VALUE = "w3cSetAlertValue"
    GET_ALERT_TEXT = "getAlertText"
    W3C_GET_ALERT_TEXT = "w3cGetAlertText"
    SET_ALERT_CREDENTIALS = "setAlertCredentials"

    # Advanced user interactions
    W3C_ACTIONS = "actions"
    W3C_CLEAR_ACTIONS = "clearActionState"
    CLICK = "mouseClick"
    DOUBLE_CLICK = "mouseDoubleClick"
    MOUSE_DOWN = "mouseButtonDown"
    MOUSE_UP = "mouseButtonUp"
    MOVE_TO = "mouseMoveTo"

    # Screen Orientation
    SET_SCREEN_ORIENTATION = "setScreenOrientation"
    GET_SCREEN_ORIENTATION = "getScreenOrientation"

    # Touch Actions
    SINGLE_TAP = "touchSingleTap"
    TOUCH_DOWN = "touchDown"
    TOUCH_UP = "touchUp"
    TOUCH_MOVE = "touchMove"
    TOUCH_SCROLL = "touchScroll"
    DOUBLE_TAP = "touchDoubleTap"
    LONG_PRESS = "touchLongPress"
    FLICK = "touchFlick"

    # HTML 5
    EXECUTE_SQL = "executeSql"

    GET_LOCATION = "getLocation"
    SET_LOCATION = "setLocation"

    GET_APP_CACHE = "getAppCache"
    GET_APP_CACHE_STATUS = "getAppCacheStatus"
    CLEAR_APP_CACHE = "clearAppCache"

    GET_LOCAL_STORAGE_ITEM = "getLocalStorageItem"
    REMOVE_LOCAL_STORAGE_ITEM = "removeLocalStorageItem"
    GET_LOCAL_STORAGE_KEYS = "getLocalStorageKeys"
    SET_LOCAL_STORAGE_ITEM = "setLocalStorageItem"
    CLEAR_LOCAL_STORAGE = "clearLocalStorage"
    GET_LOCAL_STORAGE_SIZE = "getLocalStorageSize"

    GET_SESSION_STORAGE_ITEM = "getSessionStorageItem"
    REMOVE_SESSION_STORAGE_ITEM = "removeSessionStorageItem"
    GET_SESSION_STORAGE_KEYS = "getSessionStorageKeys"
    SET_SESSION_STORAGE_ITEM = "setSessionStorageItem"
    CLEAR_SESSION_STORAGE = "clearSessionStorage"
    GET_SESSION_STORAGE_SIZE = "getSessionStorageSize"

    # Mobile
    GET_NETWORK_CONNECTION = "getNetworkConnection"
    SET_NETWORK_CONNECTION = "setNetworkConnection"
    CURRENT_CONTEXT_HANDLE = "getCurrentContextHandle"
    CONTEXT_HANDLES = "getContextHandles"
    SWITCH_TO_CONTEXT = "switchToContext"
