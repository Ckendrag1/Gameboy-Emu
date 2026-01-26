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
    
    def __init__(self):
        # Button states (True = pressed)
        self.buttons = [False] * 8
        
        # Key mapping (default)
        self.key_map = {
            pygame.K_z: self.BUTTON_A,        # Z = A
            pygame.K_x: self.BUTTON_B,        # X = B
            pygame.K_RETURN: self.BUTTON_START,   # Enter = Start
            pygame.K_RSHIFT: self.BUTTON_SELECT,  # Right Shift = Select
            pygame.K_RIGHT: self.BUTTON_RIGHT,
            pygame.K_LEFT: self.BUTTON_LEFT,
            pygame.K_UP: self.BUTTON_UP,
            pygame.K_DOWN: self.BUTTON_DOWN,
        }
    
    def handle_key_down(self, key):
        """Handle key press"""
        if key in self.key_map:
            button = self.key_map[key]
            self.buttons[button] = True
            # TODO: Trigger joypad interrupt if enabled
    
    def handle_key_up(self, key):
        """Handle key release"""
        if key in self.key_map:
            button = self.key_map[key]
            self.buttons[button] = False
    
    def is_button_pressed(self, button):
        """Check if a button is currently pressed"""
        return self.buttons[button]
    
    def get_joypad_state(self):
        """
        Get joypad state for memory register (0xFF00)
        TODO: Implement proper P1 register behavior
        """
        # The P1 register (0xFF00) works differently:
        # Bit 5: P15 Select Button Keys (0=Select)
        # Bit 4: P14 Select Direction Keys (0=Select)
        # Bit 3: P13 Input Down or Start (0=Pressed)
        # Bit 2: P12 Input Up or Select (0=Pressed)
        # Bit 1: P11 Input Left or B (0=Pressed)
        # Bit 0: P10 Input Right or A (0=Pressed)
        
        state = 0xFF  # All bits high (not pressed)
        
        # This is simplified - actual implementation needs to check
        # which button group is selected via bits 4-5
        
        return state
    
    def reset(self):
        """Reset all button states"""
        self.buttons = [False] * 8