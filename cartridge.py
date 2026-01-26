"""
Game Boy Cartridge Handler
Loads ROM files and handles Memory Bank Controllers (MBC)
"""

class Cartridge:
    """Game Boy cartridge with ROM loading"""
    
    # Cartridge types
    CART_ROM_ONLY = 0x00
    CART_MBC1 = 0x01
    CART_MBC1_RAM = 0x02
    CART_MBC1_RAM_BATTERY = 0x03
    CART_MBC3 = 0x0F
    CART_MBC3_RAM = 0x10
    CART_MBC3_RAM_BATTERY = 0x13
    CART_MBC5 = 0x19
    CART_MBC5_RAM = 0x1A
    CART_MBC5_RAM_BATTERY = 0x1B
    
    def __init__(self):
        self.rom_data = None
        self.rom_size = 0
        self.ram_size = 0
        self.cart_type = 0
        self.title = ""
        
        # MBC state
        self.rom_bank = 1
        self.ram_bank = 0
        self.ram_enabled = False
        self.banking_mode = 0
    
    def load_rom(self, filename):
        """Load a ROM file and parse header"""
        try:
            with open(filename, 'rb') as f:
                self.rom_data = bytearray(f.read())
                self.rom_size = len(self.rom_data)
            
            # Parse cartridge header (0x0100-0x014F)
            self.parse_header()
            
            print(f"[Cartridge] ROM loaded: {filename}")
            print(f"[Cartridge] Title: {self.title}")
            print(f"[Cartridge] Type: 0x{self.cart_type:02X}")
            print(f"[Cartridge] ROM Size: {self.rom_size} bytes")
            print(f"[Cartridge] RAM Size: {self.ram_size} bytes")
            
            return True
            
        except Exception as e:
            print(f"[Cartridge] Error loading ROM: {e}")
            return False
    
    def parse_header(self):
        """Parse ROM header for cartridge info"""
        if not self.rom_data or len(self.rom_data) < 0x150:
            return
        
        # Title (0x0134-0x0143)
        title_bytes = self.rom_data[0x0134:0x0144]
        self.title = ''.join(chr(b) for b in title_bytes if b != 0)
        
        # Cartridge type (0x0147)
        self.cart_type = self.rom_data[0x0147]
        
        # ROM size (0x0148)
        rom_size_code = self.rom_data[0x0148]
        self.rom_size = 32 * 1024 * (1 << rom_size_code)  # 32KB * 2^code
        
        # RAM size (0x0149)
        ram_size_code = self.rom_data[0x0149]
        ram_sizes = [0, 2*1024, 8*1024, 32*1024, 128*1024, 64*1024]
        self.ram_size = ram_sizes[ram_size_code] if ram_size_code < len(ram_sizes) else 0
    
    def read_rom(self, address):
        """Read from ROM (with MBC banking)"""
        if address < 0x4000:
            # Bank 0 - always accessible
            return self.rom_data[address] if address < len(self.rom_data) else 0
        elif address < 0x8000:
            # Switchable bank
            bank_address = (self.rom_bank * 0x4000) + (address - 0x4000)
            return self.rom_data[bank_address] if bank_address < len(self.rom_data) else 0
        return 0
    
    def write_rom(self, address, value):
        """
        Handle MBC control writes
        TODO: Implement MBC1, MBC3, MBC5 properly
        """
        # MBC1 basic implementation
        if self.cart_type in [self.CART_MBC1, self.CART_MBC1_RAM, self.CART_MBC1_RAM_BATTERY]:
            if address < 0x2000:
                # RAM enable (0x0000-0x1FFF)
                self.ram_enabled = (value & 0x0F) == 0x0A
            elif address < 0x4000:
                # ROM bank select (0x2000-0x3FFF)
                bank = value & 0x1F
                if bank == 0:
                    bank = 1
                self.rom_bank = bank
            elif address < 0x6000:
                # RAM bank select or upper ROM bank bits (0x4000-0x5FFF)
                self.ram_bank = value & 0x03
            elif address < 0x8000:
                # Banking mode select (0x6000-0x7FFF)
                self.banking_mode = value & 0x01
    
    def get_rom_data(self):
        """Get raw ROM data for loading into memory"""
        return self.rom_data[:0x8000] if self.rom_data else [0] * 0x8000