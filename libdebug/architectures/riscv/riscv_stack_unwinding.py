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
        Unwind the stack of a process using both the frame pointer (s0) and the stack pointer (sp).

        Args:
            target (Debugger): The target Debugger.

        Returns:
            list: A list of return addresses (stack trace).
        """

        # Start with the current program counter (pc)
        stack_trace = [target.pc]
        ra = target.ra if target.ra else None

        current_fp = target.x8
        current_sp = target.sp

        temp_stack = []

        # Print registers for debugging
        print(f"PC: {target.pc:x}")
        print(f"FP (s0/x8): {current_fp:x}")
        print(f"SP: {current_sp:x}")
        print(f"RA: {ra:x}")

        # Unwind using frame pointer (s0, x8)
        while current_fp:
            try:
                print(f"Current FP: {current_fp:x}")

                # Attempt to read the return address from the current frame
                return_address = int.from_bytes(target.memory[current_fp + 8, 8], byteorder="little")
                next_fp = int.from_bytes(target.memory[current_fp, 8], byteorder="little")

                # Add the return address to the temporary stack
                temp_stack.append(return_address)

                # Print more values for debugging
                for offset in range(16, 64, 8):
                    value_at_fp = int.from_bytes(target.memory[current_fp + offset, 8], byteorder="little")
                    print(f"Value at (fp + {offset}): {value_at_fp:x}")

                # Move to the next frame
                current_fp = next_fp

            except OSError:
                print("Error reading memory while unwinding stack.")
                break

        # Manual scanning of the stack if unwinding via frame pointer fails
        print("\nManual stack scanning for return addresses:")
        if ra and ra not in temp_stack:
            stack_trace.append(ra)

        while current_sp:
            try:
                for offset in range(0, 128, 8):  # Adjust the range if needed
                    potential_return_addr = int.from_bytes(target.memory[current_sp + offset, 8], byteorder="little")

                    # Just append any address we find (without validation for now)
                    stack_trace.append(potential_return_addr)
                    print(f"Potential return address found at (sp + {offset}): {potential_return_addr:x}")

                # Move up the stack
                current_sp += 128  # Adjust step size as needed

            except OSError:
                print("Error reading memory while scanning stack.")
                break

        return stack_trace
