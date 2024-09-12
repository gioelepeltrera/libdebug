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

        # Start with the current program counter (pc)
        stack_trace = [target.pc]

        # Add the return address from the ra (x1) register
        ra = target.ra if target.ra else None

        # Use the frame pointer (s0) or stack pointer (sp) to unwind through the stack frames
        current_fp = target.x8  # Frame pointer (s0 in RISC-V)
        temp_stack = []
        print("Registers: ")
        #print index + value in hex get attributes x0,x1, ...
        for i in range(32):
            print(f"x{i}: {target.__getattribute__('x'+str(i)):x}")
        print(f"pc: {target.pc:x}")
        print(f"ra: {ra:x}")
        
        while current_fp:
            try:
                # Read the return address from the stack frame
                return_address = int.from_bytes(target.memory[current_fp + 8, 8], byteorder="little")

                # Append the return address to the temporary stack
                temp_stack.append(return_address)

                # Move to the next frame pointer (s0)
                current_fp = int.from_bytes(target.memory[current_fp, 8], byteorder="little")

            except OSError:
                # Stop unwinding if memory access fails
                break

        # Include the return address from the `ra` register if it's not already in the stack
        if ra not in temp_stack:
            stack_trace = stack_trace + [ra] + temp_stack
        else:
            stack_trace = stack_trace + temp_stack

        return stack_trace