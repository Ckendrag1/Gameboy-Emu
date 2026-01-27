"""
Game Boy Interrupt System
Handles V-Blank, LCD STAT, Timer, Serial, and Joypad interrupts
"""

class Interrupts:
    """Game Boy interrupt controller"""
    
    # Interrupt bits
    INT_VBLANK = 0  # V-Blank (bit 0)
    INT_LCD    = 1  # LCD STAT (bit 1)
    INT_TIMER  = 2  # Timer (bit 2)
    INT_SERIAL = 3  # Serial (bit 3)
    INT_JOYPAD = 4  # Joypad (bit 4)
    
    # Interrupt vectors (where CPU jumps when interrupt fires)
    VECTOR_VBLANK = 0x0040
    VECTOR_LCD    = 0x0048
    VECTOR_TIMER  = 0x0050
    VECTOR_SERIAL = 0x0058
    VECTOR_JOYPAD = 0x0060
    
    def __init__(self, memory):
        self.memory = memory
        
        # Interrupt flags (IF - 0xFF0F)
        # Bit is set when interrupt is requested
        self.interrupt_flag = 0
        
        # Interrupt enable (IE - 0xFFFF)
        # Bit is set when interrupt is enabled
        self.interrupt_enable = 0
    
    def request_interrupt(self, interrupt_bit):
        """Request an interrupt by setting the corresponding bit"""
        self.interrupt_flag |= (1 << interrupt_bit)
        # Write to memory so CPU can see it
        self.memory.write_byte(0xFF0F, self.interrupt_flag)
    
    def get_interrupt_flag(self):
        """Get current interrupt flags"""
        return self.interrupt_flag
    
    def set_interrupt_flag(self, value):
        """Set interrupt flags (called when 0xFF0F is written)"""
        self.interrupt_flag = value & 0x1F  # Only lower 5 bits used
    
    def get_interrupt_enable(self):
        """Get interrupt enable register"""
        return self.interrupt_enable
    
    def set_interrupt_enable(self, value):
        """Set interrupt enable (called when 0xFFFF is written)"""
        self.interrupt_enable = value & 0x1F  # Only lower 5 bits used
    
    def handle_interrupts(self, cpu):
        """
        Check for pending interrupts and handle them
        Returns True if an interrupt was handled
        """
        # IME must be enabled for interrupts to fire
        if not cpu.ime:
            return False
        
        # Check each interrupt in priority order
        pending = self.interrupt_flag & self.interrupt_enable
        
        if pending == 0:
            return False
        
        # V-Blank (highest priority)
        if pending & (1 << self.INT_VBLANK):
            self.service_interrupt(cpu, self.INT_VBLANK, self.VECTOR_VBLANK)
            return True
        
        # LCD STAT
        elif pending & (1 << self.INT_LCD):
            self.service_interrupt(cpu, self.INT_LCD, self.VECTOR_LCD)
            return True
        
        # Timer
        elif pending & (1 << self.INT_TIMER):
            self.service_interrupt(cpu, self.INT_TIMER, self.VECTOR_TIMER)
            return True
        
        # Serial
        elif pending & (1 << self.INT_SERIAL):
            self.service_interrupt(cpu, self.INT_SERIAL, self.VECTOR_SERIAL)
            return True
        
        # Joypad
        elif pending & (1 << self.INT_JOYPAD):
            self.service_interrupt(cpu, self.INT_JOYPAD, self.VECTOR_JOYPAD)
            return True
        
        return False
    
    def service_interrupt(self, cpu, interrupt_bit, vector):
        """Service an interrupt"""
        # Disable IME
        cpu.ime = False
        
        # Clear the interrupt flag
        self.interrupt_flag &= ~(1 << interrupt_bit)
        self.memory.write_byte(0xFF0F, self.interrupt_flag)
        
        # Wake from HALT
        cpu.halted = False
        
        # Push PC onto stack
        cpu.push_word(cpu.pc)
        
        # Jump to interrupt vector
        cpu.pc = vector
        
        # Interrupt handling takes 20 cycles
        cpu.cycles += 20
        
        print(f"[Interrupt] Serviced interrupt {interrupt_bit} -> 0x{vector:04X}")