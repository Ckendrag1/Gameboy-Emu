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
    
    def __init__(self, memory, interrupts=None):
        self.memory = memory
        self.interrupts = interrupts
        self.mode = self.MODE_OAM
        self.line = 0  # Current scanline (LY register)
        self.cycles = 0
        
        # Screen buffer (4 shades: 0=white, 3=black)
        self.screen = [[0 for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]
        
        # V-Blank flag for frame synchronization
        self.vblank_flag = False
        
        # LCD Control register (LCDC - 0xFF40)
        self.lcdc = 0x91  # Default: LCD on, BG on
        
        # Scroll registers
        self.scy = 0  # Scroll Y (0xFF42)
        self.scx = 0  # Scroll X (0xFF43)
        
        # Background palette (BGP - 0xFF47)
        self.bgp = 0xFC  # Default palette: 11 11 10 00
    
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
                
                # Write LY to memory
                self.memory.write_byte(0xFF44, self.line)
                
                if self.line == 144:
                    # Enter V-Blank
                    self.mode = self.MODE_VBLANK
                    self.vblank_flag = True
                    # Trigger V-Blank interrupt
                    if self.interrupts:
                        self.interrupts.request_interrupt(self.interrupts.INT_VBLANK)
                else:
                    self.mode = self.MODE_OAM
        
        # Mode 1: V-Blank (456 cycles per line, 10 lines)
        elif self.mode == self.MODE_VBLANK:
            if self.cycles >= 456:
                self.cycles -= 456
                self.line += 1
                
                # Write LY to memory
                self.memory.write_byte(0xFF44, self.line)
                
                if self.line > 153:
                    # New frame
                    self.line = 0
                    self.mode = self.MODE_OAM
                    self.vblank_flag = False
                    self.memory.write_byte(0xFF44, 0)
    
    def render_scanline(self):
        """Render the current scanline"""
        # Read LCD control
        self.lcdc = self.memory.read_byte(0xFF40)
        
        # Check if LCD is enabled
        if not (self.lcdc & 0x80):
            # LCD is off - clear screen to white
            for x in range(SCREEN_WIDTH):
                self.screen[self.line][x] = 0
            return
        
        # Read scroll registers
        self.scy = self.memory.read_byte(0xFF42)
        self.scx = self.memory.read_byte(0xFF43)
        
        # Read palette
        self.bgp = self.memory.read_byte(0xFF47)
        
        # Render background if enabled
        if self.lcdc & 0x01:
            self.render_background_line()
        else:
            # Background disabled - clear to white
            for x in range(SCREEN_WIDTH):
                self.screen[self.line][x] = 0
        
        # Render sprites if enabled (bit 1 of LCDC)
        if self.lcdc & 0x02:
            self.render_sprites_line()
        
        # TODO: Render window if enabled (bit 5 of LCDC)
    
    def render_background_line(self):
        """Render background layer for current scanline - OPTIMIZED"""
        # Check if background is enabled
        if not (self.lcdc & 0x01):
            return
        
        # Determine which tile map to use (bit 3 of LCDC)
        tile_map_base = 0x9C00 if (self.lcdc & 0x08) else 0x9800
        
        # Determine which tile data to use (bit 4 of LCDC)
        tile_data_base = 0x8000 if (self.lcdc & 0x10) else 0x8800
        use_signed = not (self.lcdc & 0x10)
        
        # Calculate Y position in tile map (with scrolling)
        y_pos = (self.line + self.scy) & 0xFF
        tile_row = (y_pos >> 3) & 31  # Divide by 8, mod 32
        tile_y = y_pos & 7  # Y position within tile (0-7)
        
        # Pre-calculate tile map row address
        tile_map_row_addr = tile_map_base + (tile_row * 32)
        
        # Cache palette lookups
        palette = self.bgp
        palette_cache = [
            (palette >> 0) & 0x03,  # Color 0
            (palette >> 2) & 0x03,  # Color 1
            (palette >> 4) & 0x03,  # Color 2
            (palette >> 6) & 0x03   # Color 3
        ]
        
        # Render each pixel in the scanline
        screen_line = self.screen[self.line]  # Cache line reference
        
        for x in range(SCREEN_WIDTH):
            # Calculate X position in tile map (with scrolling)
            x_pos = (x + self.scx) & 0xFF
            tile_col = (x_pos >> 3) & 31  # Divide by 8, mod 32
            tile_x = 7 - (x_pos & 7)  # X position within tile (reversed for bit extraction)
            
            # Get tile index from tile map
            tile_map_addr = tile_map_row_addr + tile_col
            tile_index = self.memory.read_byte(tile_map_addr)
            
            # Calculate tile data address
            if use_signed:
                if tile_index > 127:
                    tile_index = tile_index - 256
                tile_addr = tile_data_base + (tile_index * 16)
            else:
                tile_addr = tile_data_base + (tile_index * 16)
            
            # Get pixel color from tile (optimized inline)
            row_addr = tile_addr + (tile_y * 2)
            byte1 = self.memory.read_byte(row_addr)
            byte2 = self.memory.read_byte(row_addr + 1)
            
            # Extract color bits
            bit1 = (byte1 >> tile_x) & 1
            bit2 = (byte2 >> tile_x) & 1
            color = (bit2 << 1) | bit1
            
            # Apply palette and write directly
            screen_line[x] = palette_cache[color]
    
    def get_tile_pixel(self, tile_addr, x, y):
        """
        Get a pixel color from a tile
        Each tile is 8x8 pixels, 16 bytes (2 bytes per row)
        Each pixel is 2 bits (4 colors)
        """
        # Each row is 2 bytes
        row_addr = tile_addr + (y * 2)
        
        # Read the two bytes for this row
        byte1 = self.memory.read_byte(row_addr)
        byte2 = self.memory.read_byte(row_addr + 1)
        
        # Get the bit position (tiles are rendered left-to-right, so bit 7 is leftmost)
        bit_pos = 7 - x
        
        # Extract the two bits for this pixel
        bit1 = (byte1 >> bit_pos) & 1
        bit2 = (byte2 >> bit_pos) & 1
        
        # Combine to get color (0-3)
        color = (bit2 << 1) | bit1
        
        return color
    
    def apply_palette(self, color, palette):
        """
        Apply palette to a color value
        Palette format: bits 7-6 = color 3, bits 5-4 = color 2, etc.
        """
        # Extract the 2-bit palette value for this color
        shift = color * 2
        palette_color = (palette >> shift) & 0x03
        
        return palette_color
    
    def render_sprites_line(self):
        """
        Render sprites for the current scanline - OPTIMIZED
        """
        # Check sprite size (bit 2 of LCDC)
        sprite_height = 16 if (self.lcdc & 0x04) else 8
        
        # Read sprite palettes once
        obp0 = self.memory.read_byte(0xFF48)
        obp1 = self.memory.read_byte(0xFF49)
        
        # Pre-calculate palette caches
        obp0_cache = [(obp0 >> (i*2)) & 0x03 for i in range(4)]
        obp1_cache = [(obp1 >> (i*2)) & 0x03 for i in range(4)]
        
        # Collect sprites on this scanline (max 10)
        sprites_on_line = []
        oam_base = 0xFE00
        
        for sprite_idx in range(40):
            oam_addr = oam_base + (sprite_idx * 4)
            
            sprite_y = self.memory.read_byte(oam_addr) - 16
            
            # Quick check if sprite is on this scanline
            if sprite_y <= self.line < sprite_y + sprite_height:
                sprite_x = self.memory.read_byte(oam_addr + 1) - 8
                tile_index = self.memory.read_byte(oam_addr + 2)
                attributes = self.memory.read_byte(oam_addr + 3)
                
                sprites_on_line.append((sprite_x, sprite_y, tile_index, attributes, sprite_idx))
                
                if len(sprites_on_line) >= 10:  # Hardware limit
                    break
        
        # Sort by X position (priority)
        sprites_on_line.sort(key=lambda s: (s[0], s[4]))
        
        # Render sprites in reverse for correct priority
        screen_line = self.screen[self.line]
        
        for sprite_x, sprite_y, tile_index, attributes, _ in reversed(sprites_on_line):
            # Parse attributes
            priority = (attributes >> 7) & 1
            y_flip = (attributes >> 6) & 1
            x_flip = (attributes >> 5) & 1
            palette_num = (attributes >> 4) & 1
            palette_cache = obp1_cache if palette_num else obp0_cache
            
            # Calculate sprite row
            sprite_row = self.line - sprite_y
            if y_flip:
                sprite_row = (sprite_height - 1) - sprite_row
            
            # Handle 8x16 sprites
            if sprite_height == 16:
                if sprite_row >= 8:
                    tile_index = tile_index | 0x01
                    sprite_row -= 8
                else:
                    tile_index = tile_index & 0xFE
            
            # Tile address (always 0x8000 for sprites)
            tile_addr = 0x8000 + (tile_index * 16) + (sprite_row * 2)
            
            # Read tile row data once
            byte1 = self.memory.read_byte(tile_addr)
            byte2 = self.memory.read_byte(tile_addr + 1)
            
            # Render 8 pixels
            for x in range(8):
                screen_x = sprite_x + x
                
                if screen_x < 0 or screen_x >= SCREEN_WIDTH:
                    continue
                
                # Calculate bit position
                tile_x = (7 - x) if x_flip else x
                bit_pos = 7 - tile_x
                
                # Extract color
                bit1 = (byte1 >> bit_pos) & 1
                bit2 = (byte2 >> bit_pos) & 1
                color = (bit2 << 1) | bit1
                
                # Color 0 is transparent
                if color == 0:
                    continue
                
                # Check priority
                if priority and screen_line[screen_x] != 0:
                    continue
                
                # Apply palette and draw
                screen_line[screen_x] = palette_cache[color]
    
    def render_sprite(self, sprite, sprite_height, obp0, obp1):
        """Render a single sprite"""
        sprite_x = sprite['x']
        sprite_y = sprite['y']
        tile_index = sprite['tile']
        attributes = sprite['attrs']
        
        # Parse attributes
        # Bit 7: Priority (0=above BG, 1=behind BG colors 1-3)
        # Bit 6: Y flip
        # Bit 5: X flip
        # Bit 4: Palette (0=OBP0, 1=OBP1)
        # Bit 3-0: Not used in DMG
        
        priority = (attributes >> 7) & 1
        y_flip = (attributes >> 6) & 1
        x_flip = (attributes >> 5) & 1
        palette_num = (attributes >> 4) & 1
        palette = obp1 if palette_num else obp0
        
        # Calculate which row of the sprite to render
        sprite_row = self.line - sprite_y
        
        # Apply Y flip
        if y_flip:
            sprite_row = (sprite_height - 1) - sprite_row
        
        # For 8x16 sprites, tile index uses even/odd pairs
        if sprite_height == 16:
            if sprite_row >= 8:
                tile_index = tile_index | 0x01
                sprite_row -= 8
            else:
                tile_index = tile_index & 0xFE
        
        # Tile data is always at 0x8000 for sprites
        tile_addr = 0x8000 + (tile_index * 16)
        
        # Render each pixel of the sprite
        for x in range(8):
            screen_x = sprite_x + x
            
            # Skip if off-screen
            if screen_x < 0 or screen_x >= SCREEN_WIDTH:
                continue
            
            # Apply X flip
            tile_x = (7 - x) if x_flip else x
            
            # Get pixel color from tile
            color = self.get_tile_pixel(tile_addr, tile_x, sprite_row)
            
            # Color 0 is transparent for sprites
            if color == 0:
                continue
            
            # Check priority with background
            if priority:
                # Sprite is behind background colors 1-3
                bg_color = self.screen[self.line][screen_x]
                if bg_color != 0:  # BG color is not white
                    continue
            
            # Apply sprite palette
            final_color = self.apply_palette(color, palette)
            
            # Draw pixel
            self.screen[self.line][screen_x] = final_color
    
    def render_window(self):
        """
        Render window layer
        TODO: Implement window rendering
        """
        pass
    
    def render_sprites(self):
        """
        Render sprites from OAM
        DEPRECATED: Now using render_sprites_line() instead
        """
        pass
    
    def is_vblank(self):
        """Check if in V-Blank period"""
        return self.mode == self.MODE_VBLANK
    
    def get_current_line(self):
        """Get current scanline number"""
        return self.line