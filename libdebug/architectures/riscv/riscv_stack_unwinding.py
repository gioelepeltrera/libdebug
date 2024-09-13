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
class RiscVStackUnwinding:
    """
    Class that provides stack unwinding for the RISC-V 64-bit architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process on RISC-V 64 architecture.

        Args:
            target (Debugger): The target Debugger.

        Returns:
            list: A list of return addresses (stack trace).
        """

        # Start with the current Program Counter (PC), add it to the stack trace
        stack_trace = [target.pc]  # PC is the current instruction pointer

        # Use the frame pointer (s0, x8) and return address (ra, x1)
        current_fp = target.x8  # s0 is the frame pointer in RISC-V 64
        ra = target.x1  # ra is the return address register in RISC-V 64
        temp_stack = []

        # Unwind the stack using the frame pointer
        while current_fp:
            try:
                # Read the return address from the stack (located at current_fp + 8)
                return_address = int.from_bytes(target.memory[current_fp - 8, 8], byteorder="little")

                # Append the return address to the temporary stack trace
                temp_stack.append(return_address)

                # Read the previous frame pointer (s0, located at current_fp)
                current_fp = int.from_bytes(target.memory[current_fp-16, 8], byteorder="little")                
            except OSError:
                # Stop unwinding if there is an error while reading memory
                break

        # Combine the current stack trace and the unwound addresses
        if ra in temp_stack:
            stack_trace  = stack_trace + temp_stack
        else:
            stack_trace = stack_trace + [ra] + temp_stack

        return stack_trace
