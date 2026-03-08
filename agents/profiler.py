"""
profiler.py — Performance profiling for Kitty Collab Board

Profiles agent startup time, task claiming latency, memory usage.
"""

import time
import psutil
import os
from pathlib import Path
from typing import Dict, Tuple


class PerformanceProfiler:
    """Profiles performance metrics for agents."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.metrics = {}
        self.process = psutil.Process(os.getpid())

    def profile_startup(self, func, *args, **kwargs) -> Tuple[float, any]:
        """Profile function startup time and return (elapsed_seconds, result)."""
        start_mem = self.process.memory_info().rss / (1024 * 1024)  # MB
        start_time = time.time()

        result = func(*args, **kwargs)

        elapsed = time.time() - start_time
        end_mem = self.process.memory_info().rss / (1024 * 1024)
        mem_delta = end_mem - start_mem

        self.metrics['startup_time'] = elapsed
        self.metrics['startup_memory_delta'] = mem_delta
        self.metrics['peak_memory'] = self.process.memory_info().rss / (1024 * 1024)

        return elapsed, result

    def profile_task_claim(self, func, *args, **kwargs) -> Tuple[float, any]:
        """Profile task claiming latency."""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        self.metrics['claim_latency'] = elapsed
        return elapsed, result

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)

    def report(self) -> Dict:
        """Return performance metrics."""
        return {
            'agent': self.agent_name,
            'startup_time_seconds': self.metrics.get('startup_time', 0),
            'claim_latency_ms': self.metrics.get('claim_latency', 0) * 1000,
            'memory_usage_mb': self.get_memory_usage(),
            'peak_memory_mb': self.metrics.get('peak_memory', 0),
            'memory_delta_mb': self.metrics.get('startup_memory_delta', 0),
        }


if __name__ == "__main__":
    profiler = PerformanceProfiler("test_agent")

    def test_func():
        """Simulated agent startup."""
        time.sleep(0.1)
        return "done"

    elapsed, result = profiler.profile_startup(test_func)
    print(f"Startup time: {elapsed:.3f}s")
    print(f"Report: {profiler.report()}")
