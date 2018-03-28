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
from .input_device import InputDevice

from selenium.webdriver.remote.webelement import WebElement


class PointerInput(InputDevice):

    DEFAULT_MOVE_DURATION = 250

    def __init__(self, type_, name):
        super(PointerInput, self).__init__()
        self.type = type_
        self.name = name

    def create_pointer_move(self, duration=DEFAULT_MOVE_DURATION, x=None, y=None, origin=None):
        action = dict(type="pointerMove", duration=duration)
        action["x"] = x
        action["y"] = y
        if isinstance(origin, WebElement):
            action["origin"] = {"element-6066-11e4-a52e-4f735466cecf": origin.id}
        elif origin is not None:
            action["origin"] = origin

        self.add_action(action)

    def create_pointer_down(self, button):
        self.add_action({"type": "pointerDown", "duration": 0, "button": button})

    def create_pointer_up(self, button):
        self.add_action({"type": "pointerUp", "duration": 0, "button": button})

    def create_pointer_cancel(self):
        self.add_action({"type": "pointerCancel"})

    def create_pause(self, pause_duration):
        self.add_action({"type": "pause", "duration": pause_duration * 1000})

    def encode(self):
        return {"type": self.type,
                "parameters": {"pointerType": self.name},
                "id": self.name,
                "actions": [acts for acts in self.actions]}
