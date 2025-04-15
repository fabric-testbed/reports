#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2025 FABRIC Testbed
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
