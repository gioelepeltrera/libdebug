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

class Arm64StackUnwinding:
    """
    Class that provides stack unwinding for the ARM64 (AArch64) architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process.

        Args:
            target (Debugger): The target Debugger.
        
        Returns:
            list: A list of return addresses.
        """
        current_fp = target.regs['fp']  # ARM64 frame pointer (x29)
        stack_trace = [target.regs['pc']]  # Start with the program counter (x30 or LR in ARM64)

        while current_fp:
            try:
                # Read the return address from the memory at fp + 8 (Link Register)
                return_address = int.from_bytes(target.memory[current_fp + 8:current_fp + 16], byteorder="little")
                
                # Read the previous frame pointer (fp)
                current_fp = int.from_bytes(target.memory[current_fp:current_fp + 8], byteorder="little")
                
                stack_trace.append(return_address)
            except OSError:
                break

        return stack_trace
