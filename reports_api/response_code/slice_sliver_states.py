#!/usr/bin/env python3
# MIT License
#
# Copyright (component) 2025 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Komal Thareja (kthare10@renci.org)
# Inherited from ControlFramework
import enum
from enum import Enum
from typing import Union


class SliverStates(Enum):
    """
    Reservation states
    """
    Nascent = 1
    Ticketed = 2
    Active = 4
    ActiveTicketed = 5
    Closed = 6
    CloseWait = 7
    Failed = 8
    Unknown = 9
    CloseFail = 10

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @staticmethod
    def translate(state_name: str) -> Union[int, None]:
        if state_name is None:
            return state_name
        if state_name.lower() == SliverStates.Nascent.name.lower():
            return SliverStates.Nascent.value
        elif state_name.lower() == SliverStates.Ticketed.name.lower():
            return SliverStates.Ticketed.value
        elif state_name.lower() == SliverStates.Active.name.lower():
            return SliverStates.Active.value
        elif state_name.lower() == SliverStates.ActiveTicketed.name.lower():
            return SliverStates.ActiveTicketed.value
        elif state_name.lower() == SliverStates.Closed.name.lower():
            return SliverStates.Closed.value
        elif state_name.lower() == SliverStates.CloseWait.name.lower():
            return SliverStates.CloseWait.value
        elif state_name.lower() == SliverStates.Failed.name.lower():
            return SliverStates.Failed.value
        elif state_name.lower() == SliverStates.CloseFail.name.lower():
            return SliverStates.CloseFail.value
        else:
            return SliverStates.Unknown.value


class SliceState(Enum):
    Nascent = enum.auto()
    Configuring = enum.auto()
    StableError = enum.auto()
    StableOK = enum.auto()
    Closing = enum.auto()
    Dead = enum.auto()
    Modifying = enum.auto()
    ModifyError = enum.auto()
    ModifyOK = enum.auto()
    AllocatedError = enum.auto()
    AllocatedOK = enum.auto()
    All = enum.auto()   # used only for querying

    def __str__(self):
        return self.name

    @classmethod
    def list_values(cls) -> list[int]:
        return list(map(lambda c: c.value, cls))

    @classmethod
    def list_names(cls) -> list[str]:
        return list(map(lambda c: c.name, cls))

    @staticmethod
    def list_values_ex_closing_dead() -> list[int]:
        result = SliceState.list_values()
        result.remove(SliceState.Closing.value)
        result.remove(SliceState.Dead.value)
        return result

    @staticmethod
    def translate_list(states: list[str]) -> list[int] or None:
        if states is None or len(states) == 0:
            return states

        incoming_states = list(map(lambda x: x.lower(), states))

        result = SliceState.list_values()

        if len(incoming_states) == 1 and incoming_states[0] == SliceState.All.name.lower():
            return result

        for s in SliceState:
            if s.name.lower() not in incoming_states:
                result.remove(s.value)

        return result

    @staticmethod
    def translate(state_name: str):
        if not state_name:
            return None
        if state_name.lower() == SliceState.Nascent.name.lower():
            return SliceState.Nascent
        elif state_name.lower() == SliceState.Configuring.name.lower():
            return SliceState.Configuring
        elif state_name.lower() == SliceState.StableOK.name.lower():
            return SliceState.StableOK
        elif state_name.lower() == SliceState.StableError.name.lower():
            return SliceState.StableError
        elif state_name.lower() == SliceState.ModifyOK.name.lower():
            return SliceState.ModifyOK
        elif state_name.lower() == SliceState.ModifyError.name.lower():
            return SliceState.ModifyError
        elif state_name.lower() == SliceState.Modifying.name.lower():
            return SliceState.Modifying
        elif state_name.lower() == SliceState.Closing.name.lower():
            return SliceState.Closing
        elif state_name.lower() == SliceState.Dead.name.lower():
            return SliceState.Dead
        elif state_name.lower() == SliceState.AllocatedOK.name.lower():
            return SliceState.Closing
        elif state_name.lower() == SliceState.AllocatedError.name.lower():
            return SliceState.Dead
        else:
            return SliceState.All

    @staticmethod
    def is_dead_or_closing(*, state) -> bool:
        if state == SliceState.Dead or state == SliceState.Closing:
            return True
        return False

    @staticmethod
    def is_stable(*, state) -> bool:
        if state == SliceState.StableOK or state == SliceState.StableError:
            return True
        return False

    @staticmethod
    def is_allocated(*, state) -> bool:
        if state == SliceState.AllocatedOK or state == SliceState.AllocatedError:
            return True
        return False

    @staticmethod
    def is_modified(*, state) -> bool:
        if state == SliceState.ModifyOK or state == SliceState.ModifyError:
            return True
        return False
