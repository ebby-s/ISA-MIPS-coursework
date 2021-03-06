import os
import sys

opcodes = {'ADDIU'  : '001001',
           'ADDU'   : '000000',
           'AND'    : '000000',
           'ANDI'   : '001100',
           'BEQ'    : '000100',
           'BGEZ'   : '000001',
           'BGEZAL' : '000001',
           'BGTZ'   : '000111',
           'BLEZ'   : '000110',
           'BLTZ'   : '000001',
           'BLTZAL' : '000001',
           'BNE'    : '000101',
           'DIV'    : '000000',
           'DIVU'   : '000000',
           'J'      : '000010',
           'JALR'   : '000000',
           'JAL'    : '000011',
           'JR'     : '000000',
           'LB'     : '100000',
           'LBU'    : '100100',
           'LH'     : '100001',
           'LHU'    : '100101',
           'LUI'    : '001111',
           'LW'     : '100011',
           'LWL'    : '100010',
           'LWR'    : '100110',
           'MFHI'   : '000000',
           'MFLO'   : '000000',
           'MTHI'   : '000000',
           'MTLO'   : '000000',
           'MULT'   : '000000',
           'MULTU'  : '000000',
           'OR'     : '000000',
           'ORI'    : '001101',
           'SB'     : '101000',
           'SH'     : '101001',
           'SLL'    : '000000',
           'SLLV'   : '000000',
           'SLT'    : '000000',
           'SLTI'   : '001010',
           'SLTIU'  : '001011',
           'SLTU'   : '000000',
           'SRA'    : '000000',
           'SRAV'   : '000000',
           'SRL'    : '000000',
           'SRLV'   : '000000',
           'SUBU'   : '000000',
           'SW'     : '101011',
           'XOR'    : '000000',
           'XORI'   : '001110'
           }

funct_codes = {'ADDU'  : '100001',
               'AND'   : '100100',
               'DIV'   : '011010',
               'DIVU'  : '011011',
               'JALR'  : '001001',
               'JR'    : '001000',
               'MFHI'  : '010000',
               'MFLO'  : '010010',
               'MTHI'  : '010001',
               'MTLO'  : '010011',
               'MULT'  : '011000',
               'MULTU' : '011001',
               'OR'    : '100101',
               'SLL'   : '000000',
               'SLLV'  : '000100',
               'SLT'   : '101010',
               'SLTU'  : '101011',
               'SRA'   : '000011',
               'SRAV'  : '000111',
               'SRL'   : '000010',
               'SRLV'  : '000110',
               'SUBU'  : '100011',
               'XOR'   : '100110'
               }

br_z_codes = {
        'BGEZ'   : '00001',
        'BGEZAL' : '10001',
        'BLTZ'   : '00000',
        'BLTZAL' : '10000',
        'BGTZ'   : '00000',
        'BLEZ'   : '00000'
        }

def to_bin(n,l): return bin(n & 2**l - 1)[2:].zfill(l)

def map(address):
    assert(address >= 0 and address < 4294967296)
    if address < 1024: return address
    elif address < 2147485696: return (address + 1024) % 8192
    elif address < 3217033216: return (address + 5120) % 8192
    else: return address % 8192

def unmap(mapped_addr):
    assert(mapped_addr >= 0 and mapped_addr < 8192)
    if mapped_addr < 1024: return mapped_addr
    elif mapped_addr < 3072: return mapped_addr + 2147482624
    elif mapped_addr < 7168: return mapped_addr + 3217026048
    else: return mapped_addr + 4294959104


