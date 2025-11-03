LBP-8 User Reference

Introduction

The LBP-8 is an 8-bit CPU built in LittleBigPlanet 3. It has a simple
ALU, 256B RAM, and supports 4 addressing modes.

Registers

A: The accumulator stores the results of arithmetic and logic
operations. It is an implicit operand for most instructions.

X: Index register. Supports load and increment operations only.

I: Stores input from the input bus.

O: Used to send output to an external system from the CPU.

Flags

Z: Set if the accumulator is zero.

C: Set if the last arithmetic operation resulted in a value too large to
be represented. Cleared otherwise.

Addressing Modes

  -----------------------------------------------------------------------
  Mode                    Syntax                  Description
  ----------------------- ----------------------- -----------------------
  Immediate               #value                  Operand is literal
                                                  (e.g. LDA #5)

  Register                %register               Operand is a register's
                                                  value (e.g. LDA %X)

  Direct                  \$address               Operand is value in
                                                  memory (e.g. LDA \$20)

  Register pointer        \$register              Operand is at the
                                                  address stored in the
                                                  specified register
                                                  (e.g. LDA \$I)
  -----------------------------------------------------------------------

Note: STA is only valid in direct or register pointer mode.

Instruction Set

  -----------------------------------------------------------------------
  Mnemonic          Description       Valid Modes       Flags Affected
  ----------------- ----------------- ----------------- -----------------
  IN                Loads the I       N/A               N/A
                    register with the                   
                    current input                       
                    value                               

  ADD               Add to            Immediate,        Z, C
                    accumulator       register, direct, 
                                      register pointer  

  SUB               Subtract from     Immediate,        Z, C
                    accumulator       register, direct, 
                                      register pointer  

  AND               Performs a        Immediate,        Z
                    bitwise AND on    register, direct, 
                    the accumulator   register pointer  

  XOR               Performs a        Immediate,        Z
                    bitwise XOR on    register, direct, 
                    the accumulator   register pointer  

  OR                Performs a        Immediate,        Z
                    bitwise OR on the register, direct, 
                    accumulator       register pointer  

  NOT               Performs a        N/A               Z
                    bitwise NOT on                      
                    the accumulator                     

  LDA               Load accumulator  Immediate,        Z
                                      register, direct, 
                                      register pointer  

  STA               Store accumulator Direct, register  N/A
                    at specified      pointer           
                    address in memory                   

  LDX               Load index        Immediate,        N/A
                    register          register, direct, 
                                      register pointer  

  INCX              Increment index   N/A               N/A
                    register                            

  JMP               Unconditional     Immediate,        N/A
                    jump              register, direct, 
                                      register pointer  

  JC                Jump if carry     Immediate,        N/A
                    flag is set       register, direct, 
                                      register pointer  

  JZ                Jump if zero flag Immediate,        N/A
                    is set            register, direct, 
                                      register pointer  

  OUT               Load the output   Immediate,        N/A
                    register          register, direct, 
                                      register pointer  

  HLT               Stop execution    N/A               N/A
  -----------------------------------------------------------------------

Note: The subsequent instruction after a jump is not loaded reliably. It
is recommended to insert an IN instruction before the main block to be
executed after a jump.
