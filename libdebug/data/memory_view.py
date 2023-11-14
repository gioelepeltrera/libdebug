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

from typing import Callable
from collections.abc import MutableSequence


class MemoryView(MutableSequence):
    """A memory interface for the target process.
    This class must be used to read and write memory of the target process.

    Attributes:
            getter (Callable[[int], bytes]): A function that reads memory from the target process.
            setter (Callable[[int, bytes], None]): A function that writes memory to the target process.
            unit_size (int, optional): The data size used by the getter and setter functions. Defaults to 8.
            align_to (int, optional): The address alignment that must be used when reading and writing memory. Defaults to 1.
    """

    def __init__(
        self,
        getter: Callable[[int], bytes],
        setter: Callable[[int, bytes], None],
        unit_size: int = 8,
        align_to: int = 1,
    ):
        self.getter = getter
        self.setter = setter
        self.unit_size = unit_size
        self.align_to = align_to

    def read(self, address: int, size: int) -> bytes:
        """Reads memory from the target process.

        Args:
            address (int): The address to read from.
            size (int): The number of bytes to read.

        Returns:
            bytes: The read bytes.
        """
        if self.align_to == 1:
            data = b""

            remainder = size % self.unit_size

            for i in range(address, address + size - remainder, self.unit_size):
                data += self.getter(i)

            if remainder:
                data += self.getter(address + size - remainder)[:remainder]

            return data
        else:
            prefix = address % self.align_to
            prefix_size = self.unit_size - prefix

            data = self.getter(address - prefix)[prefix:]

            remainder = (size - prefix_size) % self.unit_size

            for i in range(
                address + prefix_size, address + size - remainder, self.unit_size
            ):
                data += self.getter(i)

            if remainder:
                data += self.getter(address + size - remainder)[:remainder]

            return data

    def write(self, address: int, data: bytes):
        """Writes memory to the target process.

        Args:
            address (int): The address to write to.
            data (bytes): The data to write.
        """
        size = len(data)

        if self.align_to == 1:
            remainder = size % self.unit_size
            base = address
        else:
            prefix = address % self.align_to
            prefix_size = self.unit_size - prefix

            prev_data = self.getter(address - prefix)

            self.setter(address - prefix, prev_data[:prefix_size] + data[:prefix])

            remainder = (size - prefix_size) % self.unit_size
            base = address + prefix_size

        for i in range(base, address + size - remainder, self.unit_size):
            self.setter(i, data[i - address : i - address + self.unit_size])

        if remainder:
            prev_data = self.getter(address + size - remainder)
            self.setter(
                address + size - remainder,
                data[size - remainder :] + prev_data[remainder:],
            )

    def __getitem__(self, key) -> bytes:
        if isinstance(key, int):
            return self.read(key, 1)
        elif isinstance(key, slice):
            return self.read(key.start, key.stop - key.start)
        else:
            raise TypeError("Invalid key type")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.write(key, value)
        elif isinstance(key, slice):
            self.write(key.start, value)
        else:
            raise TypeError("Invalid key type")

    def __delitem__(self, key):
        raise NotImplementedError("MemoryView doesn't support deletion")

    def __len__(self):
        raise NotImplementedError("MemoryView doesn't support length")

    def insert(self, index, value):
        raise NotImplementedError("MemoryView doesn't support insertion")
