# LBP-8 CPU

## Introduction

The LBP-8 is an 8-bit CPU built in LittleBigPlanet 3. It has a simple
ALU, 256B RAM, and supports 4 addressing modes.

### Registers

| Register | Description                                           |
|----------|-------------------------------------------------------|
| A        | Accumulator. Stores results of arithmetic and logic operations. Implicit operand for most instructions. |
| X        | Index register. Supports load and increment operations only. |
| I        | Input register. Stores data from the input bus.      |
| O        | Output register. Sends data to an external system.  |

### Flags

| Flag | Description                                                   |
|------|---------------------------------------------------------------|
| Z    | Set if the accumulator is zero.                               |
| C    | Set if the last arithmetic operation resulted in a value to large to be represented; cleared otherwise. |

### Addressing Modes

| Mode              | Syntax       | Description                                           |
|------------------ |------------- |------------------------------------------------------|
| Immediate         | #value       | Operand is literal (e.g. LDA #5)                    |
| Register          | %register    | Operand is a register's value (e.g. LDA %X)         |
| Direct            | $address     | Operand is value in memory (e.g. LDA $20)           |
| Register pointer  | $register    | Operand is at the address stored in the specified register (e.g. LDA $I) |


Note: STA is only valid in direct or register pointer mode.

### Instruction Set

| Mnemonic | Description                       | Valid Modes                     | Flags Affected |
|----------|-----------------------------------|---------------------------------|----------------|
| IN       | Loads the I register with the current input value | N/A                             | N/A            |
| ADD      | Add to accumulator                | Immediate, register, direct, register pointer | Z, C           |
| SUB      | Subtract from accumulator         | Immediate, register, direct, register pointer | Z, C           |
| AND      | Performs a bitwise AND on the accumulator | Immediate, register, direct, register pointer | Z              |
| XOR      | Performs a bitwise XOR on the accumulator | Immediate, register, direct, register pointer | Z              |
| OR       | Performs a bitwise OR on the accumulator | Immediate, register, direct, register pointer | Z              |
| NOT      | Performs a bitwise NOT on the accumulator | N/A                             | Z              |
| LDA      | Load accumulator                  | Immediate, register, direct, register pointer | Z              |
| STA      | Store accumulator at specified address in memory | Direct, register pointer        | N/A            |
| LDX      | Load index register                | Immediate, register, direct, register pointer | N/A            |
| INCX     | Increment index register           | N/A                             | N/A            |
| JMP      | Unconditional jump                 | Immediate, register, direct, register pointer | N/A            |
| JC       | Jump if carry flag is set          | Immediate, register, direct, register pointer | N/A            |
| JZ       | Jump if zero flag is set           | Immediate, register, direct, register pointer | N/A            |
| OUT      | Load the output register           | Immediate, register, direct, register pointer | N/A            |
| HLT      | Stop execution                     | N/A                             | N/A            |


Note: The subsequent instruction after a jump is not loaded reliably. The assembler automatically inserts an IN instruction before the main block to be
executed after a jump to work around this issue.
