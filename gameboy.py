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
from interrupts import Interrupts
from audio import APU

# Display scale factor
SCALE = 3

class GameBoy:
    """Main Game Boy emulator"""
    
    def __init__(self, enable_audio=True):
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
        self.interrupts = Interrupts(None)  # Temporary, will set memory next
        self.input = Input(None)  # Temporary, will set memory next
        self.apu = APU(None, enabled=enable_audio)  # Audio
        self.memory = Memory(self.interrupts, self.input, self.apu)
        self.interrupts.memory = self.memory  # Now connect them
        self.input.memory = self.memory  # Connect input too
        self.apu.memory = self.memory  # Connect audio too
        self.cpu = CPU(self.memory)
        self.ppu = PPU(self.memory, self.interrupts)
        
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
            
            # Connect interrupt registers to memory
            self.setup_interrupt_registers()
            
            return True
        return False
    
    def setup_interrupt_registers(self):
        """Wire interrupt registers to memory I/O"""
        # IE register is at 0xFFFF (handled separately in memory)
        # IF register is at 0xFF0F
        # These will be read/written through memory.io
        pass
    
    def run(self):
        """Main emulation loop"""
        self.running = True
        
        print("[GameBoy] Emulator running...")
        
        # Performance tracking
        frame_times = []
        
        while self.running:
            frame_start = pygame.time.get_ticks()
            
            self.handle_events()
            
            if not self.paused:
                self.emulate_frame()
                self.render()
            
            # Cap at 60 FPS
            self.clock.tick(self.fps)
            
            # Performance monitoring
            frame_end = pygame.time.get_ticks()
            frame_time = frame_end - frame_start
            frame_times.append(frame_time)
            
            # Update window title with FPS and performance info
            if self.frame_count % 60 == 0:
                fps = self.clock.get_fps()
                status = "[PAUSED]" if self.paused else ""
                
                # Calculate average frame time
                if frame_times:
                    avg_frame_time = sum(frame_times[-60:]) / min(60, len(frame_times))
                    target_frame_time = 1000 / 60  # ~16.67ms
                    speed = (target_frame_time / avg_frame_time) * 100 if avg_frame_time > 0 else 100
                    
                    pygame.display.set_caption(
                        f"Game Boy Emulator - {fps:.1f} FPS ({speed:.0f}% speed) {status}"
                    )
            
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
            
            # Handle interrupts
            self.interrupts.handle_interrupts(self.cpu)
            
            # TODO: Update timers
            
            frame_cycles += cycles_executed
        
        # Update audio once per frame (less CPU intensive)
        if self.apu.enabled and self.apu.audio_enabled:
            self.apu.step(target_cycles)
    
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
                elif event.key == pygame.K_m:
                    # Toggle audio mute
                    self.apu.enabled = not self.apu.enabled
                    status = "ON" if self.apu.enabled else "OFF"
                    print(f"[GameBoy] Audio {status}")
                else:
                    self.input.handle_key_down(event.key)
            
            elif event.type == pygame.KEYUP:
                self.input.handle_key_up(event.key)
    
    def render(self):
        """Render the display - OPTIMIZED"""
        # Use surfarray for faster pixel updates
        try:
            import pygame.surfarray as surfarray
            import numpy as np
            
            # Create color lookup array
            color_array = np.array([
                [155, 188, 15],   # 0 - Lightest
                [139, 172, 15],   # 1 - Light
                [48, 98, 48],     # 2 - Dark
                [15, 56, 15]      # 3 - Darkest
            ], dtype=np.uint8)
            
            # Convert screen buffer to color indices
            screen_indices = np.array(self.ppu.screen, dtype=np.uint8)
            
            # Map indices to RGB colors
            rgb_array = color_array[screen_indices]
            
            # Create surface from array and scale
            small_surface = pygame.surfarray.make_surface(rgb_array.swapaxes(0, 1))
            pygame.transform.scale(small_surface, 
                                 (SCREEN_WIDTH * SCALE, SCREEN_HEIGHT * SCALE), 
                                 self.screen)
        except:
            # Fallback to old method if surfarray fails
            for y in range(SCREEN_HEIGHT):
                for x in range(SCREEN_WIDTH):
                    color_index = self.ppu.screen[y][x]
                    color = self.colors[color_index]
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
        self.interrupts = Interrupts(self.memory)
        self.cpu = CPU(self.memory)
        self.ppu = PPU(self.memory, self.interrupts)
        self.input.reset()