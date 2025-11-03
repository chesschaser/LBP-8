import argparse
import serial
import serial.tools.list_ports
import os
import time
import sys
import tempfile
from tqdm import tqdm
from colorama import Fore, Style, init

init()

inst_set = ["IN", "ADD", "SUB", "AND", "XOR", "OR", "NOT", "LDA", "STA", "LDX", "INCX", "JMP", "JC",
            "JZ", "OUT", "HLT"]
registers = ["A", "X", "I", "O"]
delimiters = ["#", "%", "$"]

keywords = ["+", "-", "&", "|", "^", "~", "=", "LET", "DIM", "PRINT", "GOTO", "END"]

DONE = "DONE"

def generate_sequence(value):
    sequence = "x" # Start
    sequence += "".join("ox" if (value >> i) & 0x1 else "x" for i in range(8)) # Main data
    sequence += "x" # Write enable pulse
    return sequence

def validate_instruction(mnemonic, operand, delimiter):
    if mnemonic not in inst_set:
        print(Fore.RED + f"Error: Invalid mnemonic '{mnemonic}'!")
        sys.exit(1)
    if operand:
        operand = operand[1:]
        if not operand.isdigit() and operand not in registers:
            print(Fore.RED + f"Error: Invalid register '{operand}'!")
            sys.exit(1)
        if operand.isdigit():
            if int(operand, 0) > 255:
                print(Fore.RED + f"Error: Operand '{operand}' too large to be represented!")
                sys.exit(1)
            if delimiter not in delimiters:
                print(Fore.RED + f"Error: Invalid addressing mode delimiter '{delimiter}'!")
                sys.exit(1)

def get_addressing_mode(raw_operand, delimiter):
    if raw_operand.isdigit():
        match delimiter:
            case "#":
                return 0 # immediate
            case "$":
                return 2 # direct
        print(Fore.RED + f"Error: Invalid addressing mode delimiter '{delimiter}' for numeric operand '{raw_operand}'!")
        sys.exit(1)
    match delimiter:
        case "%":
            return 1 # register
        case "$":
            return 3 # register pointer
    print(Fore.RED + f"Error: Invalid addressing mode delimiter '{delimiter}' for register operand '{raw_operand}'!")
    sys.exit(1)
        
def assemble(asm):
    if len(asm) * 2 > 256:
        print(Fore.RED + "Error: Program too long (>256 bytes)!")
        sys.exit(1)

    # Detect labels
    addr = 0
    label_map = {}
    for i, line in enumerate(asm):
        line = line.strip().split(";")[0] # Ignore comments
        if not line:
            continue
        if line.endswith(":"):
            asm.insert(i+1, "IN") # Insert bug workaround
            label_map[line[:-1]] = addr
            continue
        addr += 2 # Each instruction is 2 bytes

    # Parse assembly
    binary = []
    for line in asm:
        line = line.strip().split(";")[0] # Ignore comments
        if not line or line.endswith(":"):
            continue
        parts = line.split()
        mnemonic = parts[0]
        mnemonic = mnemonic.upper()
        if len(parts) > 1:
            operand = parts[1]
        else:
            operand = ""
            
        if operand in label_map:
            operand = "#" + str(label_map[operand])
        operand = operand.upper()
        
        delimiter = operand[0:1]
        validate_instruction(mnemonic, operand, delimiter)

        operand = operand[1:]
        if operand:
            addr_mode = get_addressing_mode(operand, delimiter)
        else:
            addr_mode = 0
            
        if operand in registers:
            operand = str(registers.index(operand))
            
        high_byte = inst_set.index(mnemonic)
        high_byte <<= 4
        if operand:
            high_byte |= (int(operand, 0) >> 4) & 0x0F # high nibble
        binary.append(high_byte)

        low_byte = 0
        if operand:
            low_byte = int(operand, 0) & 0x0F # low nibble
            low_byte <<= 2
            low_byte |= addr_mode
            low_byte <<= 2 # Make up the extra 2 bits
        binary.append(low_byte)

    return binary

