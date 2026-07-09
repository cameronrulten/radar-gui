from __future__ import annotations

import math
import random
import threading
import time
from queue import Queue

from .models import Reading, sweep_angles


class DemoSource:
    """Generates synthetic sweep readings so the GUI can be tried without hardware.

    Mimics the timing and shape of real sensor data: a near-constant "open
    space" distance with a bit of sensor noise, plus a slow-drifting
    obstacle that shows up as a cluster of close blips as the beam crosses it.
    """

    def __init__(self, step_delay: float = 0.02, max_range: float = 300.0) -> None:
        self._step_delay = step_delay
        self._max_range = max_range
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self, queue: "Queue[Reading]") -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, args=(queue,), name="radar-demo-source", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _run(self, queue: "Queue[Reading]") -> None:
        angles = sweep_angles()
        obstacle_angle = random.uniform(40, 140)
        obstacle_width = random.uniform(8, 20)
        while not self._stop_event.is_set():
            angle = next(angles)
            baseline = self._max_range * 0.85
            wobble = 15 * math.sin(time.monotonic() * 0.5)
            distance = baseline + wobble

            if abs(angle - obstacle_angle) < obstacle_width:
                closeness = 1 - abs(angle - obstacle_angle) / obstacle_width
                distance = max(20.0, baseline - closeness * (baseline - 30))

            distance += random.uniform(-2, 2)
            queue.put(
                Reading(angle=angle, distance=max(2.0, distance), timestamp=time.monotonic())
            )

            if random.random() < 0.003:
                obstacle_angle = random.uniform(20, 160)
                obstacle_width = random.uniform(8, 20)

            time.sleep(self._step_delay)
