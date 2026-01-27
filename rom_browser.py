"""
ROM File Browser
Simple GUI to select ROM files
"""

import os
import pygame
from pathlib import Path

class ROMBrowser:
    """Simple ROM file browser"""
    
    def __init__(self, roms_folder="roms"):
        pygame.init()
        
        # Window setup
        self.width = 640
        self.height = 480
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Game Boy ROM Browser - Select a ROM")
        
        # Colors
        self.bg_color = (15, 56, 15)  # Dark green
        self.text_color = (155, 188, 15)  # Light green
        self.selected_color = (139, 172, 15)  # Medium green
        self.header_color = (48, 98, 48)  # Mid green
        
        # Font
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # ROM list
        self.roms_folder = roms_folder
        self.roms = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible = 15
        
        # Load ROM list
        self.load_roms()
        
        self.clock = pygame.time.Clock()
    
    def load_roms(self):
        """Load list of ROM files from roms folder"""
        if not os.path.exists(self.roms_folder):
            os.makedirs(self.roms_folder)
            print(f"[Browser] Created {self.roms_folder} folder")
        
        # Find all .gb and .gbc files
        rom_files = []
        for ext in ['*.gb', '*.gbc', '*.GB', '*.GBC']:
            rom_files.extend(Path(self.roms_folder).glob(ext))
        
        # Sort by name
        self.roms = sorted([str(rom) for rom in rom_files])
        
        if not self.roms:
            print(f"[Browser] No ROMs found in {self.roms_folder}/")
            print("[Browser] Please add .gb or .gbc files to the roms folder")
    
    def run(self):
        """Run the browser and return selected ROM path"""
        if not self.roms:
            print("\n" + "="*50)
            print("NO ROMS FOUND!")
            print("="*50)
            print(f"Please add ROM files (.gb or .gbc) to the '{self.roms_folder}/' folder")
            print("\nYou can download free homebrew ROMs from:")
            print("  - https://gbhh.avivace.com/")
            print("  - https://itch.io/games/tag-game-boy")
            print("\nPress any key to exit...")
            
            # Wait for key press
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        waiting = False
                    elif event.type == pygame.KEYDOWN:
                        waiting = False
                
                self.screen.fill(self.bg_color)
                self.draw_no_roms_message()
                pygame.display.flip()
                self.clock.tick(30)
            
            return None
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.selected_index = max(0, self.selected_index - 1)
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.selected_index = min(len(self.roms) - 1, self.selected_index + 1)
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_PAGEUP:
                        self.selected_index = max(0, self.selected_index - 10)
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_PAGEDOWN:
                        self.selected_index = min(len(self.roms) - 1, self.selected_index + 10)
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_HOME:
                        self.selected_index = 0
                        self.scroll_offset = 0
                    
                    elif event.key == pygame.K_END:
                        self.selected_index = len(self.roms) - 1
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        return self.roms[self.selected_index]
                    
                    elif event.key == pygame.K_r:
                        # Refresh ROM list
                        self.load_roms()
                        self.selected_index = 0
                        self.scroll_offset = 0
            
            # Draw
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)
        
        return None
    
    def adjust_scroll(self):
        """Adjust scroll offset to keep selection visible"""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_index - self.max_visible + 1
    
    def draw(self):
        """Draw the browser interface"""
        self.screen.fill(self.bg_color)
        
        # Draw title
        title = self.title_font.render("Game Boy ROM Browser", True, self.text_color)
        title_rect = title.get_rect(center=(self.width // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Draw instructions
        instructions = [
            "Arrow Keys / WASD: Navigate",
            "Enter / Space: Select ROM",
            "R: Refresh List",
            "ESC: Exit"
        ]
        y = 70
        for instruction in instructions:
            text = self.font.render(instruction, True, self.header_color)
            self.screen.blit(text, (20, y))
            y += 25
        
        # Draw separator
        pygame.draw.line(self.screen, self.text_color, (10, 170), (self.width - 10, 170), 2)
        
        # Draw ROM list
        y = 190
        visible_roms = self.roms[self.scroll_offset:self.scroll_offset + self.max_visible]
        
        for i, rom_path in enumerate(visible_roms):
            actual_index = self.scroll_offset + i
            rom_name = os.path.basename(rom_path)
            
            # Highlight selected
            if actual_index == self.selected_index:
                rect = pygame.Rect(10, y - 5, self.width - 20, 25)
                pygame.draw.rect(self.screen, self.selected_color, rect)
                color = self.bg_color
            else:
                color = self.text_color
            
            # Draw ROM name
            text = self.font.render(f"{actual_index + 1}. {rom_name}", True, color)
            self.screen.blit(text, (20, y))
            y += 25
        
        # Draw scroll indicator
        if len(self.roms) > self.max_visible:
            total_height = 300
            scroll_height = max(20, (self.max_visible / len(self.roms)) * total_height)
            scroll_y = 190 + (self.scroll_offset / len(self.roms)) * total_height
            
            pygame.draw.rect(self.screen, self.header_color, 
                           (self.width - 15, 190, 5, total_height))
            pygame.draw.rect(self.screen, self.text_color,
                           (self.width - 15, scroll_y, 5, scroll_height))
        
        # Draw footer
        footer = self.font.render(f"Found {len(self.roms)} ROM(s) in {self.roms_folder}/", 
                                 True, self.header_color)
        footer_rect = footer.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(footer, footer_rect)
    
    def draw_no_roms_message(self):
        """Draw message when no ROMs are found"""
        messages = [
            "NO ROMS FOUND!",
            "",
            f"Please add .gb or .gbc files to:",
            f"  {os.path.abspath(self.roms_folder)}/",
            "",
            "Free homebrew ROMs:",
            "  https://gbhh.avivace.com/",
            "  https://itch.io/games/tag-game-boy",
            "",
            "Press any key to exit..."
        ]
        
        y = 100
        for i, message in enumerate(messages):
            if i == 0:
                text = self.title_font.render(message, True, self.text_color)
            else:
                text = self.font.render(message, True, self.text_color if message else self.bg_color)
            
            text_rect = text.get_rect(center=(self.width // 2, y))
            self.screen.blit(text, text_rect)
            y += 35 if i == 0 else 25
    
    def quit(self):
        """Clean up"""
        pygame.quit()


def select_rom(roms_folder="roms"):
    """Helper function to select a ROM"""
    browser = ROMBrowser(roms_folder)
    selected_rom = browser.run()
    browser.quit()
    return selected_rom