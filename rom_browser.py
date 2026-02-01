"""
ROM File Browser - Enhanced GUI
Features: ROM selection, palette picker, settings
"""

import os
import pygame
from pathlib import Path

class ROMBrowser:
    """Enhanced ROM file browser with settings"""
    
    def __init__(self, roms_folder="roms"):
        pygame.init()
        
        # Window setup
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Game Boy Emulator - Setup")
        
        # Colors - Modern dark theme
        self.bg_color = (32, 32, 40)
        self.panel_color = (45, 45, 55)
        self.text_color = (220, 220, 230)
        self.selected_color = (70, 130, 180)  # Steel blue
        self.accent_color = (100, 200, 100)   # Green accent
        self.button_color = (60, 60, 70)
        self.button_hover = (80, 80, 90)
        
        # Fonts
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 22)
        except:
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
            self.font = pygame.font.SysFont('Arial', 28)
            self.small_font = pygame.font.SysFont('Arial', 22)
        
        # ROM list
        self.roms_folder = roms_folder
        self.roms = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible = 12
        
        # Settings
        self.palettes = {
            "Classic Green": [(155, 188, 15), (139, 172, 15), (48, 98, 48), (15, 56, 15)],
            "Grayscale": [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)],
            "GB Pocket": [(224, 248, 208), (136, 192, 112), (52, 104, 86), (8, 24, 32)],
            "Blue": [(224, 248, 255), (120, 184, 232), (52, 104, 152), (8, 24, 48)],
            "Red": [(255, 224, 224), (232, 120, 120), (152, 52, 52), (48, 8, 8)]
        }
        self.palette_names = list(self.palettes.keys())
        self.selected_palette = 0
        self.enable_audio = True
        
        # UI state
        self.hover_button = None
        
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
    
    def run(self):
        """Run the browser and return (ROM path, palette, audio_enabled)"""
        if not self.roms:
            result = self.show_no_roms_screen()
            if result:
                self.load_roms()
                if not self.roms:
                    return None
            else:
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
                    
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.selected_palette = (self.selected_palette - 1) % len(self.palette_names)
                    
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.selected_palette = (self.selected_palette + 1) % len(self.palette_names)
                    
                    elif event.key == pygame.K_m:
                        self.enable_audio = not self.enable_audio
                    
                    elif event.key == pygame.K_PAGEUP:
                        self.selected_index = max(0, self.selected_index - 5)
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_PAGEDOWN:
                        self.selected_index = min(len(self.roms) - 1, self.selected_index + 5)
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_HOME:
                        self.selected_index = 0
                        self.scroll_offset = 0
                    
                    elif event.key == pygame.K_END:
                        self.selected_index = len(self.roms) - 1
                        self.adjust_scroll()
                    
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Return ROM path, selected palette, and audio setting
                        palette = self.palettes[self.palette_names[self.selected_palette]]
                        return (self.roms[self.selected_index], palette, self.enable_audio)
                    
                    elif event.key == pygame.K_r:
                        # Refresh ROM list
                        self.load_roms()
                        self.selected_index = 0
                        self.scroll_offset = 0
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        if self.hover_button == "start":
                            palette = self.palettes[self.palette_names[self.selected_palette]]
                            return (self.roms[self.selected_index], palette, self.enable_audio)
                        elif self.hover_button == "audio":
                            self.enable_audio = not self.enable_audio
                
                elif event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:  # Scroll up
                        self.selected_index = max(0, self.selected_index - 1)
                        self.adjust_scroll()
                    elif event.y < 0:  # Scroll down
                        self.selected_index = min(len(self.roms) - 1, self.selected_index + 1)
                        self.adjust_scroll()
            
            # Draw
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        return None
    
    def adjust_scroll(self):
        """Adjust scroll offset to keep selection visible"""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_index - self.max_visible + 1
    
    def draw(self):
        """Draw the browser interface - Modern design"""
        self.screen.fill(self.bg_color)
        mouse_pos = pygame.mouse.get_pos()
        self.hover_button = None
        
        # Header
        title = self.title_font.render("Game Boy Emulator", True, self.accent_color)
        title_rect = title.get_rect(center=(self.width // 2, 40))
        self.screen.blit(title, title_rect)
        
        # Left panel - ROM List
        left_panel = pygame.Rect(20, 90, 450, 490)
        pygame.draw.rect(self.screen, self.panel_color, left_panel, border_radius=10)
        pygame.draw.rect(self.screen, self.selected_color, left_panel, 2, border_radius=10)
        
        # ROM list title
        list_title = self.font.render(f"ROMs ({len(self.roms)})", True, self.text_color)
        self.screen.blit(list_title, (left_panel.x + 15, left_panel.y + 10))
        
        # Draw ROM list
        y = left_panel.y + 50
        visible_roms = self.roms[self.scroll_offset:self.scroll_offset + self.max_visible]
        
        for i, rom_path in enumerate(visible_roms):
            actual_index = self.scroll_offset + i
            rom_name = os.path.basename(rom_path)
            
            # Truncate long names
            if len(rom_name) > 35:
                rom_name = rom_name[:32] + "..."
            
            # Highlight selected
            if actual_index == self.selected_index:
                highlight_rect = pygame.Rect(left_panel.x + 10, y - 3, left_panel.width - 20, 32)
                pygame.draw.rect(self.screen, self.selected_color, highlight_rect, border_radius=5)
                color = (255, 255, 255)
            else:
                color = self.text_color
            
            # Draw ROM name
            text = self.small_font.render(rom_name, True, color)
            self.screen.blit(text, (left_panel.x + 20, y))
            y += 35
        
        # Scroll indicator
        if len(self.roms) > self.max_visible:
            scrollbar_height = 400
            scroll_y = left_panel.y + 50 + (self.scroll_offset / len(self.roms)) * scrollbar_height
            scroll_h = max(20, (self.max_visible / len(self.roms)) * scrollbar_height)
            
            pygame.draw.rect(self.screen, (60, 60, 70), 
                           (left_panel.right - 15, left_panel.y + 50, 5, scrollbar_height), border_radius=3)
            pygame.draw.rect(self.screen, self.selected_color,
                           (left_panel.right - 15, scroll_y, 5, scroll_h), border_radius=3)
        
        # Right panel - Settings
        right_panel = pygame.Rect(490, 90, 290, 490)
        pygame.draw.rect(self.screen, self.panel_color, right_panel, border_radius=10)
        pygame.draw.rect(self.screen, self.selected_color, right_panel, 2, border_radius=10)
        
        # Settings title
        settings_title = self.font.render("Settings", True, self.text_color)
        self.screen.blit(settings_title, (right_panel.x + 15, right_panel.y + 10))
        
        y = right_panel.y + 60
        
        # Palette selector
        palette_label = self.small_font.render("Color Palette:", True, self.text_color)
        self.screen.blit(palette_label, (right_panel.x + 15, y))
        y += 30
        
        palette_name = self.palette_names[self.selected_palette]
        palette_text = self.font.render(palette_name, True, self.accent_color)
        palette_rect = palette_text.get_rect(center=(right_panel.centerx, y + 15))
        self.screen.blit(palette_text, palette_rect)
        
        # Palette preview
        y += 50
        palette_colors = self.palettes[palette_name]
        color_width = 60
        start_x = right_panel.centerx - (color_width * 2)
        
        for i, color in enumerate(palette_colors):
            rect = pygame.Rect(start_x + (i * color_width), y, color_width - 5, 40)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, (100, 100, 110), rect, 2, border_radius=5)
        
        # Arrow hints
        y += 50
        hint = self.small_font.render("← →  Change Palette", True, (150, 150, 160))
        hint_rect = hint.get_rect(center=(right_panel.centerx, y))
        self.screen.blit(hint, hint_rect)
        
        # Audio toggle button
        y += 60
        audio_label = self.small_font.render("Audio:", True, self.text_color)
        self.screen.blit(audio_label, (right_panel.x + 15, y))
        
        audio_button = pygame.Rect(right_panel.x + 15, y + 30, 260, 40)
        
        # Check hover
        if audio_button.collidepoint(mouse_pos):
            self.hover_button = "audio"
            button_color = self.button_hover
        else:
            button_color = self.button_color
        
        pygame.draw.rect(self.screen, button_color, audio_button, border_radius=8)
        pygame.draw.rect(self.screen, self.selected_color if self.enable_audio else (100, 100, 110), 
                        audio_button, 2, border_radius=8)
        
        audio_status = "ON" if self.enable_audio else "OFF"
        audio_text = self.font.render(f"Audio: {audio_status}", True, 
                                     self.accent_color if self.enable_audio else (180, 180, 190))
        text_rect = audio_text.get_rect(center=audio_button.center)
        self.screen.blit(audio_text, text_rect)
        
        # Start button
        y += 100
        start_button = pygame.Rect(right_panel.x + 15, y, 260, 50)
        
        # Check hover
        if start_button.collidepoint(mouse_pos):
            self.hover_button = "start"
            button_color = self.accent_color
        else:
            button_color = self.selected_color
        
        pygame.draw.rect(self.screen, button_color, start_button, border_radius=10)
        
        start_text = self.title_font.render("START", True, (255, 255, 255))
        text_rect = start_text.get_rect(center=start_button.center)
        self.screen.blit(start_text, text_rect)
        
        # Controls help
        y = self.height - 80
        controls = [
            "↑↓ Select ROM  •  ←→ Change Palette  •  M Toggle Audio",
            "Enter/Space Start  •  R Refresh  •  ESC Exit"
        ]
        
        for i, text in enumerate(controls):
            help_text = self.small_font.render(text, True, (120, 120, 130))
            help_rect = help_text.get_rect(center=(self.width // 2, y + i * 25))
            self.screen.blit(help_text, help_rect)
    
    def show_no_roms_screen(self):
        """Show screen when no ROMs are found"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_r:
                        return True
            
            self.screen.fill(self.bg_color)
            
            # Title
            title = self.title_font.render("No ROMs Found!", True, (255, 100, 100))
            title_rect = title.get_rect(center=(self.width // 2, 100))
            self.screen.blit(title, title_rect)
            
            # Instructions
            messages = [
                f"Please add .gb or .gbc files to:",
                f"{os.path.abspath(self.roms_folder)}/",
                "",
                "Free homebrew ROMs:",
                "• https://gbhh.avivace.com/",
                "• https://itch.io/games/tag-game-boy",
                "",
                "Press R to refresh",
                "Press ESC to exit"
            ]
            
            y = 200
            for msg in messages:
                if msg.startswith("•") or msg.startswith("http"):
                    color = self.accent_color
                    font = self.small_font
                else:
                    color = self.text_color
                    font = self.font
                
                text = font.render(msg, True, color)
                text_rect = text.get_rect(center=(self.width // 2, y))
                self.screen.blit(text, text_rect)
                y += 40
            
            pygame.display.flip()
            self.clock.tick(30)
        
        return False
    
    def quit(self):
        """Clean up"""
        pygame.quit()


def select_rom(roms_folder="roms"):
    """Helper function to select a ROM and get settings"""
    browser = ROMBrowser(roms_folder)
    result = browser.run()
    browser.quit()
    return result