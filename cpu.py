"""
Game Boy CPU (Sharp LR35902) - COMPLETE IMPLEMENTATION
All 512 opcodes (256 regular + 256 CB-prefixed)
"""

class CPU:
    """Game Boy CPU - Sharp LR35902 - Complete"""
    
    # Flag bit positions
    FLAG_Z = 7  # Zero flag
    FLAG_N = 6  # Subtract flag
    FLAG_H = 5  # Half-carry flag
    FLAG_C = 4  # Carry flag
    
    def __init__(self, memory):
        self.memory = memory
        
        # 8-bit registers (initial values after boot ROM)
        self.a = 0x01
        self.f = 0xB0
        self.b = 0x00
        self.c = 0x13
        self.d = 0x00
        self.e = 0xD8
        self.h = 0x01
        self.l = 0x4D
        
        # 16-bit registers
        self.sp = 0xFFFE
        self.pc = 0x0100
        
        # Control flags
        self.ime = False  # Interrupt Master Enable
        self.halted = False
        self.stopped = False
        
        # Cycle counter
        self.cycles = 0
        
        # Build opcode tables for faster execution
        self.build_opcode_tables()
    
    def build_opcode_tables(self):
        """Build opcode lookup tables"""
        # Main opcode table
        self.opcode_table = [None] * 256
        # CB-prefixed opcode table
        self.cb_opcode_table = [None] * 256
        
        # We'll use the existing execute_opcode method
        # This is for future optimization
    
    # === FLAG OPERATIONS ===
    
    def get_flag(self, flag):
        return (self.f >> flag) & 1
    
    def set_flag(self, flag, value):
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
        self.f = value & 0xF0
    
    # === MEMORY ACCESS ===
    
    def fetch_byte(self):
        byte = self.memory.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return byte
    
    def fetch_word(self):
        word = self.memory.read_word(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        return word
    
    # === STACK OPERATIONS ===
    
    def push_word(self, value):
        self.sp = (self.sp - 2) & 0xFFFF
        self.memory.write_word(self.sp, value)
    
    def pop_word(self):
        value = self.memory.read_word(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        return value
    
    # === INSTRUCTION EXECUTION ===
    
    def step(self):
        if self.halted:
            self.cycles += 4
            return
        
        if self.stopped:
            return
        
        opcode = self.fetch_byte()
        self.execute_opcode(opcode)
    
    def execute_opcode(self, op):
        """Execute main opcodes - COMPLETE IMPLEMENTATION"""
        
        # 0x00-0x0F
        if op == 0x00: self.cycles += 4  # NOP
        elif op == 0x01: self.set_bc(self.fetch_word()); self.cycles += 12
        elif op == 0x02: self.memory.write_byte(self.get_bc(), self.a); self.cycles += 8
        elif op == 0x03: self.set_bc((self.get_bc() + 1) & 0xFFFF); self.cycles += 8
        elif op == 0x04: self.b = self.inc_8bit(self.b); self.cycles += 4
        elif op == 0x05: self.b = self.dec_8bit(self.b); self.cycles += 4
        elif op == 0x06: self.b = self.fetch_byte(); self.cycles += 8
        elif op == 0x07: self.rlca(); self.cycles += 4
        elif op == 0x08: addr = self.fetch_word(); self.memory.write_word(addr, self.sp); self.cycles += 20
        elif op == 0x09: self.add_hl(self.get_bc()); self.cycles += 8
        elif op == 0x0A: self.a = self.memory.read_byte(self.get_bc()); self.cycles += 8
        elif op == 0x0B: self.set_bc((self.get_bc() - 1) & 0xFFFF); self.cycles += 8
        elif op == 0x0C: self.c = self.inc_8bit(self.c); self.cycles += 4
        elif op == 0x0D: self.c = self.dec_8bit(self.c); self.cycles += 4
        elif op == 0x0E: self.c = self.fetch_byte(); self.cycles += 8
        elif op == 0x0F: self.rrca(); self.cycles += 4
        
        # 0x10-0x1F
        elif op == 0x10: self.stopped = True; self.fetch_byte(); self.cycles += 4
        elif op == 0x11: self.set_de(self.fetch_word()); self.cycles += 12
        elif op == 0x12: self.memory.write_byte(self.get_de(), self.a); self.cycles += 8
        elif op == 0x13: self.set_de((self.get_de() + 1) & 0xFFFF); self.cycles += 8
        elif op == 0x14: self.d = self.inc_8bit(self.d); self.cycles += 4
        elif op == 0x15: self.d = self.dec_8bit(self.d); self.cycles += 4
        elif op == 0x16: self.d = self.fetch_byte(); self.cycles += 8
        elif op == 0x17: self.rla(); self.cycles += 4
        elif op == 0x18: self.jr(); self.cycles += 12
        elif op == 0x19: self.add_hl(self.get_de()); self.cycles += 8
        elif op == 0x1A: self.a = self.memory.read_byte(self.get_de()); self.cycles += 8
        elif op == 0x1B: self.set_de((self.get_de() - 1) & 0xFFFF); self.cycles += 8
        elif op == 0x1C: self.e = self.inc_8bit(self.e); self.cycles += 4
        elif op == 0x1D: self.e = self.dec_8bit(self.e); self.cycles += 4
        elif op == 0x1E: self.e = self.fetch_byte(); self.cycles += 8
        elif op == 0x1F: self.rra(); self.cycles += 4
        
        # 0x20-0x2F
        elif op == 0x20: self.jr_cc(not self.get_flag(self.FLAG_Z))
        elif op == 0x21: self.set_hl(self.fetch_word()); self.cycles += 12
        elif op == 0x22: self.memory.write_byte(self.get_hl(), self.a); self.set_hl((self.get_hl() + 1) & 0xFFFF); self.cycles += 8
        elif op == 0x23: self.set_hl((self.get_hl() + 1) & 0xFFFF); self.cycles += 8
        elif op == 0x24: self.h = self.inc_8bit(self.h); self.cycles += 4
        elif op == 0x25: self.h = self.dec_8bit(self.h); self.cycles += 4
        elif op == 0x26: self.h = self.fetch_byte(); self.cycles += 8
        elif op == 0x27: self.daa(); self.cycles += 4
        elif op == 0x28: self.jr_cc(self.get_flag(self.FLAG_Z))
        elif op == 0x29: self.add_hl(self.get_hl()); self.cycles += 8
        elif op == 0x2A: self.a = self.memory.read_byte(self.get_hl()); self.set_hl((self.get_hl() + 1) & 0xFFFF); self.cycles += 8
        elif op == 0x2B: self.set_hl((self.get_hl() - 1) & 0xFFFF); self.cycles += 8
        elif op == 0x2C: self.l = self.inc_8bit(self.l); self.cycles += 4
        elif op == 0x2D: self.l = self.dec_8bit(self.l); self.cycles += 4
        elif op == 0x2E: self.l = self.fetch_byte(); self.cycles += 8
        elif op == 0x2F: self.a ^= 0xFF; self.set_flag(self.FLAG_N, 1); self.set_flag(self.FLAG_H, 1); self.cycles += 4
        
        # 0x30-0x3F
        elif op == 0x30: self.jr_cc(not self.get_flag(self.FLAG_C))
        elif op == 0x31: self.sp = self.fetch_word(); self.cycles += 12
        elif op == 0x32: self.memory.write_byte(self.get_hl(), self.a); self.set_hl((self.get_hl() - 1) & 0xFFFF); self.cycles += 8
        elif op == 0x33: self.sp = (self.sp + 1) & 0xFFFF; self.cycles += 8
        elif op == 0x34: addr = self.get_hl(); self.memory.write_byte(addr, self.inc_8bit(self.memory.read_byte(addr))); self.cycles += 12
        elif op == 0x35: addr = self.get_hl(); self.memory.write_byte(addr, self.dec_8bit(self.memory.read_byte(addr))); self.cycles += 12
        elif op == 0x36: self.memory.write_byte(self.get_hl(), self.fetch_byte()); self.cycles += 12
        elif op == 0x37: self.set_flag(self.FLAG_N, 0); self.set_flag(self.FLAG_H, 0); self.set_flag(self.FLAG_C, 1); self.cycles += 4
        elif op == 0x38: self.jr_cc(self.get_flag(self.FLAG_C))
        elif op == 0x39: self.add_hl(self.sp); self.cycles += 8
        elif op == 0x3A: self.a = self.memory.read_byte(self.get_hl()); self.set_hl((self.get_hl() - 1) & 0xFFFF); self.cycles += 8
        elif op == 0x3B: self.sp = (self.sp - 1) & 0xFFFF; self.cycles += 8
        elif op == 0x3C: self.a = self.inc_8bit(self.a); self.cycles += 4
        elif op == 0x3D: self.a = self.dec_8bit(self.a); self.cycles += 4
        elif op == 0x3E: self.a = self.fetch_byte(); self.cycles += 8
        elif op == 0x3F: self.set_flag(self.FLAG_N, 0); self.set_flag(self.FLAG_H, 0); self.set_flag(self.FLAG_C, not self.get_flag(self.FLAG_C)); self.cycles += 4
        
        # 0x40-0x7F - LD r,r instructions
        elif 0x40 <= op <= 0x75 or 0x77 <= op <= 0x7F:
            self.ld_r_r(op)
        elif op == 0x76: self.halted = True; self.cycles += 4  # HALT
        
        # 0x80-0xBF - ALU operations
        elif 0x80 <= op <= 0x87: self.add_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0x88 <= op <= 0x8F: self.adc_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0x90 <= op <= 0x97: self.sub_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0x98 <= op <= 0x9F: self.sbc_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0xA0 <= op <= 0xA7: self.and_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0xA8 <= op <= 0xAF: self.xor_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0xB0 <= op <= 0xB7: self.or_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        elif 0xB8 <= op <= 0xBF: self.cp_a(self.get_reg8(op & 7)); self.cycles += 4 if (op & 7) != 6 else 8
        
        # 0xC0-0xCF
        elif op == 0xC0: self.ret_cc(not self.get_flag(self.FLAG_Z))
        elif op == 0xC1: self.set_bc(self.pop_word()); self.cycles += 12
        elif op == 0xC2: self.jp_cc(not self.get_flag(self.FLAG_Z))
        elif op == 0xC3: self.pc = self.fetch_word(); self.cycles += 16
        elif op == 0xC4: self.call_cc(not self.get_flag(self.FLAG_Z))
        elif op == 0xC5: self.push_word(self.get_bc()); self.cycles += 16
        elif op == 0xC6: self.add_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xC7: self.rst(0x00)
        elif op == 0xC8: self.ret_cc(self.get_flag(self.FLAG_Z))
        elif op == 0xC9: self.pc = self.pop_word(); self.cycles += 16
        elif op == 0xCA: self.jp_cc(self.get_flag(self.FLAG_Z))
        elif op == 0xCB: self.execute_cb_opcode(self.fetch_byte())
        elif op == 0xCC: self.call_cc(self.get_flag(self.FLAG_Z))
        elif op == 0xCD: addr = self.fetch_word(); self.push_word(self.pc); self.pc = addr; self.cycles += 24
        elif op == 0xCE: self.adc_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xCF: self.rst(0x08)
        
        # 0xD0-0xDF
        elif op == 0xD0: self.ret_cc(not self.get_flag(self.FLAG_C))
        elif op == 0xD1: self.set_de(self.pop_word()); self.cycles += 12
        elif op == 0xD2: self.jp_cc(not self.get_flag(self.FLAG_C))
        elif op == 0xD3: pass  # Invalid
        elif op == 0xD4: self.call_cc(not self.get_flag(self.FLAG_C))
        elif op == 0xD5: self.push_word(self.get_de()); self.cycles += 16
        elif op == 0xD6: self.sub_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xD7: self.rst(0x10)
        elif op == 0xD8: self.ret_cc(self.get_flag(self.FLAG_C))
        elif op == 0xD9: self.pc = self.pop_word(); self.ime = True; self.cycles += 16  # RETI
        elif op == 0xDA: self.jp_cc(self.get_flag(self.FLAG_C))
        elif op == 0xDB: pass  # Invalid
        elif op == 0xDC: self.call_cc(self.get_flag(self.FLAG_C))
        elif op == 0xDD: pass  # Invalid
        elif op == 0xDE: self.sbc_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xDF: self.rst(0x18)
        
        # 0xE0-0xEF
        elif op == 0xE0: self.memory.write_byte(0xFF00 + self.fetch_byte(), self.a); self.cycles += 12
        elif op == 0xE1: self.set_hl(self.pop_word()); self.cycles += 12
        elif op == 0xE2: self.memory.write_byte(0xFF00 + self.c, self.a); self.cycles += 8
        elif op == 0xE3: pass  # Invalid
        elif op == 0xE4: pass  # Invalid
        elif op == 0xE5: self.push_word(self.get_hl()); self.cycles += 16
        elif op == 0xE6: self.and_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xE7: self.rst(0x20)
        elif op == 0xE8: self.add_sp_n()
        elif op == 0xE9: self.pc = self.get_hl(); self.cycles += 4
        elif op == 0xEA: self.memory.write_byte(self.fetch_word(), self.a); self.cycles += 16
        elif op == 0xEB: pass  # Invalid
        elif op == 0xEC: pass  # Invalid
        elif op == 0xED: pass  # Invalid
        elif op == 0xEE: self.xor_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xEF: self.rst(0x28)
        
        # 0xF0-0xFF
        elif op == 0xF0: self.a = self.memory.read_byte(0xFF00 + self.fetch_byte()); self.cycles += 12
        elif op == 0xF1: self.set_af(self.pop_word()); self.cycles += 12
        elif op == 0xF2: self.a = self.memory.read_byte(0xFF00 + self.c); self.cycles += 8
        elif op == 0xF3: self.ime = False; self.cycles += 4
        elif op == 0xF4: pass  # Invalid
        elif op == 0xF5: self.push_word(self.get_af()); self.cycles += 16
        elif op == 0xF6: self.or_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xF7: self.rst(0x30)
        elif op == 0xF8: self.ld_hl_sp_n()
        elif op == 0xF9: self.sp = self.get_hl(); self.cycles += 8
        elif op == 0xFA: self.a = self.memory.read_byte(self.fetch_word()); self.cycles += 16
        elif op == 0xFB: self.ime = True; self.cycles += 4
        elif op == 0xFC: pass  # Invalid
        elif op == 0xFD: pass  # Invalid
        elif op == 0xFE: self.cp_a(self.fetch_byte()); self.cycles += 8
        elif op == 0xFF: self.rst(0x38)
        
        else:
            print(f"[CPU] Unimplemented: 0x{op:02X} at 0x{self.pc-1:04X}")
            self.cycles += 4
    
    def execute_cb_opcode(self, op):
        """Execute CB-prefixed opcodes - ALL 256"""
        r = op & 0x07
        is_hl = (r == 6)
        cycles = 16 if is_hl else 8
        
        # RLC (0x00-0x07)
        if 0x00 <= op <= 0x07: self.set_reg8(r, self.rlc(self.get_reg8(r))); self.cycles += cycles
        # RRC (0x08-0x0F)
        elif 0x08 <= op <= 0x0F: self.set_reg8(r, self.rrc(self.get_reg8(r))); self.cycles += cycles
        # RL (0x10-0x17)
        elif 0x10 <= op <= 0x17: self.set_reg8(r, self.rl(self.get_reg8(r))); self.cycles += cycles
        # RR (0x18-0x1F)
        elif 0x18 <= op <= 0x1F: self.set_reg8(r, self.rr(self.get_reg8(r))); self.cycles += cycles
        # SLA (0x20-0x27)
        elif 0x20 <= op <= 0x27: self.set_reg8(r, self.sla(self.get_reg8(r))); self.cycles += cycles
        # SRA (0x28-0x2F)
        elif 0x28 <= op <= 0x2F: self.set_reg8(r, self.sra(self.get_reg8(r))); self.cycles += cycles
        # SWAP (0x30-0x37)
        elif 0x30 <= op <= 0x37: self.set_reg8(r, self.swap(self.get_reg8(r))); self.cycles += cycles
        # SRL (0x38-0x3F)
        elif 0x38 <= op <= 0x3F: self.set_reg8(r, self.srl(self.get_reg8(r))); self.cycles += cycles
        # BIT (0x40-0x7F)
        elif 0x40 <= op <= 0x7F:
            bit = (op >> 3) & 0x07
            self.bit(bit, self.get_reg8(r))
            self.cycles += 12 if is_hl else 8
        # RES (0x80-0xBF)
        elif 0x80 <= op <= 0xBF:
            bit = (op >> 3) & 0x07
            self.set_reg8(r, self.get_reg8(r) & ~(1 << bit))
            self.cycles += cycles
        # SET (0xC0-0xFF)
        elif 0xC0 <= op <= 0xFF:
            bit = (op >> 3) & 0x07
            self.set_reg8(r, self.get_reg8(r) | (1 << bit))
            self.cycles += cycles
    
    # === HELPER FUNCTIONS ===
    
    def get_reg8(self, idx):
        if idx == 0: return self.b
        elif idx == 1: return self.c
        elif idx == 2: return self.d
        elif idx == 3: return self.e
        elif idx == 4: return self.h
        elif idx == 5: return self.l
        elif idx == 6: return self.memory.read_byte(self.get_hl())
        elif idx == 7: return self.a
    
    def set_reg8(self, idx, val):
        val &= 0xFF
        if idx == 0: self.b = val
        elif idx == 1: self.c = val
        elif idx == 2: self.d = val
        elif idx == 3: self.e = val
        elif idx == 4: self.h = val
        elif idx == 5: self.l = val
        elif idx == 6: self.memory.write_byte(self.get_hl(), val)
        elif idx == 7: self.a = val
    
    def ld_r_r(self, op):
        dst = (op >> 3) & 0x07
        src = op & 0x07
        self.set_reg8(dst, self.get_reg8(src))
        self.cycles += 4 if src != 6 and dst != 6 else 8
    
    def inc_8bit(self, val):
        res = (val + 1) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, (val & 0x0F) == 0x0F)
        return res
    
    def dec_8bit(self, val):
        res = (val - 1) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (val & 0x0F) == 0)
        return res
    
    def add_a(self, val):
        res = self.a + val
        self.set_flag(self.FLAG_Z, (res & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((self.a & 0xF) + (val & 0xF)) > 0xF)
        self.set_flag(self.FLAG_C, res > 0xFF)
        self.a = res & 0xFF
    
    def adc_a(self, val):
        c = self.get_flag(self.FLAG_C)
        res = self.a + val + c
        self.set_flag(self.FLAG_Z, (res & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((self.a & 0xF) + (val & 0xF) + c) > 0xF)
        self.set_flag(self.FLAG_C, res > 0xFF)
        self.a = res & 0xFF
    
    def sub_a(self, val):
        res = self.a - val
        self.set_flag(self.FLAG_Z, (res & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (self.a & 0xF) < (val & 0xF))
        self.set_flag(self.FLAG_C, res < 0)
        self.a = res & 0xFF
    
    def sbc_a(self, val):
        c = self.get_flag(self.FLAG_C)
        res = self.a - val - c
        self.set_flag(self.FLAG_Z, (res & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (self.a & 0xF) < ((val & 0xF) + c))
        self.set_flag(self.FLAG_C, res < 0)
        self.a = res & 0xFF
    
    def and_a(self, val):
        self.a &= val
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 1)
        self.set_flag(self.FLAG_C, 0)
    
    def xor_a(self, val):
        self.a ^= val
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, 0)
    
    def or_a(self, val):
        self.a |= val
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, 0)
    
    def cp_a(self, val):
        res = self.a - val
        self.set_flag(self.FLAG_Z, (res & 0xFF) == 0)
        self.set_flag(self.FLAG_N, 1)
        self.set_flag(self.FLAG_H, (self.a & 0xF) < (val & 0xF))
        self.set_flag(self.FLAG_C, res < 0)
    
    def add_hl(self, val):
        hl = self.get_hl()
        res = hl + val
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((hl & 0xFFF) + (val & 0xFFF)) > 0xFFF)
        self.set_flag(self.FLAG_C, res > 0xFFFF)
        self.set_hl(res & 0xFFFF)
    
    def jr(self):
        offset = self.fetch_byte()
        if offset > 127:
            offset -= 256
        self.pc = (self.pc + offset) & 0xFFFF
    
    def jr_cc(self, cond):
        offset = self.fetch_byte()
        if cond:
            if offset > 127:
                offset -= 256
            self.pc = (self.pc + offset) & 0xFFFF
            self.cycles += 12
        else:
            self.cycles += 8
    
    def jp_cc(self, cond):
        addr = self.fetch_word()
        if cond:
            self.pc = addr
            self.cycles += 16
        else:
            self.cycles += 12
    
    def call_cc(self, cond):
        addr = self.fetch_word()
        if cond:
            self.push_word(self.pc)
            self.pc = addr
            self.cycles += 24
        else:
            self.cycles += 12
    
    def ret_cc(self, cond):
        if cond:
            self.pc = self.pop_word()
            self.cycles += 20
        else:
            self.cycles += 8
    
    def rst(self, addr):
        self.push_word(self.pc)
        self.pc = addr
        self.cycles += 16
    
    def daa(self):
        a = self.a
        adjust = 0
        carry = False
        
        if not self.get_flag(self.FLAG_N):
            if self.get_flag(self.FLAG_H) or (a & 0x0F) > 9:
                adjust |= 0x06
            if self.get_flag(self.FLAG_C) or a > 0x99:
                adjust |= 0x60
                carry = True
            a += adjust
        else:
            if self.get_flag(self.FLAG_H):
                adjust |= 0x06
            if self.get_flag(self.FLAG_C):
                adjust |= 0x60
            a -= adjust
        
        self.a = a & 0xFF
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, carry or self.get_flag(self.FLAG_C))
    
    def add_sp_n(self):
        offset = self.fetch_byte()
        if offset > 127:
            offset -= 256
        res = self.sp + offset
        self.set_flag(self.FLAG_Z, 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((self.sp & 0x0F) + (offset & 0x0F)) > 0x0F)
        self.set_flag(self.FLAG_C, ((self.sp & 0xFF) + (offset & 0xFF)) > 0xFF)
        self.sp = res & 0xFFFF
        self.cycles += 16
    
    def ld_hl_sp_n(self):
        offset = self.fetch_byte()
        if offset > 127:
            offset -= 256
        res = self.sp + offset
        self.set_flag(self.FLAG_Z, 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, ((self.sp & 0x0F) + (offset & 0x0F)) > 0x0F)
        self.set_flag(self.FLAG_C, ((self.sp & 0xFF) + (offset & 0xFF)) > 0xFF)
        self.set_hl(res & 0xFFFF)
        self.cycles += 12
    
    # === ROTATE/SHIFT OPERATIONS ===
    
    def rlca(self):
        c = (self.a >> 7) & 1
        self.a = ((self.a << 1) | c) & 0xFF
        self.set_flag(self.FLAG_Z, 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
    
    def rrca(self):
        c = self.a & 1
        self.a = ((self.a >> 1) | (c << 7)) & 0xFF
        self.set_flag(self.FLAG_Z, 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
    
    def rla(self):
        c = self.get_flag(self.FLAG_C)
        nc = (self.a >> 7) & 1
        self.a = ((self.a << 1) | c) & 0xFF
        self.set_flag(self.FLAG_Z, 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, nc)
    
    def rra(self):
        c = self.get_flag(self.FLAG_C)
        nc = self.a & 1
        self.a = ((self.a >> 1) | (c << 7)) & 0xFF
        self.set_flag(self.FLAG_Z, 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, nc)
    
    def rlc(self, val):
        c = (val >> 7) & 1
        res = ((val << 1) | c) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
        return res
    
    def rrc(self, val):
        c = val & 1
        res = ((val >> 1) | (c << 7)) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
        return res
    
    def rl(self, val):
        c = self.get_flag(self.FLAG_C)
        nc = (val >> 7) & 1
        res = ((val << 1) | c) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, nc)
        return res
    
    def rr(self, val):
        c = self.get_flag(self.FLAG_C)
        nc = val & 1
        res = ((val >> 1) | (c << 7)) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, nc)
        return res
    
    def sla(self, val):
        c = (val >> 7) & 1
        res = (val << 1) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
        return res
    
    def sra(self, val):
        c = val & 1
        res = ((val >> 1) | (val & 0x80)) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
        return res
    
    def srl(self, val):
        c = val & 1
        res = (val >> 1) & 0xFF
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, c)
        return res
    
    def swap(self, val):
        res = ((val & 0x0F) << 4) | ((val & 0xF0) >> 4)
        self.set_flag(self.FLAG_Z, res == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 0)
        self.set_flag(self.FLAG_C, 0)
        return res
    
    def bit(self, bit, val):
        self.set_flag(self.FLAG_Z, (val & (1 << bit)) == 0)
        self.set_flag(self.FLAG_N, 0)
        self.set_flag(self.FLAG_H, 1)