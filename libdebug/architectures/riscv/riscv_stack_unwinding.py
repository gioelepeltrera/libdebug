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
    Class that provides stack unwinding for the RISC-V architecture.
    """

    def unwind(self, target: "Debugger") -> list:
        """
        Unwind the stack of a process using both the frame pointer (s0) and the stack pointer (sp).

        Args:
            target (Debugger): The target Debugger.

        Returns:
            list: A list of return addresses (stack trace).
        """

        # Start with the current program counter (pc)
        stack_trace_fp = [target.pc]
        stack_trace_sp = [target.pc]

        # Add the return address from the ra (x1) register
        ra = target.ra if target.ra else None

        # Frame pointer (s0, x8) based unwinding
        current_fp = target.s0  # Corrected register: x8 is the frame pointer (s0)
        temp_stack_fp = []
        
        # Stack pointer (sp, x2) based unwinding
        current_sp = target.sp  # Corrected register: x2 is the stack pointer (sp)
        temp_stack_sp = []

        # Print registers for debugging
        print("Registers: ")
        for i in range(32):
            print(f"x{i}: {getattr(target, f'x{i}'):x}")
        print(f"pc: {target.pc:x}")
        print(f"ra: {ra:x}")

        # Unwind using frame pointer (s0, x8)
        print("\nUnwinding using frame pointer (s0, x8):")
        while current_fp:
            try:
                print(f"Frame pointer (s0) at: {current_fp:x}")
                
                # Read the return address from the stack frame
                return_address_fp = int.from_bytes(target.memory[current_fp + 8, 8], byteorder="little")

                # Append the return address to the temporary stack
                temp_stack_fp.append(return_address_fp)

                # Move to the next frame pointer
                current_fp = int.from_bytes(target.memory[current_fp, 8], byteorder="little")

            except OSError:
                print("Error reading memory using frame pointer (s0).")
                break

        # Unwind using stack pointer (sp, x2)
        print("\nUnwinding using stack pointer (sp, x2):")
        while current_sp:
            try:
                print(f"Stack pointer (sp) at: {current_sp:x}")

                # Read the return address from the stack
                return_address_sp = int.from_bytes(target.memory[current_sp, 8], byteorder="little")

                # Append the return address to the temporary stack
                temp_stack_sp.append(return_address_sp)

                # Move to the next stack pointer
                current_sp = int.from_bytes(target.memory[current_sp + 8, 8], byteorder="little")

            except OSError:
                print("Error reading memory using stack pointer (sp).")
                break

        # Include the return address from the `ra` register if it's not in the stack trace
        if ra not in temp_stack_fp:
            stack_trace_fp = stack_trace_fp + [ra] + temp_stack_fp
        else:
            stack_trace_fp = stack_trace_fp + temp_stack_fp

        if ra not in temp_stack_sp:
            stack_trace_sp = stack_trace_sp + [ra] + temp_stack_sp
        else:
            stack_trace_sp = stack_trace_sp + temp_stack_sp

        # Print both stack traces before returning
        print("\nStack trace using frame pointer (s0, x8):")
        print(stack_trace_fp)

        print("\nStack trace using stack pointer (sp, x2):")
        print(stack_trace_sp)

        # Return both stack traces for better testing
        return stack_trace_fp, stack_trace_sp
