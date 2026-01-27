"""
Game Boy Emulator - Main Entry Point
Run this file to start the emulator
"""

import sys
import os
from gameboy import GameBoy
from rom_browser import select_rom

def print_controls():
    """Print control scheme"""
    print("\n" + "="*50)
    print("CONTROLS")
    print("="*50)
    print("Game Boy Controls:")
    print("  Arrow Keys / WASD - D-Pad")
    print("  Z / Space         - A Button")
    print("  X / Left Shift    - B Button")
    print("  Enter             - Start")
    print("  Tab / Backspace   - Select")
    print("")
    print("Emulator Controls:")
    print("  P      - Pause/Resume")
    print("  ESC    - Quit")
    print("  F11    - Toggle Fullscreen (if supported)")
    print("="*50 + "\n")

def main():
    """Main entry point"""
    print("=" * 50)
    print("Game Boy Emulator")
    print("=" * 50)
    
    rom_file = None
    
    # Check if ROM file was provided as command line argument
    if len(sys.argv) > 1:
        rom_file = sys.argv[1]
        
        # Check if file exists
        if not os.path.exists(rom_file):
            print(f"Error: ROM file not found: {rom_file}")
            print("\nLaunching ROM browser instead...")
            rom_file = None
    
    # If no ROM provided, launch browser
    if rom_file is None:
        print("\nLaunching ROM browser...")
        rom_file = select_rom("roms")
        
        if rom_file is None:
            print("\nNo ROM selected. Exiting...")
            return
    
    # Create emulator instance
    emulator = GameBoy()
    
    # Load ROM
    print(f"\nLoading ROM: {rom_file}")
    if emulator.load_rom(rom_file):
        print_controls()
        print("Starting emulation...")
        print("Have fun!\n")
        emulator.run()
    else:
        print("Failed to load ROM")
    
    # Clean up
    emulator.quit()
    print("\nThanks for playing!")

if __name__ == "__main__":
    main()
