#!/usr/bin/env python3
"""
🐉 NECROZMAv2 - BATCH RUNNER

Batch processing with subprocess isolation.
"Memory cleanup between batches for stable long runs"

Features:
- Subprocess isolation (memory cleanup automatic)
- Progress tracking with RAM usage
- Failed batch recovery
- Result merging
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import pandas as pd
import psutil
import gc


class BatchRunner:
    """
    Orchestrator for batch processing strategy backtests.
    
    Runs each batch in isolated subprocess to prevent memory leaks.
    
    Usage:
        runner = BatchRunner(batch_size=200)
        results = runner.run_all_batches(strategies, universe, labels)
    """
    
    def __init__(self, batch_size: int = 200, output_dir: str = "results"):
        """
        Initialize batch runner.
        
        Args:
            batch_size: Number of strategies per batch (default: 200)
            output_dir: Directory to save batch results
        """
        self.batch_size = batch_size
        self.output_dir = Path(output_dir) / "batch_results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.total_strategies = 0
        self.num_batches = 0
        self.failed_batches = []
        self.completed_batches = []
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def get_system_memory(self) -> Dict[str, float]:
        """Get system memory stats."""
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / 1024 / 1024 / 1024,
            'available_gb': mem.available / 1024 / 1024 / 1024,
            'used_pct': mem.percent
        }
    
    def calculate_batches(self, total_items: int) -> List[Tuple[int, int]]:
        """
        Calculate batch ranges.
        
        Args:
            total_items: Total number of items to process
            
        Returns:
            List of (start_idx, end_idx) tuples
        """
        batches = []
        for i in range(0, total_items, self.batch_size):
            start_idx = i
            end_idx = min(i + self.batch_size, total_items)
            batches.append((start_idx, end_idx))
        
        self.num_batches = len(batches)
        return batches
    
    def run_batch_subprocess(self, batch_idx: int, start_idx: int, end_idx: int,
                             script_path: str, args: List[str]) -> Tuple[bool, float, str]:
        """
        Run a single batch in subprocess.
        
        Args:
            batch_idx: Batch index
            start_idx: Start strategy index
            end_idx: End strategy index
            script_path: Path to batch processing script
            args: Additional arguments
            
        Returns:
            Tuple of (success, duration, output_file)
        """
        start_time = time.time()
        mem_before = self.get_memory_usage()
        
        print(f"\n{'─'*60}")
        print(f"📦 BATCH {batch_idx + 1}/{self.num_batches}")
        print(f"   Strategies: {start_idx} - {end_idx - 1}")
        print(f"   RAM before: {mem_before:.0f} MB")
        
        # Build command
        cmd = [
            sys.executable, script_path,
            '--start', str(start_idx),
            '--end', str(end_idx),
            '--batch-idx', str(batch_idx),
            '--output-dir', str(self.output_dir),
            *args
        ]
        
        try:
            # Run subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout per batch
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                output_file = self.output_dir / f"batch_{batch_idx:04d}.parquet"
                print(f"   ✅ Completed in {duration:.1f}s")
                self.completed_batches.append(batch_idx)
                return True, duration, str(output_file)
            else:
                print(f"   ❌ Failed: {result.stderr[:200]}")
                self.failed_batches.append(batch_idx)
                return False, duration, ""
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout after 1 hour")
            self.failed_batches.append(batch_idx)
            return False, 3600, ""
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.failed_batches.append(batch_idx)
            return False, 0, ""
    
    def run_batch_inprocess(self, batch_idx: int, strategies: List, 
                            universe: pd.DataFrame, labels: pd.DataFrame,
                            backtest_func, risk_levels: List[float]) -> pd.DataFrame:
        """
        Run a single batch in-process with memory cleanup.
        
        Args:
            batch_idx: Batch index
            strategies: List of strategies to test
            universe: Universe DataFrame
            labels: Labels DataFrame
            backtest_func: Function to run backtest
            risk_levels: Risk levels to test
            
        Returns:
            DataFrame with batch results
        """
        start_time = time.time()
        mem_before = self.get_memory_usage()
        
        print(f"\n{'─'*60}")
        print(f"📦 BATCH {batch_idx + 1}/{self.num_batches}")
        print(f"   Strategies: {len(strategies)}")
        print(f"   RAM before: {mem_before:.0f} MB")
        
        try:
            # Run backtest for this batch
            results = backtest_func(strategies, universe, labels, risk_levels)
            
            # Force garbage collection
            gc.collect()
            
            duration = time.time() - start_time
            mem_after = self.get_memory_usage()
            
            print(f"   ✅ Completed in {duration:.1f}s")
            print(f"   RAM after: {mem_after:.0f} MB (Δ {mem_after - mem_before:+.0f} MB)")
            
            self.completed_batches.append(batch_idx)
            return results
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.failed_batches.append(batch_idx)
            return pd.DataFrame()
    
    def merge_results(self) -> pd.DataFrame:
        """
        Merge all batch result files.
        
        Returns:
            Combined DataFrame
        """
        print(f"\n📊 Merging {len(self.completed_batches)} batch results...")
        
        dfs = []
        for batch_idx in sorted(self.completed_batches):
            batch_file = self.output_dir / f"batch_{batch_idx:04d}.parquet"
            if batch_file.exists():
                df = pd.read_parquet(batch_file)
                dfs.append(df)
        
        if not dfs:
            print("   ⚠️ No batch results found")
            return pd.DataFrame()
        
        combined = pd.concat(dfs, ignore_index=True)
        print(f"   ✅ Merged {len(combined)} results from {len(dfs)} batches")
        
        return combined
    
    def cleanup_batch_files(self):
        """Delete intermediate batch files."""
        for batch_file in self.output_dir.glob("batch_*.parquet"):
            batch_file.unlink()
        print(f"🗑️ Cleaned up batch files")
    
    def print_summary(self, total_duration: float):
        """Print batch processing summary."""
        print(f"\n{'='*60}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"   Total batches: {self.num_batches}")
        print(f"   Completed: {len(self.completed_batches)}")
        print(f"   Failed: {len(self.failed_batches)}")
        print(f"   Total duration: {total_duration/60:.1f} min")
        
        if self.failed_batches:
            print(f"   ⚠️ Failed batches: {self.failed_batches}")
        
        mem = self.get_system_memory()
        print(f"   System RAM: {mem['used_pct']:.1f}% used")