def asm_to_hex(asm_dir, hex_dir):
    try: v = (sys.argv[3] == '-v')
    except: v = False
    asm_file = open(asm_dir)
    hex_file = open(hex_dir,'w')
    asm_in = asm_file.readlines()

    instr_lines = []
    data_lines = {}
    line_count = 0

    comment = False

    for i,line in enumerate(asm_in):
        if '/*' in line: comment = True
        if ('*/' in line) and (line.find('/*') < line.find('*/')): comment = False
        if (i < 11) or comment: continue     # The first 11 lines are comments only

        split = [x.replace('$','').replace(',','') for x in line.split()]
        if len(split) == 0: continue
        if split[0].upper() in opcodes:
            instr_lines.append(split)
        elif split[0].upper() == "DATA":
            data = hex(int(to_bin(int(split[2]),32),2))[2:].zfill(8)
            data_lines[int(split[1][2:],16)] = data[-2:]
            data_lines[int(split[1][2:],16)+1] = data[4:6]
            data_lines[int(split[1][2:],16)+2] = data[2:4]
            data_lines[int(split[1][2:],16)+3] = data[:2]
        elif line[0] not in ['#', '\n', '-']:
            print(line)
            raise Exception("Couldn't parse")

    for i in range(5120):
        if unmap(i) in data_lines.keys():
            hex_file.write(data_lines[unmap(i)] + '\n')
        else:
            hex_file.write('00\n')

    for line in instr_lines:
        opcode = opcodes[line[0].upper()]
        if line[0].upper() in ['ADDIU', 'ANDI', 'ORI', 'SLTI', 'SLTIU', 'XORI']:
            Rt = int(line[1])
            Rs = int(line[2])
            imm = int(line[3])
            hex_line = hex(int(opcode + to_bin(Rs,5) + to_bin(Rt,5) + to_bin(imm,16),2))
        elif line[0].upper() in ['ADDU', 'AND', 'OR', 'SLT', 'SLTU', 'SUBU', 'XOR']:
            Rd = int(line[1])
            Rs = int(line[2])
            Rt = int(line[3])
            hex_line = hex(int(opcode + to_bin(Rs,5) + to_bin(Rt,5) + to_bin(Rd,5) + '00000' + funct_codes[line[0].upper()],2))
        elif line[0].upper() == 'LUI':
            Rt = int(line[1])
            imm = int(line[2])
            hex_line = hex(int(opcode + '00000' + to_bin(Rt,5) + to_bin(imm,16),2))
        elif line[0].upper() in ['SLL', 'SRA', 'SRL']:
            Rd = int(line[1])
            Rt = int(line[2])
            shamt = int(line[3])
            hex_line = hex(int(opcode + '00000' + to_bin(Rt,5) + to_bin(Rd,5) + to_bin(shamt,5) + funct_codes[line[0].upper()],2))
        elif line[0].upper() in ['SLLV', 'SRAV', 'SRLV']:
            Rd = int(line[1])
            Rt = int(line[2])
            Rs = int(line[3])
            hex_line = hex(int(opcode + to_bin(Rs,5) + to_bin(Rt,5) + to_bin(Rd,5) + '00000' + funct_codes[line[0].upper()],2))
        elif line[0].upper() in ['DIV', 'DIVU', 'MULT', 'MULTU']:
            Rs = int(line[1])
            Rt = int(line[2])
            hex_line = hex(int(opcode + to_bin(Rs,5) + to_bin(Rt,5) + '0000000000' + funct_codes[line[0].upper()],2))
        elif line[0].upper() in ['MFHI', 'MFLO']:
            Rd = int(line[1])
            hex_line = hex(int(opcode + '0000000000' + to_bin(Rd,5) + '00000' + funct_codes[line[0].upper()],2))
        elif line[0].upper() in ['MTHI', 'MTLO']:
            Rs = int(line[1])
            hex_line = hex(int(opcode + to_bin(Rs,5) + '000000000000000' + funct_codes[line[0].upper()],2))
        elif line[0].upper() in ['BEQ', 'BNE']:
            Rs = int(line[1])
            Rt = int(line[2])
            offset = int(line[3])
            hex_line = hex(int(opcode + to_bin(Rs,5) + to_bin(Rt,5) + to_bin(offset,16),2))
        elif line[0].upper() in ['BGEZ', 'BGEZAL', 'BGTZ', 'BLEZ', 'BLTZ', 'BLTZAL']:
            Rs = int(line[1])
            offset = int(line[2])
            hex_line = hex(int(opcode + to_bin(Rs,5) + br_z_codes[line[0].upper()] + to_bin(offset,16),2))
        elif line[0].upper() in ['J', 'JAL']:
            target = int(line[1])
            hex_line = hex(int(opcode + to_bin(target,26),2))
        elif line[0].upper() in ['JR', 'JALR']:
            Rs = int(line[1])
            if len(line) == 3: Rd = int(line[2])
            elif line[0].upper() == 'JALR': Rd = 31
            else: Rd = 0
            hex_line = hex(int(opcode + to_bin(Rs,5) + '00000' + to_bin(Rd,5) + '00000' + funct_codes[line[0].upper()],2))
        elif line[0].upper() in ['LB', 'LBU', 'LH', 'LHU', 'LW', 'LWL', 'LWR', 'SB', 'SH', 'SW']:
            Rt = int(line[1])
            offset = int(line[2].split('(')[0])
            Rs = int(line[2].split('(')[1].replace(')',''))
            hex_line = hex(int(opcode + to_bin(Rs,5) + to_bin(Rt,5) + to_bin(offset,16),2))
        hex_line = hex_line.split('x')[-1].zfill(8) + 'h'

        if v: print(', '.join(line).ljust(20, ' '), hex_line)

        for i in range(4):
            # print(hex_line[-2*i-3:-2*i-1])
            hex_file.write(hex_line[-2*i-3:-2*i-1]+'\n')
            line_count += 1


    for i in range(8192 - (line_count + 5120)):
        if unmap(i + line_count + 5120) in data_lines.keys():
            hex_file.write(data_lines[unmap(i + line_count + 5120)] + '\n')
        else:
            hex_file.write('00\n')

    for line in data_lines.items(): print("ADDRESS: 0x" + hex(line[0])[2:].zfill(8) + ", DATA: 0x" + line[1].zfill(2))

for filename in os.listdir(sys.argv[1]):
    if filename.endswith(".asm.txt"):
        print(os.path.join(sys.argv[1], filename))
        asm_to_hex(os.path.join(sys.argv[1], filename), os.path.join(sys.argv[2], filename.replace('asm','hex')))
