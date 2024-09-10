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
#include <stdlib.h>  // For malloc and free
#include <string.h>  // For memcpy

void manipulate_buffer(char *buffer) {
    for (int i = 0; i < 0x8; i++) {
        buffer[i] = 'A'+i;
    }
    for (int i = 0; i<0x8; i++){
        buffer[i+0x20] = buffer[i];
    }

    for (int i=0;i<0x8;i++){
        buffer[i+0x30] = buffer[i+0x20];
    }

    for (int i=0;i<0x8;i++){
        buffer[i+0x40] = buffer[i+0x30];
    }

    for (int i=0;i<0x8;i++){
        buffer[i+0x50] = buffer[i+0x40];
    }
    for (int i=0;i<0x8;i++){
        buffer[i+0x60] = buffer[i+0x50];
    }
    for (int i=0;i<0x8;i++){
        buffer[i+0x70] = buffer[i+0x60];
    }

}

int main() {
    // Disable buffering for easier debugging
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    // Allocate memory for the buffer using malloc
    char *buffer = (char *)malloc(0x80 * sizeof(char));  // Allocate 16 bytes for the buffer
    char buffer2[0x11];
    if (buffer == NULL) {
        // Check if memory allocation was successful
        printf("Memory allocation failed!\n");
        return 1;
    }

    printf("Welcome to the buffer manipulation program!\n");
    
    // Input from the user, use fgets to avoid buffer overflow
    printf("Enter input (max 15 chars): ");
    fgets(buffer2, 16, stdin);

    // Print the address of the buffer (so Python can monitor it)
    printf("Address of buffer: %p END\n", (void *)buffer);

    // Manipulate the buffer
    manipulate_buffer(buffer);


    return 0;
}
