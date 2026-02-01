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
from timer import Timer

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
        
        # Create small surface for faster rendering
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Game Boy color palette - Choose your style!
        # Original Game Boy (Green):
        self.colors = [
            (155, 188, 15),   # 0 - Lightest
            (139, 172, 15),   # 1 - Light
            (48, 98, 48),     # 2 - Dark
            (15, 56, 15)      # 3 - Darkest
        ]
        
        # Uncomment for Grayscale:
        # self.colors = [
        #     (255, 255, 255),  # White
        #     (170, 170, 170),  # Light gray
        #     (85, 85, 85),     # Dark gray
        #     (0, 0, 0)         # Black
        # ]
        
        # Uncomment for Game Boy Pocket style:
        # self.colors = [
        #     (224, 248, 208),
        #     (136, 192, 112),
        #     (52, 104, 86),
        #     (8, 24, 32)
        # ]
        
        # Initialize components
        self.cartridge = Cartridge()
        self.interrupts = Interrupts(None)  # Temporary, will set memory next
        self.input = Input(None, self.interrupts)  # Pass interrupts!
        self.apu = APU(None, enabled=enable_audio)  # Audio
        self.timer = Timer(self.interrupts)  # Timer system
        self.memory = Memory(self.interrupts, self.input, self.apu, self.timer)
        self.interrupts.memory = self.memory  # Now connect them
        self.input.memory = self.memory  # Connect input too
        self.apu.memory = self.memory  # Connect audio too
        self.cpu = CPU(self.memory)
        self.ppu = PPU(self.memory, self.interrupts)
        
        # Emulator state
        self.running = False
        self.paused = False
        self.frame_skip = 0  # 0 = no skip, 1 = render every other frame, etc.
        self.turbo_mode = False  # Uncapped speed mode
        
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
                
                # Only render if not frame skipping
                if self.frame_count % (self.frame_skip + 1) == 0:
                    self.render()
            
            # Cap FPS unless in turbo mode
            if self.turbo_mode:
                self.clock.tick()  # Uncapped - run as fast as possible
            else:
                self.clock.tick(self.fps)  # Normal - cap at 60 FPS
            
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
        target_cycles = 70224  # Cycles per frame at ~4.19 MHz / 60 FPS
        frame_cycles = 0
        
        while frame_cycles < target_cycles:
            # Execute one CPU instruction
            cycles_before = self.cpu.cycles
            self.cpu.step()
            cycles_executed = self.cpu.cycles - cycles_before
            
            # Prevent infinite loop if CPU is stuck
            if cycles_executed == 0:
                cycles_executed = 4
                self.cpu.cycles += 4
            
            # Update PPU
            self.ppu.step(cycles_executed)
            
            # Update Timer (CRITICAL for games like Tetris!)
            self.timer.step(cycles_executed)
            
            # Handle interrupts
            self.interrupts.handle_interrupts(self.cpu)
            
            frame_cycles += cycles_executed
            
            # Safety break - don't hang if something goes wrong
            if frame_cycles > target_cycles * 2:
                print(f"[WARNING] Frame took {frame_cycles} cycles (expected {target_cycles})")
                break
        
        # Update audio once per frame (less CPU intensive)
        if self.apu.enabled and self.apu.audio_enabled:
            self.apu.step(target_cycles)
    
    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # ALWAYS print when ANY key is pressed
                key_name = pygame.key.name(event.key)
                print(f"[KEYPRESS] {key_name} (code: {event.key})")
                
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"[GameBoy] {'Paused' if self.paused else 'Resumed'}")
                elif event.key == pygame.K_m:
                    self.apu.enabled = not self.apu.enabled
                    status = "ON" if self.apu.enabled else "OFF"
                    print(f"[GameBoy] Audio {status}")
                elif event.key == pygame.K_t:
                    self.turbo_mode = not self.turbo_mode
                    status = "ON (Uncapped FPS)" if self.turbo_mode else "OFF (60 FPS)"
                    print(f"[GameBoy] Turbo Mode {status}")
                else:
                    # Pass ALL other keys to game
                    print(f"[PASSING] {key_name} to input handler")
                    self.input.handle_key_down(event.key)
            
            elif event.type == pygame.KEYUP:
                self.input.handle_key_up(event.key)
    
    def render(self):
        """Render the display - FASTEST METHOD"""
        # Draw each scanline as a horizontal line (much faster than individual pixels)
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                color = self.colors[self.ppu.screen[y][x]]
                # Draw scaled pixel rect
                self.screen.fill(color, (x * SCALE, y * SCALE, SCALE, SCALE))
        
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