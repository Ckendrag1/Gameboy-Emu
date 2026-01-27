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
    print("  M      - Toggle Audio (Mute/Unmute)")
    print("  ESC    - Quit")
    print("  F11    - Toggle Fullscreen (if supported)")
    print("="*50 + "\n")

def main():
    """Main entry point"""
    print("=" * 50)
    print("Game Boy Emulator")
    print("=" * 50)
    
    rom_file = None
    enable_audio = True
    
    # Check command line arguments
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--no-audio" or arg == "-na":
                enable_audio = False
                print("Audio disabled via command line")
            elif os.path.exists(arg):
                rom_file = arg
    
    # If no ROM provided, launch browser
    if rom_file is None:
        print("\nLaunching ROM browser...")
        rom_file = select_rom("roms")
        
        if rom_file is None:
            print("\nNo ROM selected. Exiting...")
            return
    
    # Create emulator instance
    emulator = GameBoy(enable_audio=enable_audio)
    
    # Load ROM
    print(f"\nLoading ROM: {rom_file}")
    if emulator.load_rom(rom_file):
        print_controls()
        print("Starting emulation...")
        if not enable_audio:
            print("⚠️  Audio is DISABLED")
        print("Have fun!\n")
        emulator.run()
    else:
        print("Failed to load ROM")
    
    # Clean up
    emulator.quit()
    print("\nThanks for playing!")

if __name__ == "__main__":
    main()