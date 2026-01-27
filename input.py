"""
Game Boy Input Handler
Maps keyboard to Game Boy buttons
"""

import pygame

class Input:
    """Game Boy joypad input handler"""
    
    # Game Boy buttons
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_SELECT = 2
    BUTTON_START = 3
    BUTTON_RIGHT = 4
    BUTTON_LEFT = 5
    BUTTON_UP = 6
    BUTTON_DOWN = 7
    
    def __init__(self, memory=None):
        self.memory = memory
        
        # Button states (True = pressed)
        self.buttons = [False] * 8
        
        # Key mapping (multiple options for each button)
        self.key_map = {
            # A Button (primary: Z, alt: Space)
            pygame.K_z: self.BUTTON_A,
            pygame.K_SPACE: self.BUTTON_A,
            
            # B Button (primary: X, alt: Left Shift)
            pygame.K_x: self.BUTTON_B,
            pygame.K_LSHIFT: self.BUTTON_B,
            
            # Start (Enter)
            pygame.K_RETURN: self.BUTTON_START,
            pygame.K_KP_ENTER: self.BUTTON_START,
            
            # Select (Right Shift, Backspace, Tab)
            pygame.K_RSHIFT: self.BUTTON_SELECT,
            pygame.K_BACKSPACE: self.BUTTON_SELECT,
            pygame.K_TAB: self.BUTTON_SELECT,
            
            # D-Pad (Arrow keys and WASD)
            pygame.K_RIGHT: self.BUTTON_RIGHT,
            pygame.K_d: self.BUTTON_RIGHT,
            
            pygame.K_LEFT: self.BUTTON_LEFT,
            pygame.K_a: self.BUTTON_LEFT,
            
            pygame.K_UP: self.BUTTON_UP,
            pygame.K_w: self.BUTTON_UP,
            
            pygame.K_DOWN: self.BUTTON_DOWN,
            pygame.K_s: self.BUTTON_DOWN,
        }
        
        # P1 register state
        self.p1 = 0xFF  # All buttons released
        self.select_buttons = False  # Select button keys (A,B,Select,Start)
        self.select_dpad = False     # Select direction keys
    
    def handle_key_down(self, key):
        """Handle key press"""
        if key in self.key_map:
            button = self.key_map[key]
            self.buttons[button] = True
            self.update_p1_register()
    
    def handle_key_up(self, key):
        """Handle key release"""
        if key in self.key_map:
            button = self.key_map[key]
            self.buttons[button] = False
            self.update_p1_register()
    
    def is_button_pressed(self, button):
        """Check if a button is currently pressed"""
        return self.buttons[button]
    
    def read_p1(self):
        """
        Read P1 register (0xFF00)
        
        P1 register format:
        Bit 7-6: Not used
        Bit 5: P15 Select Button Keys (0=Select)
        Bit 4: P14 Select Direction Keys (0=Select)
        Bit 3: P13 Input Down or Start (0=Pressed)
        Bit 2: P12 Input Up or Select (0=Pressed)
        Bit 1: P11 Input Left or B (0=Pressed)
        Bit 0: P10 Input Right or A (0=Pressed)
        """
        result = 0xCF  # Start with bits 7-6 set, bits 3-0 set (not pressed)
        
        # Check which button group is selected
        if not self.select_buttons:
            # Button keys selected (A, B, Select, Start)
            if self.buttons[self.BUTTON_START]:
                result &= ~0x08  # Bit 3
            if self.buttons[self.BUTTON_SELECT]:
                result &= ~0x04  # Bit 2
            if self.buttons[self.BUTTON_B]:
                result &= ~0x02  # Bit 1
            if self.buttons[self.BUTTON_A]:
                result &= ~0x01  # Bit 0
            result &= ~0x20  # Clear bit 5 to show buttons are selected
        
        if not self.select_dpad:
            # Direction keys selected (Up, Down, Left, Right)
            if self.buttons[self.BUTTON_DOWN]:
                result &= ~0x08  # Bit 3
            if self.buttons[self.BUTTON_UP]:
                result &= ~0x04  # Bit 2
            if self.buttons[self.BUTTON_LEFT]:
                result &= ~0x02  # Bit 1
            if self.buttons[self.BUTTON_RIGHT]:
                result &= ~0x01  # Bit 0
            result &= ~0x10  # Clear bit 4 to show dpad is selected
        
        return result
    
    def write_p1(self, value):
        """
        Write to P1 register (0xFF00)
        Game writes to select which button group to read
        """
        # Bit 5: Select button keys (0=select)
        self.select_buttons = not (value & 0x20)
        
        # Bit 4: Select direction keys (0=select)
        self.select_dpad = not (value & 0x10)
        
        self.update_p1_register()
    
    def update_p1_register(self):
        """Update the P1 register in memory"""
        if self.memory:
            self.p1 = self.read_p1()
            # Write to I/O register
            self.memory.io[0x00] = self.p1
    
    def reset(self):
        """Reset all button states"""
        self.buttons = [False] * 8
        self.p1 = 0xFF
        self.select_buttons = False
        self.select_dpad = False