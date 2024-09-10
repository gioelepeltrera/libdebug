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
        "stp x29, x30, [sp, #-16]!\n\t"  // Save frame pointer and link register

        // Loading 64-bit values into x0-x14 registers
        "movz x0, #0x3344, lsl #48\n\t"
        "movk x0, #0x5566, lsl #32\n\t"
        "movk x0, #0x7788, lsl #16\n\t"
        "movk x0, #0x99aa\n\t"

        "movz x1, #0x1122, lsl #48\n\t"
        "movk x1, #0x3344, lsl #32\n\t"
        "movk x1, #0x5566, lsl #16\n\t"
        "movk x1, #0x7700\n\t"

        "movz x2, #0x2233, lsl #48\n\t"
        "movk x2, #0x4455, lsl #32\n\t"
        "movk x2, #0x6677, lsl #16\n\t"
        "movk x2, #0x0011\n\t"

        "movz x3, #0x3344, lsl #48\n\t"
        "movk x3, #0x5566, lsl #32\n\t"
        "movk x3, #0x7700, lsl #16\n\t"
        "movk x3, #0x1122\n\t"

        "movz x4, #0x4455, lsl #48\n\t"
        "movk x4, #0x6677, lsl #32\n\t"
        "movk x4, #0x0011, lsl #16\n\t"
        "movk x4, #0x2233\n\t"

        "movz x5, #0x5566, lsl #48\n\t"
        "movk x5, #0x7700, lsl #32\n\t"
        "movk x5, #0x1122, lsl #16\n\t"
        "movk x5, #0x3344\n\t"

        "movz x6, #0x6677, lsl #48\n\t"
        "movk x6, #0x0011, lsl #32\n\t"
        "movk x6, #0x2233, lsl #16\n\t"
        "movk x6, #0x4455\n\t"

        "movz x7, #0xaabb, lsl #48\n\t"
        "movk x7, #0xccdd, lsl #32\n\t"
        "movk x7, #0x1122, lsl #16\n\t"
        "movk x7, #0x3344\n\t"

        "movz x8, #0xbbcc, lsl #48\n\t"
        "movk x8, #0xdd11, lsl #32\n\t"
        "movk x8, #0x2233, lsl #16\n\t"
        "movk x8, #0x44aa\n\t"

        "movz x9, #0xccdd, lsl #48\n\t"
        "movk x9, #0x1122, lsl #32\n\t"
        "movk x9, #0x3344, lsl #16\n\t"
        "movk x9, #0xaabb\n\t"

        "movz x10, #0xdd11, lsl #48\n\t"
        "movk x10, #0x2233, lsl #32\n\t"
        "movk x10, #0x44aa, lsl #16\n\t"
        "movk x10, #0xbbcc\n\t"

        "movz x11, #0x1122, lsl #48\n\t"
        "movk x11, #0x3344, lsl #32\n\t"
        "movk x11, #0x5566, lsl #16\n\t"
        "movk x11, #0x7788\n\t"

        "movz x12, #0x2233, lsl #48\n\t"
        "movk x12, #0x4455, lsl #32\n\t"
        "movk x12, #0x6677, lsl #16\n\t"
        "movk x12, #0x8899\n\t"

        "movz x13, #0x3344, lsl #48\n\t"
        "movk x13, #0x5566, lsl #32\n\t"
        "movk x13, #0x7788, lsl #16\n\t"
        "movk x13, #0x99aa\n\t"

        "movz x14, #0x4455, lsl #48\n\t"
        "movk x14, #0x6677, lsl #32\n\t"
        "movk x14, #0x8899, lsl #16\n\t"
        "movk x14, #0xaabb\n\t"

        "nop\n\t"

        // Loading 32-bit values into w0-w14 registers
        "movz w0, #0x1122, lsl #16\n\t"
        "movk w0, #0x3344\n\t"

        "movz w1, #0x2233, lsl #16\n\t"
        "movk w1, #0x4455\n\t"

        "movz w2, #0x3344, lsl #16\n\t"
        "movk w2, #0x5566\n\t"

        "movz w3, #0x4455, lsl #16\n\t"
        "movk w3, #0x6677\n\t"

        "movz w4, #0x5566, lsl #16\n\t"
        "movk w4, #0x7788\n\t"

        "movz w5, #0x6677, lsl #16\n\t"
        "movk w5, #0x8899\n\t"

        "movz w6, #0x7788, lsl #16\n\t"
        "movk w6, #0x99aa\n\t"

        "movz w7, #0x8899, lsl #16\n\t"
        "movk w7, #0xaabb\n\t"

        "movz w8, #0x99aa, lsl #16\n\t"
        "movk w8, #0xbbcc\n\t"

        "movz w9, #0xaabb, lsl #16\n\t"
        "movk w9, #0xccdd\n\t"

        "movz w10, #0xbbcc, lsl #16\n\t"
        "movk w10, #0xdd11\n\t"

        "movz w11, #0xccdd, lsl #16\n\t"
        "movk w11, #0x1122\n\t"

        "movz w12, #0xdd11, lsl #16\n\t"
        "movk w12, #0x2233\n\t"

        "movz w13, #0x1122, lsl #16\n\t"
        "movk w13, #0x3344\n\t"

        "movz w14, #0x2233, lsl #16\n\t"
        "movk w14, #0x4455\n\t"

        "nop\n\t"

        "ldp x29, x30, [sp], #16\n\t"  // Restore frame pointer and link register
        :
        :
        : "x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8",
          "x9", "x10", "x11", "x12", "x13", "x14", "x29", "x30"
    );
}

int main()
{
    printf("Provola\n");

    register_test();

    return EXIT_SUCCESS;
}

