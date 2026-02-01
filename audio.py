"""
Game Boy APU (Audio Processing Unit) - Improved Version
Handles 4 sound channels with proper timing and envelopes
"""

import pygame
import numpy as np
from collections import deque

class APU:
    """Game Boy Audio Processing Unit - Improved"""
    
    def __init__(self, memory, enabled=True):
        self.memory = memory
        self.enabled = enabled
        
        if not self.enabled:
            return
        
        # Initialize pygame audio with better settings
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.init()
            self.audio_enabled = True
            print("[APU] Audio initialized: 44100Hz, Stereo, 2048 buffer")
        except Exception as e:
            print(f"[APU] Failed to initialize audio: {e}")
            self.audio_enabled = False
            return
        
        # Sample rate and timing
        self.sample_rate = 44100
        self.buffer_size = 2048
        self.cycles_per_sample = 95  # ~4194304 / 44100
        self.cycle_counter = 0
        
        # Frame sequencer (512 Hz)
        self.frame_sequencer_counter = 0
        self.frame_sequencer_step = 0
        
        # Audio buffer (using deque for better performance)
        self.audio_buffer = deque(maxlen=8192)
        
        # Duty cycle patterns (8 steps each)
        self.duty_patterns = [
            [0, 0, 0, 0, 0, 0, 0, 1],  # 12.5%
            [1, 0, 0, 0, 0, 0, 0, 1],  # 25%
            [1, 0, 0, 0, 0, 1, 1, 1],  # 50%
            [0, 1, 1, 1, 1, 1, 1, 0],  # 75%
        ]
        
        # Channel 1 (Square with sweep)
        self.ch1 = {
            'enabled': False,
            'dac_enabled': False,
            'frequency': 0,
            'frequency_shadow': 0,
            'duty': 2,
            'duty_position': 0,
            'volume': 0,
            'envelope_volume': 0,
            'envelope_period': 0,
            'envelope_counter': 0,
            'envelope_direction': 0,
            'length_counter': 0,
            'length_enabled': False,
            'sweep_period': 0,
            'sweep_shift': 0,
            'sweep_direction': 0,
            'sweep_counter': 0,
            'sweep_enabled': False,
        }
        
        # Channel 2 (Square)
        self.ch2 = {
            'enabled': False,
            'dac_enabled': False,
            'frequency': 0,
            'duty': 2,
            'duty_position': 0,
            'volume': 0,
            'envelope_volume': 0,
            'envelope_period': 0,
            'envelope_counter': 0,
            'envelope_direction': 0,
            'length_counter': 0,
            'length_enabled': False,
        }
        
        # Channel 3 (Wave)
        self.ch3 = {
            'enabled': False,
            'dac_enabled': False,
            'frequency': 0,
            'volume_code': 0,
            'sample_position': 0,
            'length_counter': 0,
            'length_enabled': False,
        }
        self.wave_ram = [0] * 32  # 16 bytes, 2 samples per byte
        
        # Channel 4 (Noise)
        self.ch4 = {
            'enabled': False,
            'dac_enabled': False,
            'lfsr': 0x7FFF,  # Linear Feedback Shift Register
            'volume': 0,
            'envelope_volume': 0,
            'envelope_period': 0,
            'envelope_counter': 0,
            'envelope_direction': 0,
            'length_counter': 0,
            'length_enabled': False,
            'clock_shift': 0,
            'width_mode': 0,
            'divisor_code': 0,
            'frequency_timer': 0,
        }
        
        # Master control
        self.sound_enabled = True
        self.master_volume_left = 7
        self.master_volume_right = 7
        
        # Channel panning (NR51)
        self.ch1_left = True
        self.ch1_right = True
        self.ch2_left = True
        self.ch2_right = True
        self.ch3_left = True
        self.ch3_right = True
        self.ch4_left = True
        self.ch4_right = True
        
        # Frequency timers
        self.ch1_freq_timer = 0
        self.ch2_freq_timer = 0
        self.ch3_freq_timer = 0
    
    def step(self, cycles):
        """Update APU state"""
        if not self.audio_enabled or not self.enabled or not self.sound_enabled:
            return
        
        # Update frame sequencer (512 Hz)
        self.frame_sequencer_counter += cycles
        if self.frame_sequencer_counter >= 8192:  # ~512 Hz
            self.frame_sequencer_counter -= 8192
            self.clock_frame_sequencer()
        
        # Generate audio samples
        self.cycle_counter += cycles
        while self.cycle_counter >= self.cycles_per_sample:
            self.cycle_counter -= self.cycles_per_sample
            
            # Generate sample from all channels
            left, right = self.generate_sample()
            self.audio_buffer.append((left, right))
        
        # Play buffer when full enough
        if len(self.audio_buffer) >= self.buffer_size:
            self.play_buffer()
    
    def clock_frame_sequencer(self):
        """Clock the frame sequencer (512 Hz)"""
        # Step 0, 2, 4, 6: Clock length
        if self.frame_sequencer_step % 2 == 0:
            self.clock_length_counters()
        
        # Step 7: Clock envelope
        if self.frame_sequencer_step == 7:
            self.clock_envelopes()
        
        # Step 2, 6: Clock sweep
        if self.frame_sequencer_step == 2 or self.frame_sequencer_step == 6:
            self.clock_sweep()
        
        self.frame_sequencer_step = (self.frame_sequencer_step + 1) % 8
    
    def clock_length_counters(self):
        """Clock length counters"""
        for ch in [self.ch1, self.ch2, self.ch3, self.ch4]:
            if ch['length_enabled'] and ch['length_counter'] > 0:
                ch['length_counter'] -= 1
                if ch['length_counter'] == 0:
                    ch['enabled'] = False
    
    def clock_envelopes(self):
        """Clock volume envelopes"""
        for ch in [self.ch1, self.ch2, self.ch4]:
            if ch['envelope_period'] > 0:
                ch['envelope_counter'] += 1
                if ch['envelope_counter'] >= ch['envelope_period']:
                    ch['envelope_counter'] = 0
                    
                    new_volume = ch['envelope_volume']
                    if ch['envelope_direction'] == 1:  # Increase
                        new_volume += 1
                    else:  # Decrease
                        new_volume -= 1
                    
                    if 0 <= new_volume <= 15:
                        ch['envelope_volume'] = new_volume
    
    def clock_sweep(self):
        """Clock frequency sweep (Channel 1 only)"""
        if not self.ch1['sweep_enabled']:
            return
        
        self.ch1['sweep_counter'] += 1
        if self.ch1['sweep_counter'] >= self.ch1['sweep_period']:
            self.ch1['sweep_counter'] = 0
            
            if self.ch1['sweep_period'] > 0:
                new_freq = self.calculate_sweep_frequency()
                
                if new_freq <= 2047 and self.ch1['sweep_shift'] > 0:
                    self.ch1['frequency'] = new_freq
                    self.ch1['frequency_shadow'] = new_freq
    
    def calculate_sweep_frequency(self):
        """Calculate new sweep frequency"""
        offset = self.ch1['frequency_shadow'] >> self.ch1['sweep_shift']
        
        if self.ch1['sweep_direction'] == 0:  # Increase
            return self.ch1['frequency_shadow'] + offset
        else:  # Decrease
            return self.ch1['frequency_shadow'] - offset
    
    def generate_sample(self):
        """Generate one stereo audio sample"""
        left = 0.0
        right = 0.0
        
        if not self.sound_enabled:
            return (0, 0)
        
        # Mix Channel 1
        if self.ch1['enabled'] and self.ch1['dac_enabled']:
            sample = self.generate_square_wave(self.ch1, 1)
            if self.ch1_left:
                left += sample
            if self.ch1_right:
                right += sample
        
        # Mix Channel 2
        if self.ch2['enabled'] and self.ch2['dac_enabled']:
            sample = self.generate_square_wave(self.ch2, 2)
            if self.ch2_left:
                left += sample
            if self.ch2_right:
                right += sample
        
        # Mix Channel 3
        if self.ch3['enabled'] and self.ch3['dac_enabled']:
            sample = self.generate_wave()
            if self.ch3_left:
                left += sample
            if self.ch3_right:
                right += sample
        
        # Mix Channel 4
        if self.ch4['enabled'] and self.ch4['dac_enabled']:
            sample = self.generate_noise()
            if self.ch4_left:
                left += sample
            if self.ch4_right:
                right += sample
        
        # Apply master volume and convert to 16-bit
        left = left * (self.master_volume_left / 7.0) * 0.25
        right = right * (self.master_volume_right / 7.0) * 0.25
        
        # Convert to int16
        left = int(np.clip(left * 8192, -32768, 32767))
        right = int(np.clip(right * 8192, -32768, 32767))
        
        return (left, right)
    
    def generate_square_wave(self, channel, ch_num):
        """Generate square wave sample"""
        # Clock frequency timer
        freq = channel['frequency']
        if freq == 0:
            return 0.0
        
        # Update duty position based on frequency
        freq_hz = 131072.0 / (2048 - freq)
        phase_inc = (freq_hz * 8) / self.sample_rate
        
        channel['duty_position'] = (channel['duty_position'] + phase_inc) % 8
        
        # Get current duty output
        duty_pattern = self.duty_patterns[channel['duty']]
        output = duty_pattern[int(channel['duty_position'])]
        
        # Apply volume
        volume = channel['envelope_volume'] / 15.0
        
        return (output * 2 - 1) * volume
    
    def generate_wave(self):
        """Generate wave channel sample"""
        freq = self.ch3['frequency']
        if freq == 0:
            return 0.0
        
        # Update sample position
        freq_hz = 65536.0 / (2048 - freq)
        phase_inc = (freq_hz * 32) / self.sample_rate
        
        self.ch3['sample_position'] = (self.ch3['sample_position'] + phase_inc) % 32
        
        # Get sample from wave RAM
        sample_index = int(self.ch3['sample_position'])
        sample = self.wave_ram[sample_index]
        
        # Apply volume shift
        volume_shifts = [4, 0, 1, 2]
        shift = volume_shifts[self.ch3['volume_code']]
        sample = (sample >> shift) / 15.0
        
        return sample * 2 - 1
    
    def generate_noise(self):
        """Generate noise channel sample"""
        # Clock LFSR
        divisors = [8, 16, 32, 48, 64, 80, 96, 112]
        divisor = divisors[self.ch4['divisor_code']]
        freq = divisor << self.ch4['clock_shift']
        
        self.ch4['frequency_timer'] += 1
        if self.ch4['frequency_timer'] >= freq:
            self.ch4['frequency_timer'] = 0
            
            # Clock LFSR
            bit = (self.ch4['lfsr'] & 1) ^ ((self.ch4['lfsr'] >> 1) & 1)
            self.ch4['lfsr'] = (self.ch4['lfsr'] >> 1) | (bit << 14)
            
            if self.ch4['width_mode'] == 1:
                self.ch4['lfsr'] = (self.ch4['lfsr'] & ~0x40) | (bit << 6)
        
        # Output
        output = 1 if (self.ch4['lfsr'] & 1) == 0 else -1
        volume = self.ch4['envelope_volume'] / 15.0
        
        return output * volume
    
    def play_buffer(self):
        """Play audio buffer (non-blocking)"""
        if len(self.audio_buffer) < self.buffer_size:
            return
        
        try:
            # Check if pygame.mixer has available channels
            if pygame.mixer.get_busy() and pygame.mixer.get_num_channels() >= 8:
                # Too many sounds playing, skip this buffer
                self.audio_buffer.clear()
                return
            
            # Convert to numpy array
            samples = []
            for _ in range(min(self.buffer_size, len(self.audio_buffer))):
                if self.audio_buffer:
                    samples.append(self.audio_buffer.popleft())
                else:
                    samples.append((0, 0))
            
            if not samples:
                return
            
            audio_array = np.array(samples, dtype=np.int16)
            
            # Create and play sound (non-blocking)
            sound = pygame.sndarray.make_sound(audio_array)
            channel = pygame.mixer.find_channel(True)  # Force find channel
            if channel:
                channel.play(sound)
        except Exception as e:
            # Clear buffer on error to prevent buildup
            self.audio_buffer.clear()
    
    def write_register(self, address, value):
        """Write to audio register"""
        if not self.enabled:
            return
        
        # Channel 1 Registers
        if address == 0xFF10:  # NR10 - Sweep
            self.ch1['sweep_period'] = (value >> 4) & 0x07
            self.ch1['sweep_direction'] = (value >> 3) & 0x01
            self.ch1['sweep_shift'] = value & 0x07
        
        elif address == 0xFF11:  # NR11 - Length/Duty
            self.ch1['duty'] = (value >> 6) & 0x03
            self.ch1['length_counter'] = 64 - (value & 0x3F)
        
        elif address == 0xFF12:  # NR12 - Volume Envelope
            self.ch1['volume'] = (value >> 4) & 0x0F
            self.ch1['envelope_direction'] = (value >> 3) & 0x01
            self.ch1['envelope_period'] = value & 0x07
            self.ch1['dac_enabled'] = (value & 0xF8) != 0
        
        elif address == 0xFF13:  # NR13 - Frequency Low
            self.ch1['frequency'] = (self.ch1['frequency'] & 0x0700) | value
        
        elif address == 0xFF14:  # NR14 - Frequency High/Control
            self.ch1['frequency'] = (self.ch1['frequency'] & 0x00FF) | ((value & 0x07) << 8)
            self.ch1['length_enabled'] = (value & 0x40) != 0
            
            if value & 0x80:  # Trigger
                self.trigger_channel1()
        
        # Channel 2 Registers
        elif address == 0xFF16:  # NR21
            self.ch2['duty'] = (value >> 6) & 0x03
            self.ch2['length_counter'] = 64 - (value & 0x3F)
        
        elif address == 0xFF17:  # NR22
            self.ch2['volume'] = (value >> 4) & 0x0F
            self.ch2['envelope_direction'] = (value >> 3) & 0x01
            self.ch2['envelope_period'] = value & 0x07
            self.ch2['dac_enabled'] = (value & 0xF8) != 0
        
        elif address == 0xFF18:  # NR23
            self.ch2['frequency'] = (self.ch2['frequency'] & 0x0700) | value
        
        elif address == 0xFF19:  # NR24
            self.ch2['frequency'] = (self.ch2['frequency'] & 0x00FF) | ((value & 0x07) << 8)
            self.ch2['length_enabled'] = (value & 0x40) != 0
            
            if value & 0x80:  # Trigger
                self.trigger_channel2()
        
        # Channel 3 Registers
        elif address == 0xFF1A:  # NR30
            self.ch3['dac_enabled'] = (value & 0x80) != 0
            if not self.ch3['dac_enabled']:
                self.ch3['enabled'] = False
        
        elif address == 0xFF1B:  # NR31
            self.ch3['length_counter'] = 256 - value
        
        elif address == 0xFF1C:  # NR32
            self.ch3['volume_code'] = (value >> 5) & 0x03
        
        elif address == 0xFF1D:  # NR33
            self.ch3['frequency'] = (self.ch3['frequency'] & 0x0700) | value
        
        elif address == 0xFF1E:  # NR34
            self.ch3['frequency'] = (self.ch3['frequency'] & 0x00FF) | ((value & 0x07) << 8)
            self.ch3['length_enabled'] = (value & 0x40) != 0
            
            if value & 0x80:  # Trigger
                self.trigger_channel3()
        
        # Wave RAM
        elif 0xFF30 <= address <= 0xFF3F:
            index = (address - 0xFF30) * 2
            self.wave_ram[index] = (value >> 4) & 0x0F
            self.wave_ram[index + 1] = value & 0x0F
        
        # Channel 4 Registers
        elif address == 0xFF20:  # NR41
            self.ch4['length_counter'] = 64 - (value & 0x3F)
        
        elif address == 0xFF21:  # NR42
            self.ch4['volume'] = (value >> 4) & 0x0F
            self.ch4['envelope_direction'] = (value >> 3) & 0x01
            self.ch4['envelope_period'] = value & 0x07
            self.ch4['dac_enabled'] = (value & 0xF8) != 0
        
        elif address == 0xFF22:  # NR43
            self.ch4['clock_shift'] = (value >> 4) & 0x0F
            self.ch4['width_mode'] = (value >> 3) & 0x01
            self.ch4['divisor_code'] = value & 0x07
        
        elif address == 0xFF23:  # NR44
            self.ch4['length_enabled'] = (value & 0x40) != 0
            
            if value & 0x80:  # Trigger
                self.trigger_channel4()
        
        # Master Control
        elif address == 0xFF24:  # NR50
            self.master_volume_right = value & 0x07
            self.master_volume_left = (value >> 4) & 0x07
        
        elif address == 0xFF25:  # NR51 - Panning
            self.ch1_right = (value & 0x01) != 0
            self.ch2_right = (value & 0x02) != 0
            self.ch3_right = (value & 0x04) != 0
            self.ch4_right = (value & 0x08) != 0
            self.ch1_left = (value & 0x10) != 0
            self.ch2_left = (value & 0x20) != 0
            self.ch3_left = (value & 0x40) != 0
            self.ch4_left = (value & 0x80) != 0
        
        elif address == 0xFF26:  # NR52
            was_enabled = self.sound_enabled
            self.sound_enabled = (value & 0x80) != 0
            
            if was_enabled and not self.sound_enabled:
                # Power off - clear all registers
                self.reset()
    
    def trigger_channel1(self):
        """Trigger Channel 1"""
        if self.ch1['dac_enabled']:
            self.ch1['enabled'] = True
        self.ch1['envelope_volume'] = self.ch1['volume']
        self.ch1['envelope_counter'] = 0
        self.ch1['duty_position'] = 0
        self.ch1['frequency_shadow'] = self.ch1['frequency']
        
        if self.ch1['length_counter'] == 0:
            self.ch1['length_counter'] = 64
    
    def trigger_channel2(self):
        """Trigger Channel 2"""
        if self.ch2['dac_enabled']:
            self.ch2['enabled'] = True
        self.ch2['envelope_volume'] = self.ch2['volume']
        self.ch2['envelope_counter'] = 0
        self.ch2['duty_position'] = 0
        
        if self.ch2['length_counter'] == 0:
            self.ch2['length_counter'] = 64
    
    def trigger_channel3(self):
        """Trigger Channel 3"""
        if self.ch3['dac_enabled']:
            self.ch3['enabled'] = True
        self.ch3['sample_position'] = 0
        
        if self.ch3['length_counter'] == 0:
            self.ch3['length_counter'] = 256
    
    def trigger_channel4(self):
        """Trigger Channel 4"""
        if self.ch4['dac_enabled']:
            self.ch4['enabled'] = True
        self.ch4['envelope_volume'] = self.ch4['volume']
        self.ch4['envelope_counter'] = 0
        self.ch4['lfsr'] = 0x7FFF
        
        if self.ch4['length_counter'] == 0:
            self.ch4['length_counter'] = 64
    
    def read_register(self, address):
        """Read from audio register"""
        if address == 0xFF26:  # NR52
            status = 0x70  # Unused bits
            if self.sound_enabled:
                status |= 0x80
            if self.ch1['enabled']:
                status |= 0x01
            if self.ch2['enabled']:
                status |= 0x02
            if self.ch3['enabled']:
                status |= 0x04
            if self.ch4['enabled']:
                status |= 0x08
            return status
        
        return 0xFF
    
    def reset(self):
        """Reset APU"""
        self.ch1['enabled'] = False
        self.ch2['enabled'] = False
        self.ch3['enabled'] = False
        self.ch4['enabled'] = False
        self.audio_buffer.clear()