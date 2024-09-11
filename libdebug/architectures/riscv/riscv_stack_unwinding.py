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


class RiscVStackUnwinding():
    """
    Class that provides stack unwinding for the RISC-V architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process.

        Args:
            target (Debugger): The target Debugger.

        Returns:
            list: A list of return addresses (stack trace).
        """

        # Start with the current program counter (pc), which holds the current instruction pointer
        stack_trace = [target.pc]
        
        # Add the return address from the ra (x1) register, if valid
        ra = target.ra if target.ra else None

        # Use the stack pointer (sp) to unwind through the stack frames
        current_sp = target.sp
        temp_stack = []
        while current_sp:
            try:
                # Read the return address from the stack (stored at current_sp)
                return_address = int.from_bytes(target.memory[current_sp, 8], byteorder="little")

                # Append the return address to the temporary stack
                temp_stack.append(return_address)

                # Read the next stack pointer (previous frame pointer) from the current stack pointer
                current_sp = int.from_bytes(target.memory[current_sp + 8, 8], byteorder="little")
                
            except OSError:
                # Stop unwinding if memory access fails
                break

        # Include the return address from the `ra` register if it's not in the temporary stack
        if ra not in temp_stack:
            stack_trace = stack_trace + [ra] + temp_stack
        else:
            stack_trace = stack_trace + temp_stack

        return stack_trace
