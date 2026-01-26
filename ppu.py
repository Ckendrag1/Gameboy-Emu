"""
Game Boy PPU (Picture Processing Unit)
Handles all graphics rendering
"""

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144

class PPU:
    """Picture Processing Unit - handles graphics rendering"""
    
    # PPU Modes
    MODE_HBLANK = 0  # H-Blank
    MODE_VBLANK = 1  # V-Blank
    MODE_OAM = 2     # OAM scan
    MODE_DRAW = 3    # Drawing pixels
    
    def __init__(self, memory):
        self.memory = memory
        self.mode = self.MODE_OAM
        self.line = 0  # Current scanline (LY register)
        self.cycles = 0
        
        # Screen buffer (4 shades: 0=white, 3=black)
        self.screen = [[0 for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]
        
        # V-Blank flag for frame synchronization
        self.vblank_flag = False
    
    def step(self, cpu_cycles):
        """Update PPU state based on CPU cycles"""
        self.cycles += cpu_cycles
        
        # Mode 2: OAM scan (80 cycles)
        if self.mode == self.MODE_OAM:
            if self.cycles >= 80:
                self.cycles -= 80
                self.mode = self.MODE_DRAW
        
        # Mode 3: Drawing pixels (172 cycles)
        elif self.mode == self.MODE_DRAW:
            if self.cycles >= 172:
                self.cycles -= 172
                self.mode = self.MODE_HBLANK
                self.render_scanline()
        
        # Mode 0: H-Blank (204 cycles)
        elif self.mode == self.MODE_HBLANK:
            if self.cycles >= 204:
                self.cycles -= 204
                self.line += 1
                
                if self.line == 144:
                    # Enter V-Blank
                    self.mode = self.MODE_VBLANK
                    self.vblank_flag = True
                    # TODO: Trigger V-Blank interrupt
                else:
                    self.mode = self.MODE_OAM
        
        # Mode 1: V-Blank (456 cycles per line, 10 lines)
        elif self.mode == self.MODE_VBLANK:
            if self.cycles >= 456:
                self.cycles -= 456
                self.line += 1
                
                if self.line > 153:
                    # New frame
                    self.line = 0
                    self.mode = self.MODE_OAM
                    self.vblank_flag = False
    
    def render_scanline(self):
        """
        Render the current scanline
        TODO: Implement proper tile rendering
        """
        # This is a placeholder implementation
        # Full implementation requires:
        # 1. Read tile map from VRAM
        # 2. Decode tile data
        # 3. Render background layer
        # 4. Render window layer
        # 5. Render sprites (OAM)
        # 6. Apply palette
        # 7. Handle priority and transparency
        
        # For now, just create a test pattern
        for x in range(SCREEN_WIDTH):
            # Simple test pattern
            self.screen[self.line][x] = (x + self.line) % 4
    
    def get_tile_data(self, tile_index, tile_data_select):
        """
        Get tile data from VRAM
        TODO: Implement proper tile decoding
        """
        # Tiles are 8x8 pixels, 2 bytes per row
        # Each pixel is 2 bits (4 colors)
        pass
    
    def render_background(self):
        """
        Render background layer
        TODO: Implement
        """
        pass
    
    def render_window(self):
        """
        Render window layer
        TODO: Implement
        """
        pass
    
    def render_sprites(self):
        """
        Render sprites from OAM
        TODO: Implement
        """
        pass
    
    def is_vblank(self):
        """Check if in V-Blank period"""
        return self.mode == self.MODE_VBLANK
    
    def get_current_line(self):
        """Get current scanline number"""
        return self.line