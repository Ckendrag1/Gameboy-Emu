"""
Main Game Boy Emulator Class
Ties all components together
"""

import pygame
from memory import Memory
from cpu import CPU
from ppu import PPU, SCREEN_WIDTH, SCREEN_HEIGHT
from input import Input
from cartridge import Cartridge

# Display scale factor
SCALE = 3

class GameBoy:
    """Main Game Boy emulator"""
    
    def __init__(self):
        pygame.init()
        
        # Create window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH * SCALE, SCREEN_HEIGHT * SCALE))
        pygame.display.set_caption("Game Boy Emulator")
        self.clock = pygame.time.Clock()
        
        # Game Boy color palette (classic green)
        self.colors = [
            (155, 188, 15),   # 0 - Lightest
            (139, 172, 15),   # 1 - Light
            (48, 98, 48),     # 2 - Dark
            (15, 56, 15)      # 3 - Darkest
        ]
        
        # Initialize components
        self.cartridge = Cartridge()
        self.memory = Memory()
        self.cpu = CPU(self.memory)
        self.ppu = PPU(self.memory)
        self.input = Input()
        
        # Emulator state
        self.running = False
        self.paused = False
        
        # Performance tracking
        self.fps = 60
        self.frame_count = 0
    
    def load_rom(self, filename):
        """Load a ROM file"""
        if self.cartridge.load_rom(filename):
            # Load ROM data into memory
            rom_data = self.cartridge.get_rom_data()
            self.memory.load_rom(rom_data)
            return True
        return False
    
    def run(self):
        """Main emulation loop"""
        self.running = True
        
        print("[GameBoy] Starting emulator...")
        print("[GameBoy] Controls:")
        print("  Arrow Keys - D-Pad")
        print("  Z - A Button")
        print("  X - B Button")
        print("  Enter - Start")
        print("  Right Shift - Select")
        print("  ESC - Quit")
        print("  P - Pause")
        
        while self.running:
            self.handle_events()
            
            if not self.paused:
                self.emulate_frame()
                self.render()
            
            # Cap at 60 FPS
            self.clock.tick(self.fps)
            
            # Update window title with FPS
            if self.frame_count % 60 == 0:
                fps = self.clock.get_fps()
                pygame.display.set_caption(f"Game Boy Emulator - {fps:.1f} FPS")
            
            self.frame_count += 1
    
    def emulate_frame(self):
        """Emulate one frame (~70224 cycles)"""
        frame_cycles = 0
        target_cycles = 70224  # Cycles per frame at 60 FPS
        
        while frame_cycles < target_cycles:
            cycles_before = self.cpu.cycles
            
            # Execute one CPU instruction
            self.cpu.step()
            
            cycles_executed = self.cpu.cycles - cycles_before
            
            # Update PPU
            self.ppu.step(cycles_executed)
            
            # TODO: Update timers
            # TODO: Handle interrupts
            
            frame_cycles += cycles_executed
    
    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"[GameBoy] {'Paused' if self.paused else 'Resumed'}")
                else:
                    self.input.handle_key_down(event.key)
            
            elif event.type == pygame.KEYUP:
                self.input.handle_key_up(event.key)
    
    def render(self):
        """Render the display"""
        # Draw pixels from PPU screen buffer
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                color_index = self.ppu.screen[y][x]
                color = self.colors[color_index]
                
                # Draw scaled pixel
                rect = pygame.Rect(x * SCALE, y * SCALE, SCALE, SCALE)
                pygame.draw.rect(self.screen, color, rect)
        
        pygame.display.flip()
    
    def quit(self):
        """Clean up and quit"""
        print("[GameBoy] Shutting down...")
        pygame.quit()
    
    def reset(self):
        """Reset the emulator"""
        print("[GameBoy] Resetting...")
        self.cpu = CPU(self.memory)
        self.ppu = PPU(self.memory)
        self.input.reset()