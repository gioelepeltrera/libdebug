#
# This file is part of libdebug Python library (https://github.com/io-no/libdebug).
# Copyright (c) 2023 Roberto Alessandro Bertolini.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from dataclasses import dataclass
from typing import Callable


@dataclass
class RegisterHolder:
    """An abstract class that holds the state of the registers of a process, providing setters and getters for them."""

    def apply_on(self, target, target_class):
        """Applies the current register values to the specified target.

        Args:
            target (object): The object to which the register values should be applied.
            target_class (type): The class of the target object, needed to set the attributes.
        """
        pass

    def flush(self, source):
        """Flushes the register values from the specified source.

        Args:
            source (object): The object from which the register values should be flushed.
        """
        pass


@dataclass
class PtraceRegisterHolder(RegisterHolder):
    """An abstract class that holds the state of the registers of a process, specifically for the `ptrace` debugging backend.

    This class should not be instantiated directly, but rather through the `register_holder_provider` function.

    Attributes:
        register_file (bytes): The content of the register file of the process, as returned by `ptrace`.
    """

    register_file: bytes
    ptrace_setter: Callable[[bytes], None]
