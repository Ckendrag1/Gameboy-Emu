"""
Game Boy Emulator - Main Entry Point
Run this file to start the emulator
"""

import sys
import os
from gameboy import GameBoy

def main():
    """Main entry point"""
    print("=" * 50)
    print("Game Boy Emulator")
    print("=" * 50)
    
    # Create emulator instance
    emulator = GameBoy()
    
    # Check if ROM file was provided
    if len(sys.argv) > 1:
        rom_file = sys.argv[1]
        
        # Check if file exists
        if not os.path.exists(rom_file):
            print(f"Error: ROM file not found: {rom_file}")
            return
        
        # Load ROM
        if emulator.load_rom(rom_file):
            print("\nStarting emulation...")
            emulator.run()
        else:
            print("Failed to load ROM")
    else:
        print("\nUsage: python main.py <rom_file.gb>")
        print("\nExample:")
        print("  python main.py roms/tetris.gb")
        print("\nRunning in demo mode (no ROM loaded)...")
        print("Note: Without a ROM, you'll just see a test pattern")
        
        # Run anyway for testing
        response = input("\nRun without ROM? (y/n): ")
        if response.lower() == 'y':
            emulator.run()
    
    # Clean up
    emulator.quit()

if __name__ == "__main__":
    main()