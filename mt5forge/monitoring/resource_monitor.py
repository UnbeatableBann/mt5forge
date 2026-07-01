"""CPU and memory monitoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ResourceSnapshot:
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    healthy: bool


class ResourceMonitor:
    """Measure process CPU and memory utilization."""

    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0) -> None:
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def snapshot(self) -> ResourceSnapshot:
        try:
            import psutil

            process = psutil.Process()
            cpu = float(psutil.cpu_percent(interval=0.0))
            memory = float(psutil.virtual_memory().percent)
            rss = float(process.memory_info().rss / (1024 * 1024))
        except Exception:
            cpu = 0.0
            memory = 0.0
            rss = 0.0
        healthy = cpu < self.cpu_threshold and memory < self.memory_threshold
        return ResourceSnapshot(cpu_percent=cpu, memory_percent=memory, memory_rss_mb=rss, healthy=healthy)
