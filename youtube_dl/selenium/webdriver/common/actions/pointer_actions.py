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
from . import interaction

from .interaction import Interaction
from .mouse_button import MouseButton
from .pointer_input import PointerInput

from selenium.webdriver.remote.webelement import WebElement


class PointerActions(Interaction):

    def __init__(self, source=None):
        if source is None:
            source = PointerInput(interaction.POINTER, "mouse")
        self.source = source
        super(PointerActions, self).__init__(source)

    def pointer_down(self, button=MouseButton.LEFT):
        self._button_action("create_pointer_down", button=button)

    def pointer_up(self, button=MouseButton.LEFT):
        self._button_action("create_pointer_up", button=button)

    def move_to(self, element, x=None, y=None):
        if not isinstance(element, WebElement):
            raise AttributeError("move_to requires a WebElement")
        if x is not None or y is not None:
            el_rect = element.rect
            left_offset = el_rect['width'] / 2
            top_offset = el_rect['height'] / 2
            left = -left_offset + (x or 0)
            top = -top_offset + (y or 0)
        else:
            left = 0
            top = 0
        self.source.create_pointer_move(origin=element, x=int(left), y=int(top))
        return self

    def move_by(self, x, y):
        self.source.create_pointer_move(origin=interaction.POINTER, x=int(x), y=int(y))
        return self

    def move_to_location(self, x, y):
        self.source.create_pointer_move(origin='viewport', x=int(x), y=int(y))
        return self

    def click(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down(MouseButton.LEFT)
        self.pointer_up(MouseButton.LEFT)
        return self

    def context_click(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down(MouseButton.RIGHT)
        self.pointer_up(MouseButton.RIGHT)
        return self

    def click_and_hold(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down()
        return self

    def release(self):
        self.pointer_up()
        return self

    def double_click(self, element=None):
        if element:
            self.move_to(element)
        self.click()
        self.click()

    def pause(self, duration=0):
        self.source.create_pause(duration)
        return self

    def _button_action(self, action, button=MouseButton.LEFT):
        meth = getattr(self.source, action)
        meth(button)
        return self
