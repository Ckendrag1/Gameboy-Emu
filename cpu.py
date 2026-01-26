"""
Game Boy CPU (Sharp LR35902)
Modified Z80 processor with custom instruction set
"""

class CPU:
    """Game Boy CPU - Sharp LR35902"""
    
    # Flag bit positions
    FLAG_Z = 7  # Zero flag
    FLAG_N = 6  # Subtract flag
    FLAG_H = 5  # Half-carry flag
    FLAG_C = 4  # Carry flag
    
    def __init__(self, memory):
        self.memory = memory
        
        # 8-bit registers
        self.a = 0x01  # Accumulator
        self.f = 0xB0  # Flags (Zero, Subtract, Half-carry, Carry)
        self.b = 0x00
        self.c = 0x13
        self.d = 0x00
        self.e = 0xD8
        self.h = 0x01
        self.l = 0x4D
        
        # 16-bit registers
        self.sp = 0xFFFE  # Stack Pointer
        self.pc = 0x0100  # Program Counter (starts at 0x0100 after boot ROM)
        
        # Control flags
        self.ime = False  # Interrupt Master Enable
        self.halted = False
        self.stopped = False
        
        # Cycle counter
        self.cycles = 0
    
    # === FLAG OPERATIONS ===
    
    def get_flag(self, flag):
        """Get flag value"""
        return (self.f >> flag) & 1
    
    def set_flag(self, flag, value):
        """Set flag value"""
        if value:
            self.f |= (1 << flag)
        else:
            self.f &= ~(1 << flag)
    
    # === 16-BIT REGISTER PAIRS ===
    
    def get_bc(self):
        return (self.b << 8) | self.c
    
    def set_bc(self, value):
        self.b = (value >> 8) & 0xFF
        self.c = value & 0xFF
    
    def get_de(self):
        return (self.d << 8) | self.e
    
    def set_de(self, value):
        self.d = (value >> 8) & 0xFF
        self.e = value & 0xFF
    
    def get_hl(self):
        return (self.h << 8) | self.l
    
    def set_hl(self, value):
        self.h = (value >> 8) & 0xFF
        self.l = value & 0xFF
    
    def get_af(self):
        return (self.a << 8) | self.f
    
    def set_af(self, value):
        self.a = (value >> 8) & 0xFF
        self.f = value & 0xF0  # Lower 4 bits always 0
    
    # === MEMORY ACCESS ===
    
    def fetch_byte(self):
        """Fetch next byte and increment PC"""
        byte = self.memory.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return byte
    
    def fetch_word(self):
        """Fetch next word and increment PC"""
        word = self.memory.read_word(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        return word
    
    # === STACK OPERATIONS ===
    
    def push_word(self, value):
        """Push word onto stack"""
        self.sp = (self.sp - 2) & 0xFFFF
        self.memory.write_word(self.sp, value)
    
    def pop_word(self):
        """Pop word from stack"""
        value = self.memory.read_word(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        return value
    
    # === INSTRUCTION EXECUTION ===
    
    def step(self):
        """Execute one instruction"""
        if self.halted:
            self.cycles += 4
            # TODO: Check for interrupts to wake from halt
            return
        
        if self.stopped:
            # TODO: Wake from stop on button press
            return
        
        opcode = self.fetch_byte()
        self.execute_opcode(opcode)
    
    def execute_opcode(self, opcode):
        """Execute a single opcode"""
        
        # 0x0X - Misc/control operations
        if opcode == 0x00:  # NOP
            self.cycles += 4
        
        elif opcode == 0x01:  # LD BC,nn
            self.set_bc(self.fetch_word())
            self.cycles += 12
        
        elif opcode == 0x02:  # LD (BC),A
            self.memory.write_byte(self.get_bc(), self.a)
            self.cycles += 8
        
        elif opcode == 0x03:  # INC BC
            self.set_bc((self.get_bc() + 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x04:  # INC B
            self.b = self.inc_8bit(self.b)
            self.cycles += 4
        
        elif opcode == 0x05:  # DEC B
            self.b = self.dec_8bit(self.b)
            self.cycles += 4
        
        elif opcode == 0x06:  # LD B,n
            self.b = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x07:  # RLCA
            carry = (self.a >> 7) & 1
            self.a = ((self.a << 1) | carry) & 0xFF
            self.set_flag(self.FLAG_Z, 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 4
        
        elif opcode == 0x08:  # LD (nn),SP
            addr = self.fetch_word()
            self.memory.write_word(addr, self.sp)
            self.cycles += 20
        
        elif opcode == 0x09:  # ADD HL,BC
            self.add_hl(self.get_bc())
            self.cycles += 8
        
        elif opcode == 0x0A:  # LD A,(BC)
            self.a = self.memory.read_byte(self.get_bc())
            self.cycles += 8
        
        elif opcode == 0x0B:  # DEC BC
            self.set_bc((self.get_bc() - 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x0C:  # INC C
            self.c = self.inc_8bit(self.c)
            self.cycles += 4
        
        elif opcode == 0x0D:  # DEC C
            self.c = self.dec_8bit(self.c)
            self.cycles += 4
        
        elif opcode == 0x0E:  # LD C,n
            self.c = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x0F:  # RRCA
            carry = self.a & 1
            self.a = ((self.a >> 1) | (carry << 7)) & 0xFF
            self.set_flag(self.FLAG_Z, 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 4
        
        # 0x1X
        elif opcode == 0x11:  # LD DE,nn
            self.set_de(self.fetch_word())
            self.cycles += 12
        
        elif opcode == 0x12:  # LD (DE),A
            self.memory.write_byte(self.get_de(), self.a)
            self.cycles += 8
        
        elif opcode == 0x13:  # INC DE
            self.set_de((self.get_de() + 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x14:  # INC D
            self.d = self.inc_8bit(self.d)
            self.cycles += 4
        
        elif opcode == 0x15:  # DEC D
            self.d = self.dec_8bit(self.d)
            self.cycles += 4
        
        elif opcode == 0x16:  # LD D,n
            self.d = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x17:  # RLA
            carry = self.get_flag(self.FLAG_C)
            new_carry = (self.a >> 7) & 1
            self.a = ((self.a << 1) | carry) & 0xFF
            self.set_flag(self.FLAG_Z, 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, new_carry)
            self.cycles += 4
        
        elif opcode == 0x18:  # JR n
            offset = self.fetch_byte()
            if offset > 127:
                offset = offset - 256
            self.pc = (self.pc + offset) & 0xFFFF
            self.cycles += 12
        
        elif opcode == 0x19:  # ADD HL,DE
            self.add_hl(self.get_de())
            self.cycles += 8
        
        elif opcode == 0x1A:  # LD A,(DE)
            self.a = self.memory.read_byte(self.get_de())
            self.cycles += 8
        
        elif opcode == 0x1B:  # DEC DE
            self.set_de((self.get_de() - 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x1C:  # INC E
            self.e = self.inc_8bit(self.e)
            self.cycles += 4
        
        elif opcode == 0x1D:  # DEC E
            self.e = self.dec_8bit(self.e)
            self.cycles += 4
        
        elif opcode == 0x1E:  # LD E,n
            self.e = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x1F:  # RRA
            carry = self.get_flag(self.FLAG_C)
            new_carry = self.a & 1
            self.a = ((self.a >> 1) | (carry << 7)) & 0xFF
            self.set_flag(self.FLAG_Z, 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, new_carry)
            self.cycles += 4
        
        # 0x2X
        elif opcode == 0x20:  # JR NZ,n
            offset = self.fetch_byte()
            if not self.get_flag(self.FLAG_Z):
                if offset > 127:
                    offset = offset - 256
                self.pc = (self.pc + offset) & 0xFFFF
                self.cycles += 12
            else:
                self.cycles += 8
        
        elif opcode == 0x21:  # LD HL,nn
            self.set_hl(self.fetch_word())
            self.cycles += 12
        
        elif opcode == 0x22:  # LD (HL+),A / LDI (HL),A
            self.memory.write_byte(self.get_hl(), self.a)
            self.set_hl((self.get_hl() + 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x23:  # INC HL
            self.set_hl((self.get_hl() + 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x24:  # INC H
            self.h = self.inc_8bit(self.h)
            self.cycles += 4
        
        elif opcode == 0x25:  # DEC H
            self.h = self.dec_8bit(self.h)
            self.cycles += 4
        
        elif opcode == 0x26:  # LD H,n
            self.h = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x28:  # JR Z,n
            offset = self.fetch_byte()
            if self.get_flag(self.FLAG_Z):
                if offset > 127:
                    offset = offset - 256
                self.pc = (self.pc + offset) & 0xFFFF
                self.cycles += 12
            else:
                self.cycles += 8
        
        elif opcode == 0x29:  # ADD HL,HL
            self.add_hl(self.get_hl())
            self.cycles += 8
        
        elif opcode == 0x2A:  # LD A,(HL+) / LDI A,(HL)
            self.a = self.memory.read_byte(self.get_hl())
            self.set_hl((self.get_hl() + 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x2B:  # DEC HL
            self.set_hl((self.get_hl() - 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x2C:  # INC L
            self.l = self.inc_8bit(self.l)
            self.cycles += 4
        
        elif opcode == 0x2D:  # DEC L
            self.l = self.dec_8bit(self.l)
            self.cycles += 4
        
        elif opcode == 0x2E:  # LD L,n
            self.l = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x2F:  # CPL (complement A)
            self.a ^= 0xFF
            self.set_flag(self.FLAG_N, 1)
            self.set_flag(self.FLAG_H, 1)
            self.cycles += 4
        
        # 0x3X
        elif opcode == 0x30:  # JR NC,n
            offset = self.fetch_byte()
            if not self.get_flag(self.FLAG_C):
                if offset > 127:
                    offset = offset - 256
                self.pc = (self.pc + offset) & 0xFFFF
                self.cycles += 12
            else:
                self.cycles += 8
        
        elif opcode == 0x31:  # LD SP,nn
            self.sp = self.fetch_word()
            self.cycles += 12
        
        elif opcode == 0x32:  # LD (HL-),A / LDD (HL),A
            self.memory.write_byte(self.get_hl(), self.a)
            self.set_hl((self.get_hl() - 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x33:  # INC SP
            self.sp = (self.sp + 1) & 0xFFFF
            self.cycles += 8
        
        elif opcode == 0x34:  # INC (HL)
            addr = self.get_hl()
            value = self.memory.read_byte(addr)
            result = self.inc_8bit(value)
            self.memory.write_byte(addr, result)
            self.cycles += 12
        
        elif opcode == 0x35:  # DEC (HL)
            addr = self.get_hl()
            value = self.memory.read_byte(addr)
            result = self.dec_8bit(value)
            self.memory.write_byte(addr, result)
            self.cycles += 12
        
        elif opcode == 0x36:  # LD (HL),n
            self.memory.write_byte(self.get_hl(), self.fetch_byte())
            self.cycles += 12
        
        elif opcode == 0x37:  # SCF (set carry flag)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, 1)
            self.cycles += 4
        
        elif opcode == 0x38:  # JR C,n
            offset = self.fetch_byte()
            if self.get_flag(self.FLAG_C):
                if offset > 127:
                    offset = offset - 256
                self.pc = (self.pc + offset) & 0xFFFF
                self.cycles += 12
            else:
                self.cycles += 8
        
        elif opcode == 0x39:  # ADD HL,SP
            self.add_hl(self.sp)
            self.cycles += 8
        
        elif opcode == 0x3A:  # LD A,(HL-) / LDD A,(HL)
            self.a = self.memory.read_byte(self.get_hl())
            self.set_hl((self.get_hl() - 1) & 0xFFFF)
            self.cycles += 8
        
        elif opcode == 0x3B:  # DEC SP
            self.sp = (self.sp - 1) & 0xFFFF
            self.cycles += 8
        
        elif opcode == 0x3C:  # INC A
            self.a = self.inc_8bit(self.a)
            self.cycles += 4
        
        elif opcode == 0x3D:  # DEC A
            self.a = self.dec_8bit(self.a)
            self.cycles += 4
        
        elif opcode == 0x3E:  # LD A,n
            self.a = self.fetch_byte()
            self.cycles += 8
        
        elif opcode == 0x3F:  # CCF (complement carry flag)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, not self.get_flag(self.FLAG_C))
            self.cycles += 4
        
        # 0x4X-0x7X - 8-bit LD instructions (LD r,r)
        elif 0x40 <= opcode <= 0x7F:
            if opcode == 0x76:  # HALT
                self.halted = True
                self.cycles += 4
            else:
                self.ld_r_r(opcode)
        
        # 0x80-0x8F - ADD/ADC
        elif 0x80 <= opcode <= 0x87:  # ADD A,r
            self.add_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        elif 0x88 <= opcode <= 0x8F:  # ADC A,r
            self.adc_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        # 0x90-0x9F - SUB/SBC
        elif 0x90 <= opcode <= 0x97:  # SUB r
            self.sub_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        elif 0x98 <= opcode <= 0x9F:  # SBC A,r
            self.sbc_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        # 0xA0-0xAF - AND/XOR
        elif 0xA0 <= opcode <= 0xA7:  # AND r
            self.and_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        elif 0xA8 <= opcode <= 0xAF:  # XOR r
            self.xor_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        # 0xB0-0xBF - OR/CP
        elif 0xB0 <= opcode <= 0xB7:  # OR r
            self.or_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        elif 0xB8 <= opcode <= 0xBF:  # CP r
            self.cp_a(self.get_reg8(opcode & 0x07))
            self.cycles += 4 if (opcode & 0x07) != 6 else 8
        
        # 0xCX
        elif opcode == 0xC0:  # RET NZ
            if not self.get_flag(self.FLAG_Z):
                self.pc = self.pop_word()
                self.cycles += 20
            else:
                self.cycles += 8
        
        elif opcode == 0xC1:  # POP BC
            self.set_bc(self.pop_word())
            self.cycles += 12
        
        elif opcode == 0xC2:  # JP NZ,nn
            addr = self.fetch_word()
            if not self.get_flag(self.FLAG_Z):
                self.pc = addr
                self.cycles += 16
            else:
                self.cycles += 12
        
        elif opcode == 0xC3:  # JP nn
            self.pc = self.fetch_word()
            self.cycles += 16
        
        elif opcode == 0xC4:  # CALL NZ,nn
            addr = self.fetch_word()
            if not self.get_flag(self.FLAG_Z):
                self.push_word(self.pc)
                self.pc = addr
                self.cycles += 24
            else:
                self.cycles += 12
        
        elif opcode == 0xC5:  # PUSH BC
            self.push_word(self.get_bc())
            self.cycles += 16
        
        elif opcode == 0xC6:  # ADD A,n
            self.add_a(self.fetch_byte())
            self.cycles += 8
        
        elif opcode == 0xC8:  # RET Z
            if self.get_flag(self.FLAG_Z):
                self.pc = self.pop_word()
                self.cycles += 20
            else:
                self.cycles += 8
        
        elif opcode == 0xC9:  # RET
            self.pc = self.pop_word()
            self.cycles += 16
        
        elif opcode == 0xCA:  # JP Z,nn
            addr = self.fetch_word()
            if self.get_flag(self.FLAG_Z):
                self.pc = addr
                self.cycles += 16
            else:
                self.cycles += 12
        
        elif opcode == 0xCB:  # PREFIX CB
            cb_opcode = self.fetch_byte()
            self.execute_cb_opcode(cb_opcode)
        
        elif opcode == 0xCC:  # CALL Z,nn
            addr = self.fetch_word()
            if self.get_flag(self.FLAG_Z):
                self.push_word(self.pc)
                self.pc = addr
                self.cycles += 24
            else:
                self.cycles += 12
        
        elif opcode == 0xCD:  # CALL nn
            addr = self.fetch_word()
            self.push_word(self.pc)
            self.pc = addr
            self.cycles += 24
        
        elif opcode == 0xCE:  # ADC A,n
            self.adc_a(self.fetch_byte())
            self.cycles += 8
        
        # 0xDX
        elif opcode == 0xD0:  # RET NC
            if not self.get_flag(self.FLAG_C):
                self.pc = self.pop_word()
                self.cycles += 20
            else:
                self.cycles += 8
        
        elif opcode == 0xD1:  # POP DE
            self.set_de(self.pop_word())
            self.cycles += 12
        
        elif opcode == 0xD2:  # JP NC,nn
            addr = self.fetch_word()
            if not self.get_flag(self.FLAG_C):
                self.pc = addr
                self.cycles += 16
            else:
                self.cycles += 12
        
        elif opcode == 0xD4:  # CALL NC,nn
            addr = self.fetch_word()
            if not self.get_flag(self.FLAG_C):
                self.push_word(self.pc)
                self.pc = addr
                self.cycles += 24
            else:
                self.cycles += 12
        
        elif opcode == 0xD5:  # PUSH DE
            self.push_word(self.get_de())
            self.cycles += 16
        
        elif opcode == 0xD6:  # SUB n
            self.sub_a(self.fetch_byte())
            self.cycles += 8
        
        elif opcode == 0xD8:  # RET C
            if self.get_flag(self.FLAG_C):
                self.pc = self.pop_word()
                self.cycles += 20
            else:
                self.cycles += 8
        
        elif opcode == 0xD9:  # RETI
            self.pc = self.pop_word()
            self.ime = True
            self.cycles += 16
        
        elif opcode == 0xDA:  # JP C,nn
            addr = self.fetch_word()
            if self.get_flag(self.FLAG_C):
                self.pc = addr
                self.cycles += 16
            else:
                self.cycles += 12
        
        elif opcode == 0xDC:  # CALL C,nn
            addr = self.fetch_word()
            if self.get_flag(self.FLAG_C):
                self.push_word(self.pc)
                self.pc = addr
                self.cycles += 24
            else:
                self.cycles += 12
        
        elif opcode == 0xDE:  # SBC A,n
            self.sbc_a(self.fetch_byte())
            self.cycles += 8
        
        # 0xEX
        elif opcode == 0xE0:  # LDH (n),A
            self.memory.write_byte(0xFF00 + self.fetch_byte(), self.a)
            self.cycles += 12
        
        elif opcode == 0xE1:  # POP HL
            self.set_hl(self.pop_word())
            self.cycles += 12
        
        elif opcode == 0xE2:  # LD (C),A
            self.memory.write_byte(0xFF00 + self.c, self.a)
            self.cycles += 8
        
        elif opcode == 0xE5:  # PUSH HL
            self.push_word(self.get_hl())
            self.cycles += 16
        
        elif opcode == 0xE6:  # AND n
            self.and_a(self.fetch_byte())
            self.cycles += 8
        
        elif opcode == 0xE9:  # JP (HL)
            self.pc = self.get_hl()
            self.cycles += 4
        
        elif opcode == 0xEA:  # LD (nn),A
            self.memory.write_byte(self.fetch_word(), self.a)
            self.cycles += 16
        
        elif opcode == 0xEE:  # XOR n
            self.xor_a(self.fetch_byte())
            self.cycles += 8
        
        # 0xFX
        elif opcode == 0xF0:  # LDH A,(n)
            self.a = self.memory.read_byte(0xFF00 + self.fetch_byte())
            self.cycles += 12
        
        elif opcode == 0xF1:  # POP AF
            self.set_af(self.pop_word())
            self.cycles += 12
        
        elif opcode == 0xF2:  # LD A,(C)
            self.a = self.memory.read_byte(0xFF00 + self.c)
            self.cycles += 8
        
        elif opcode == 0xF3:  # DI (disable interrupts)
            self.ime = False
            self.cycles += 4
        
        elif opcode == 0xF5:  # PUSH AF
            self.push_word(self.get_af())
            self.cycles += 16
        
        elif opcode == 0xF6:  # OR n
            self.or_a(self.fetch_byte())
            self.cycles += 8
        
        elif opcode == 0xFA:  # LD A,(nn)
            self.a = self.memory.read_byte(self.fetch_word())
            self.cycles += 16
        
        elif opcode == 0xFB:  # EI (enable interrupts)
            self.ime = True
            self.cycles += 4
        
        elif opcode == 0xFE:  # CP n
            self.cp_a(self.fetch_byte())
            self.cycles += 8
        
        else:
            print(f"[CPU] Unimplemented opcode: 0x{opcode:02X} at PC: 0x{self.pc-1:04X}")
            self.cycles += 4
    
    def execute_cb_opcode(self, opcode):
        """Execute CB-prefixed opcodes (bit operations)"""
        # Extract register index (bits 0-2)
        reg_idx = opcode & 0x07
        
        # RLC r (0x00-0x07)
        if 0x00 <= opcode <= 0x07:
            value = self.get_reg8(reg_idx)
            carry = (value >> 7) & 1
            result = ((value << 1) | carry) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # RRC r (0x08-0x0F)
        elif 0x08 <= opcode <= 0x0F:
            value = self.get_reg8(reg_idx)
            carry = value & 1
            result = ((value >> 1) | (carry << 7)) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # RL r (0x10-0x17)
        elif 0x10 <= opcode <= 0x17:
            value = self.get_reg8(reg_idx)
            carry = self.get_flag(self.FLAG_C)
            new_carry = (value >> 7) & 1
            result = ((value << 1) | carry) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, new_carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # RR r (0x18-0x1F)
        elif 0x18 <= opcode <= 0x1F:
            value = self.get_reg8(reg_idx)
            carry = self.get_flag(self.FLAG_C)
            new_carry = value & 1
            result = ((value >> 1) | (carry << 7)) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, new_carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # SLA r (0x20-0x27)
        elif 0x20 <= opcode <= 0x27:
            value = self.get_reg8(reg_idx)
            carry = (value >> 7) & 1
            result = (value << 1) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # SRA r (0x28-0x2F)
        elif 0x28 <= opcode <= 0x2F:
            value = self.get_reg8(reg_idx)
            carry = value & 1
            result = ((value >> 1) | (value & 0x80)) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # SWAP r (0x30-0x37)
        elif 0x30 <= opcode <= 0x37:
            value = self.get_reg8(reg_idx)
            result = ((value & 0x0F) << 4) | ((value & 0xF0) >> 4)
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, 0)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # SRL r (0x38-0x3F)
        elif 0x38 <= opcode <= 0x3F:
            value = self.get_reg8(reg_idx)
            carry = value & 1
            result = (value >> 1) & 0xFF
            self.set_reg8(reg_idx, result)
            self.set_flag(self.FLAG_Z, result == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 0)
            self.set_flag(self.FLAG_C, carry)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # BIT n,r (0x40-0x7F)
        elif 0x40 <= opcode <= 0x7F:
            bit = (opcode >> 3) & 0x07
            value = self.get_reg8(reg_idx)
            self.set_flag(self.FLAG_Z, (value & (1 << bit)) == 0)
            self.set_flag(self.FLAG_N, 0)
            self.set_flag(self.FLAG_H, 1)
            self.cycles += 8 if reg_idx != 6 else 12
        
        # RES n,r (0x80-0xBF)
        elif 0x80 <= opcode <= 0xBF:
            bit = (opcode >> 3) & 0x07
            value = self.get_reg8(reg_idx)
            result = value & ~(1 << bit)
            self.set_reg8(reg_idx, result)
            self.cycles += 8 if reg_idx != 6 else 16
        
        # SET n,r (0xC0-0xFF)
        elif 0xC0 <= opcode <= 0xFF:
            bit = (opcode >> 3) & 0x07
            value = self.get_reg8(reg_idx)
            result = value | (1 << bit)
            self.set_reg8(reg_idx, result)
            self.cycles += 8 if reg_idx != 6 else 16
        
        else:
            print(f"[CPU] Unimplemented CB opcode: 0x{opcode:02X}")
            self.cycles += 8
    
    # === HELPER FUNCTIONS ===
    
    def get_reg8(self, index):
        """Get 8-bit register by index (0-7: B,C,D,E,H,L,(HL),A)"""
        if index == 0:
            return self.b
        elif index == 1:
            return self.c
        elif index == 2:
            return self.d
        elif index == 3:
            return self.e
        elif index == 4:
            return self.h
        elif index == 5:
            return self.l
        elif index == 6:
            return self.memory.read_byte(self.get_hl())
        elif index == 7:
            return self.a
    
    def set_reg8(self, index, value):
        """Set 8-bit register by index"""
        value &= 0xFF
        if index == 0:
            self.b = value
        elif index == 1:
            self.c = value
        elif index == 2:
            self.d = value
        elif index == 3:
            self.e = value
        elif index == 4:
            self.h = value
        elif index == 5:
            self.l = value
        elif index == 6:
            self.memory.write_byte(self.get_hl(), value)
        elif index == 7:
            self.a = value
    
    def ld_r_r(self, opcode):
        """Handle LD r,r instructions (0x40-0x7F except 0x76)"""
        dst = (opcode >> 3) & 0x07
        src = opcode & 0x07
        value = self.get_reg8(src)
        self.set_reg8(dst, value)
        
        # Timing: 4 cycles for reg-reg, 8 if (HL) is involved
        if src == 6 or dst == 6:
            self.cycles += 8
        else:
            self.cycles += 4
    
    def inc_8bit(self, value):
        """8-bit increment with flags"""
        result = (value + 1) & 0xFF
        self.set_flag(self.FLAG_Z, result == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, (value & 0x0F) == 0x0F)
        return result
    
    def dec_8bit(self, value):
        """8-bit decrement with flags"""
        result = (value - 1) & 0xFF
        self.set_flag(self.FLAG_Z, result == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (value & 0x0F) == 0)
        return result
    
    def add_a(self, value):
        """Add to accumulator with flags"""
        result = self.a + value
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((self.a & 0xF) + (value & 0xF)) > 0xF)
        self.set_flag(self.FLAG_C, result > 0xFF)
        self.a = result & 0xFF
    
    def adc_a(self, value):
        """Add with carry to accumulator"""
        carry = self.get_flag(self.FLAG_C)
        result = self.a + value + carry
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((self.a & 0xF) + (value & 0xF) + carry) > 0xF)
        self.set_flag(self.FLAG_C, result > 0xFF)
        self.a = result & 0xFF
    
    def sub_a(self, value):
        """Subtract from accumulator"""
        result = self.a - value
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (self.a & 0xF) < (value & 0xF))
        self.set_flag(self.FLAG_C, result < 0)
        self.a = result & 0xFF
    
    def sbc_a(self, value):
        """Subtract with carry from accumulator"""
        carry = self.get_flag(self.FLAG_C)
        result = self.a - value - carry
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (self.a & 0xF) < ((value & 0xF) + carry))
        self.set_flag(self.FLAG_C, result < 0)
        self.a = result & 0xFF
    
    def and_a(self, value):
        """AND with accumulator"""
        self.a &= value
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 1)
        self.set_flag(self.FLAG_C, 0)
    
    def xor_a(self, value):
        """XOR with accumulator"""
        self.a ^= value
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, 0)
    
    def or_a(self, value):
        """OR with accumulator"""
        self.a |= value
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, 0)
    
    def cp_a(self, value):
        """Compare with accumulator (like SUB but don't store result)"""
        result = self.a - value
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (self.a & 0xF) < (value & 0xF))
        self.set_flag(self.FLAG_C, result < 0)
    
    def add_hl(self, value):
        """Add to HL register with flags"""
        hl = self.get_hl()
        result = hl + value
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((hl & 0xFFF) + (value & 0xFFF)) > 0xFFF)
        self.set_flag(self.FLAG_C, result > 0xFFFF)
        self.set_hl(result & 0xFFFF)