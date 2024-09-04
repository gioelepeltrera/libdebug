#
# This file is part of libdebug Python library (https://github.com/gioelepeltrera/libdebug).
# Copyright (c) 2024 Gioele Peltrera.
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
class Arm64StackUnwinding():
    """
    Class that provides stack unwinding for the AArch64 architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process.

        Args:
            target (Debugger): The target Debugger.
        
        Returns:
            list: A list of return addresses.
        """

        # Start with the current PC (Program Counter, equivalent to RIP in x86-64)
        current_fp = target.x29  # Frame pointer (x29)
        stack_trace = [target.pc]  # Program counter (x30 holds return address in AArch64)

        while current_fp:
            try:
                # Read the return address from the link register (LR) or the stack
                return_address = int.from_bytes(target.memory[current_fp + 8, 8], byteorder="little")

                # Read the previous frame pointer (x29) and set it as the current one
                current_fp = int.from_bytes(target.memory[current_fp, 8], byteorder="little")

                # Append the return address to the stack trace
                stack_trace.append(return_address)
            except OSError:
                # If we hit an error while reading memory, stop unwinding
                break

        return stack_trace
