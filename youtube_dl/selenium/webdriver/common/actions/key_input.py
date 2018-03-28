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

from .input_device import InputDevice
from .interaction import (Interaction,
                          Pause)


class KeyInput(InputDevice):
    def __init__(self, name):
        super(KeyInput, self).__init__()
        self.name = name
        self.type = interaction.KEY

    def encode(self):
        return {"type": self.type, "id": self.name, "actions": [acts.encode() for acts in self.actions]}

    def create_key_down(self, key):
        self.add_action(TypingInteraction(self, "keyDown", key))

    def create_key_up(self, key):
        self.add_action(TypingInteraction(self, "keyUp", key))

    def create_pause(self, pause_duration=0):
        self.add_action(Pause(self, pause_duration))


class TypingInteraction(Interaction):

    def __init__(self, source, type_, key):
        super(TypingInteraction, self).__init__(source)
        self.type = type_
        self.key = key

    def encode(self):
        return {"type": self.type, "value": self.key}
