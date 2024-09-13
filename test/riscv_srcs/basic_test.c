//
// This file is part of libdebug Python library (https://github.com/gioelepeltrera/libdebug).
// Copyright (c) 2024 Gioele Peltrera.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.
//
#include <stdio.h>
#include <stdlib.h>

void register_test()
{
    asm volatile (
        // Loading 64-bit values into x0-x14 registers
        //"li x0, 0x0000000000000000\n\t"

        //temporary registersq
        "li x5, 0x5566770011223344\n\t"
        "li x6, 0x6677001122334455\n\t"
        "li x7, 0x7700112233445566\n\t"

        "li x9, 0x0011223344556677\n\t"

        //saved registers
        "li x18, 0x0011223344556677\n\t"
        "li x19, 0x1122334455667700\n\t"
        "li x20, 0x2233445566770011\n\t"
        "li x21, 0x3344556677001122\n\t"
        "li x22, 0x4455667700112233\n\t"
        "li x23, 0x5566770011223344\n\t"
        "li x24, 0x6677001122334455\n\t"
        "li x25, 0x7700112233445566\n\t"
        "li x26, 0x0011223344556677\n\t"
        "li x27, 0x1122334455667700\n\t"
        //temporary registers
        "li x28, 0x2233445566770011\n\t"
        "li x29, 0x3344556677001122\n\t"
        "li x30, 0x4455667700112233\n\t"
        "li x31, 0x5566770011223344\n\t"
        "nop\n\t"

        "nop\n\t"

        // Simply return using `jalr ra` (equivalent to `ret` in RISC-V)
        :
        :
        : "x0", "x5", "x6", "x7", "x9", "x18", "x19", "x20", "x21", "x22", "x23", "x24", "x25", "x26", "x27", "x28", "x29", "x30", "x31"
    );
    return;
}

int main()
{
    printf("Running register test\n");

    register_test();

    return EXIT_SUCCESS;
}
