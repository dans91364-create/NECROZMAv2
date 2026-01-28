#!/usr/bin/env python3
"""
🐉 NECROZMAv2 - THERMAL MANAGER

Cooling break system for VM-safe operation.
"Even Necrozma needs to cool down"

Features:
- CPU monitoring
- Automatic cooling breaks
- Configurable intervals
- Early exit when cool
"""

import time
import psutil
from typing import Optional, Dict


class ThermalManager:
    """
    Manage cooling breaks for stable long-running jobs.
    
    Prevents thermal throttling on cloud VMs (Vast.ai, Lambda, etc.)
    
    Usage:
        thermal = ThermalManager()
        
        for i, batch in enumerate(batches):
            process_batch(batch)
            thermal.check_and_cool(batch_idx=i)
    """
    
    def __init__(
        self,
        batch_interval: int = 5,
        batch_cool_duration: int = 30,
        universe_interval: int = 3,
        universe_cool_duration: int = 60,
        cpu_threshold: float = 80.0,
        cool_target: float = 40.0
    ):
        """
        Initialize ThermalManager.
        
        Args:
            batch_interval: Cool every N batches
            batch_cool_duration: Cooling duration after batches (seconds)
            universe_interval: Cool every N universes
            universe_cool_duration: Cooling duration after universes (seconds)
            cpu_threshold: CPU % to trigger emergency cooling
            cool_target: Target CPU % to resume early
        """
        self.batch_interval = batch_interval
        self.batch_cool_duration = batch_cool_duration
        self.universe_interval = universe_interval
        self.universe_cool_duration = universe_cool_duration
        self.cpu_threshold = cpu_threshold
        self.cool_target = cool_target
        
        # Tracking
        self.total_cooling_time = 0
        self.cooling_breaks = 0
        self.batches_processed = 0
        self.universes_processed = 0
    
    def get_cpu_percent(self, interval: float = 0.5) -> float:
        """Get current CPU usage."""
        return psutil.cpu_percent(interval=interval)
    
    def get_system_stats(self) -> Dict:
        """Get system stats."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'load_avg': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        }
    
    def should_cool_batch(self, batch_idx: int) -> bool:
        """Check if cooling needed after batch."""
        if self.batch_interval <= 0:
            return False
        return batch_idx > 0 and (batch_idx + 1) % self.batch_interval == 0
    
    def should_cool_universe(self, universe_idx: int) -> bool:
        """Check if cooling needed after universe."""
        if self.universe_interval <= 0:
            return False
        return universe_idx > 0 and (universe_idx + 1) % self.universe_interval == 0
    
    def should_emergency_cool(self) -> bool:
        """Check if emergency cooling needed (CPU too high)."""
        cpu = self.get_cpu_percent(interval=0.1)
        return cpu > self.cpu_threshold
    
    def cooling_break(self, duration: int, reason: str = "scheduled"):
        """
        Execute cooling break with countdown.
        
        Args:
            duration: Break duration in seconds
            reason: Reason for cooling break
        """
        print(f"\n❄️  COOLING BREAK - {reason}")
        print(f"   Duration: {duration}s (early exit if CPU < {self.cool_target}%)")
        print("─" * 50)
        
        start_time = time.time()
        elapsed = 0
        
        while elapsed < duration:
            remaining = int(duration - elapsed)
            cpu = self.get_cpu_percent(interval=1)
            
            # Show countdown
            print(f"   ⏱️  {remaining:3d}s remaining | CPU: {cpu:5.1f}%", end="\r")
            
            # Early exit if CPU is cool enough
            if cpu < self.cool_target and elapsed > 5:
                print(f"\n   ✅ CPU cooled to {cpu:.1f}%, resuming early")
                break
            
            elapsed = time.time() - start_time
        
        actual_duration = time.time() - start_time
        self.total_cooling_time += actual_duration
        self.cooling_breaks += 1
        
        print(f"\n   🔥 Cooling complete ({actual_duration:.0f}s)")
    
    def check_and_cool_batch(self, batch_idx: int):
        """Check and cool after batch if needed."""
        self.batches_processed = batch_idx + 1
        
        if self.should_emergency_cool():
            self.cooling_break(self.batch_cool_duration * 2, "EMERGENCY - CPU too high")
        elif self.should_cool_batch(batch_idx):
            self.cooling_break(self.batch_cool_duration, f"after batch {batch_idx + 1}")
    
    def check_and_cool_universe(self, universe_idx: int):
        """Check and cool after universe if needed."""
        self.universes_processed = universe_idx + 1
        
        if self.should_emergency_cool():
            self.cooling_break(self.universe_cool_duration * 2, "EMERGENCY - CPU too high")
        elif self.should_cool_universe(universe_idx):
            self.cooling_break(self.universe_cool_duration, f"after universe {universe_idx + 1}")
    
    def print_summary(self):
        """Print thermal management summary."""
        print(f"\n🌡️ THERMAL SUMMARY")
        print(f"   Cooling breaks: {self.cooling_breaks}")
        print(f"   Total cooling time: {self.total_cooling_time/60:.1f} min")
        print(f"   Batches processed: {self.batches_processed}")
        print(f"   Universes processed: {self.universes_processed}")
