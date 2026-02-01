"""
Game Boy Timer System
DIV, TIMA, TMA, TAC registers - Hardware accurate
"""

class Timer:
    """Game Boy Timer - DIV and TIMA"""
    
    def __init__(self, interrupts):
        self.interrupts = interrupts
        
        # Timer registers
        self.div = 0x00    # 0xFF04 - Divider Register (16384 Hz)
        self.tima = 0x00   # 0xFF05 - Timer Counter (programmable)
        self.tma = 0x00    # 0xFF06 - Timer Modulo (reload value)
        self.tac = 0x00    # 0xFF07 - Timer Control
        
        # Internal counters
        self.div_counter = 0     # Counts CPU cycles for DIV
        self.tima_counter = 0    # Counts CPU cycles for TIMA
        
        # Timer frequencies (CPU cycles per TIMA increment)
        # TAC bits 1-0 select frequency:
        # 00: 4096 Hz   (1024 cycles)
        # 01: 262144 Hz (16 cycles)
        # 10: 65536 Hz  (64 cycles)
        # 11: 16384 Hz  (256 cycles)
        self.tima_frequencies = [1024, 16, 64, 256]
        
        # Timer enabled flag
        self.timer_enabled = False
    
    def step(self, cycles):
        """Update timer state based on CPU cycles"""
        # Update DIV register (always runs at 16384 Hz)
        # DIV increments every 256 CPU cycles (4194304 / 16384 = 256)
        self.div_counter += cycles
        while self.div_counter >= 256:
            self.div_counter -= 256
            self.div = (self.div + 1) & 0xFF
        
        # Update TIMA if timer is enabled
        if self.timer_enabled:
            self.tima_counter += cycles
            
            # Get current frequency
            freq_index = self.tac & 0x03
            cycles_per_tick = self.tima_frequencies[freq_index]
            
            while self.tima_counter >= cycles_per_tick:
                self.tima_counter -= cycles_per_tick
                self.tima = (self.tima + 1) & 0xFF
                
                # Check for overflow
                if self.tima == 0:
                    # Overflow! Reload from TMA and request interrupt
                    self.tima = self.tma
                    if self.interrupts:
                        self.interrupts.request_interrupt(self.interrupts.INT_TIMER)
    
    def read_register(self, address):
        """Read timer register"""
        if address == 0xFF04:
            return self.div
        elif address == 0xFF05:
            return self.tima
        elif address == 0xFF06:
            return self.tma
        elif address == 0xFF07:
            return self.tac | 0xF8  # Upper 5 bits always set
        return 0xFF
    
    def write_register(self, address, value):
        """Write timer register"""
        value &= 0xFF
        
        if address == 0xFF04:
            # Writing any value to DIV resets it to 0
            self.div = 0
            self.div_counter = 0
        
        elif address == 0xFF05:
            self.tima = value
        
        elif address == 0xFF06:
            self.tma = value
        
        elif address == 0xFF07:
            # TAC - Timer Control
            old_enabled = self.timer_enabled
            self.tac = value & 0x07  # Only lower 3 bits used
            self.timer_enabled = (value & 0x04) != 0  # Bit 2 = enable
            
            # If timer was just enabled, reset counter
            if not old_enabled and self.timer_enabled:
                self.tima_counter = 0
    
    def reset(self):
        """Reset timer to initial state"""
        self.div = 0
        self.tima = 0
        self.tma = 0
        self.tac = 0
        self.div_counter = 0
        self.tima_counter = 0
        self.timer_enabled = False