def compile_file(file):
    global keywords

    def is_symbol(token):
        return token not in keywords and not token.isdigit()

    def alloc(name, size=1):
        nonlocal next_addr
        if name not in symbols:
            symbols[name] = {"addr": next_addr, "size": size}
            next_addr += size
        return symbols[name]["addr"]

    with open(file, "r") as f:
        lines = f.readlines()

    compiled = []
    symbols = {}
    next_addr = 0x0
    
    for line_num, line in enumerate(lines):
        tokens = [t.strip().upper() for t in line.strip().split()]
        if not tokens or tokens[0].startswith("#"):  # ignore comments
            continue

        if tokens[0].endswith(":"):
            label = tokens[0][:-1]
            compiled.append(f"{label}:")
            continue
        
        op = tokens[0]

        if op == "DIM":
            if len(tokens) < 3:
                print(Fore.RED + f"Error on line '{line_num}': DIM requires name and size!")
                sys.exit(1)
                continue
            name = tokens[1]
            try:
                size = int(tokens[2].strip("[]"))
            except ValueError:
                print(Fore.RED + f"Error on line '{line_num}': Invalid size '{tokens[2]}' in DIM!")
                sys.exit(1)
                continue
            alloc(name, size)
        elif op == "LET" or is_symbol(op):
            if is_symbol(op):
                offset = 0
            else:
                offset = 1
            name = tokens[offset]
            if not is_symbol(name):
                print(Fore.RED + f"Error on line '{line_num}': Invalid variable name '{name}'!")
                sys.exit(1)
            alloc(name)

            assign = tokens[offset + 1]
            if assign != "=":
                print(Fore.RED + f"Error on line '{line_num}': Expected '=' for variable declaration '{name}'!")
                sys.exit(1)
                
            rhs = tokens[offset + 2:]
            if not rhs:
                print(Fore.RED + f"Error on line '{line_num}': Expected literal or symbol for variable declaration '{name}'!")
                sys.exit(1)
                
            if len(rhs) == 1:
                # Literal or symbol assignment
                val = rhs[0]
                if val.isdigit():
                    compiled.append(f"LDA #{val}")
                elif is_symbol(val):
                    addr = symbols[val]["addr"]
                    compiled.append(f"LDA ${addr:02X}")
                else:
                    print(Fore.RED + f"Error on line '{line_num}': Expected literal or symbol for variable declaration '{name}', got '{val}'!")                    
                    sys.exit(1)
                compiled.append(f"STA ${symbols[name]['addr']:02X}")
            elif len(rhs) == 3:
                # Arithmetic or logical operation
                left, operator, right = rhs
                if operator not in ["+", "-", "&", "|", "^"]:
                    print(Fore.RED + f"Error on line {line_num}: Unsupported operator '{operator}'!")
                    sys.exit(1)
                if left.isdigit():
                    compiled.append(f"LDA #{left}")
                else:
                    compiled.append(f"LDA ${symbols[left]['addr']:02X}")
                if right.isdigit():
                    right = f"#{right}"
                else:
                    right = f"${symbols[right]['addr']:02X}"
                if operator == "+": compiled.append(f"ADD {right}")
                elif operator == "-": compiled.append(f"SUB {right}")
                elif operator == "&": compiled.append(f"AND {right}")
                elif operator == "|": compiled.append(f"OR {right}")
                elif operator == "^": compiled.append(f"XOR {right}")
                compiled.append(f"STA ${symbols[name]['addr']:02X}")
        elif op == "GOTO":
            label = tokens[1]
            compiled.append(f"JMP {label}")
        elif op == "PRINT":
            expr = tokens[1]
            if expr.isdigit():
                compiled.append(f"OUT #{expr}")
            else:
                compiled.append(f"LDA ${symbols[expr]['addr']:02X}")
                compiled.append("OUT %A")
        elif op == "END":
            compiled.append("HLT")
    return compiled
                
def find_programmer(name="PROGRAMMER_ON"):
    for port in serial.tools.list_ports.comports():
        try:
            ser = serial.Serial(port.device, 115200, timeout=1)
            time.sleep(2)
            for _ in range(5):  # try reading 5 lines
                response = ser.readline().decode().strip()
                if response == name:
                    ser.close()
                    return port.device
            ser.close()
        except:
            pass
    return None

def gen_bin(n):
    return bin(n)[2:].zfill(8)

def main():
    parser = argparse.ArgumentParser(
        description="Tool to upload programs to the LBP-8."
    )
    
    parser.add_argument("target_file", help="path to the program file")

    parser.add_argument(
        "-a", "--assembly", 
        action="store_true", 
        help="skip compilation and directly assemble file contents"
    )
    parser.add_argument(
        "-c", "--compile", 
        action="store_true", 
        help="use if target file requires compilation prior to assembly"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="enable verbose output"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.target_file):
        print(Fore.RED + f"Error: File '{args.target_file}' not found!")
        sys.exit(1)

    if not args.compile and not args.assembly:
        print(Fore.RED + f"Error: No mode specified!")
        sys.exit(1)
        
    load_asm = True
    if args.compile and not args.assembly:
        load_asm = False
        print(Fore.WHITE + "Compiling ...")
        asm = compile_file(args.target_file)
        print(Fore.GREEN + "Done compiling!\n")

        if args.verbose:
            print(Fore.CYAN + "Generated assembly:")
            print(Fore.CYAN + "\n".join(asm) + "\n")
            
    print(Fore.WHITE + "Assembling ...")

    if load_asm:
        with open(args.target_file, "r") as asm_file:
            asm = asm_file.readlines()

    binary = assemble(asm)    
    print(Fore.GREEN + "Done assembling!\n")
    
    if args.verbose:
        print(Fore.CYAN + "Generated binary: ")
        print(Fore.CYAN + " ".join(map(gen_bin, binary)) + "\n")

    print(Fore.WHITE + "Generating sequence ...")
    sequence = "tttt" # Ensure reset
    sequence += "".join([generate_sequence(word) for word in binary])
    sequence += "x" # Ensure write enable is pulsed
    print(Fore.GREEN + "Done generating sequence!\n")

    if args.verbose:
        print(Fore.CYAN + "Generated sequence: ")
        print(Fore.CYAN + "".join(sequence) + "\n")

    print(Fore.WHITE + "Finding programmer ...")
    programmer_port = find_programmer()
    if programmer_port is None:
        print(Fore.RED + "Error: Programmer not found!")
        sys.exit(1)
        
    print(Fore.GREEN + f"Programmer detected on '{programmer_port}'!\n")
    
    ser = serial.Serial(port=programmer_port, baudrate=115200, timeout=1)
    time.sleep(2)
    
    chunk_size = 8        
    for i in tqdm(range(0, len(sequence), chunk_size), desc=(Fore.WHITE + "Uploading:"), ncols=70):
        try:
            ser.write(sequence[i:i+chunk_size].encode())
            ser.write(b'\n')
            ser.flush()
            
            while True:
                response = ser.readline().decode().strip()
                if response:
                    if response == "DONE":
                        break
        except Exception as e:
            print(Fore.RED + f"Error: An error occurred during the upload.\n" + str(e))
            ser.close()

    print(Fore.GREEN + "Upload complete!")
    ser.close()
    
if __name__ == "__main__":
    main()
