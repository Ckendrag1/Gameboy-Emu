"""
Game Boy Memory Management
Handles the complete memory map of the Game Boy
"""

class Memory:
    """Game Boy memory management (64KB address space)"""
    def __init__(self, interrupts=None, input_handler=None, apu=None):
        self.interrupts = interrupts
        self.input_handler = input_handler
        self.apu = apu
        
        # Memory map
        self.rom = [0] * 0x8000      # 0x0000-0x7FFF: ROM (32KB)
        self.vram = [0] * 0x2000     # 0x8000-0x9FFF: Video RAM (8KB)
        self.eram = [0] * 0x2000     # 0xA000-0xBFFF: External RAM (8KB)
        self.wram = [0] * 0x2000     # 0xC000-0xDFFF: Work RAM (8KB)
        self.oam = [0] * 0xA0        # 0xFE00-0xFE9F: Sprite Attribute Table
        self.io = [0] * 0x80         # 0xFF00-0xFF7F: I/O Registers
        self.hram = [0] * 0x7F       # 0xFF80-0xFFFE: High RAM
        self.ie = 0                  # 0xFFFF: Interrupt Enable
        
    def read_byte(self, address):
        """Read a byte from memory - OPTIMIZED"""
        address &= 0xFFFF
        
        # Fast path for most common accesses
        if address < 0x8000:
            return self.rom[address]
        elif address < 0xA000:
            return self.vram[address - 0x8000]
        elif address >= 0xC000 and address < 0xE000:
            return self.wram[address - 0xC000]
        elif address >= 0xFE00 and address < 0xFEA0:
            return self.oam[address - 0xFE00]
        elif address >= 0xFF80 and address < 0xFFFF:
            return self.hram[address - 0xFF80]
        
        # Less common paths
        if address < 0xC000:
            return self.eram[address - 0xA000]
        elif address < 0xFE00:
            return self.wram[address - 0xE000]  # Echo RAM
        elif address < 0xFF00:
            return 0
        elif address < 0xFF80:
            # I/O registers
            if address == 0xFF00:
                return self.input_handler.read_p1() if self.input_handler else 0xFF
            elif address == 0xFF0F:
                return self.interrupts.get_interrupt_flag() if self.interrupts else 0xFF
            elif 0xFF10 <= address <= 0xFF3F:
                return self.apu.read_register(address) if self.apu else 0xFF
            return self.io[address - 0xFF00]
        else:  # 0xFFFF
            return self.interrupts.get_interrupt_enable() if self.interrupts else self.ie
    
    def write_byte(self, address, value):
        """Write a byte to memory"""
        address &= 0xFFFF
        value &= 0xFF
        
        if address < 0x8000:
            # ROM is normally read-only (MBC writes handled in cartridge.py)
            pass
        elif address < 0xA000:
            self.vram[address - 0x8000] = value
        elif address < 0xC000:
            self.eram[address - 0xA000] = value
        elif address < 0xE000:
            self.wram[address - 0xC000] = value
        elif address < 0xFE00:
            self.wram[address - 0xE000] = value  # Echo RAM
        elif address < 0xFEA0:
            self.oam[address - 0xFE00] = value
        elif address < 0xFF00:
            pass  # Unusable memory
        elif address < 0xFF80:
            # I/O registers
            if address == 0xFF00 and self.input_handler:
                # P1 - Joypad register
                self.input_handler.write_p1(value)
            elif address == 0xFF0F and self.interrupts:
                # IF - Interrupt Flag
                self.interrupts.set_interrupt_flag(value)
            elif 0xFF10 <= address <= 0xFF3F and self.apu:
                # Audio registers
                self.apu.write_register(address, value)
            self.io[address - 0xFF00] = value
        elif address < 0xFFFF:
            self.hram[address - 0xFF80] = value
        else:
            # 0xFFFF - IE register
            if self.interrupts:
                self.interrupts.set_interrupt_enable(value)
            self.ie = value
    
    def read_word(self, address):
        """Read a 16-bit word (little-endian)"""
        low = self.read_byte(address)
        high = self.read_byte(address + 1)
        return (high << 8) | low
    
    def write_word(self, address, value):
        """Write a 16-bit word (little-endian)"""
        self.write_byte(address, value & 0xFF)
        self.write_byte(address + 1, (value >> 8) & 0xFF)
    
    def load_rom(self, rom_data):
        """Load ROM data into memory"""
        for i, byte in enumerate(rom_data[:0x8000]):
            self.rom[i] = byte