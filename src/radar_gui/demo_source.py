from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from queue import Queue

from .models import Reading, sweep_angles

_RESHUFFLE_PROBABILITY = 0.0015  # per step - roughly every couple of sweeps


@dataclass
class _Object:
    angle: float
    distance: float
    width: float


class DemoSource:
    """Generates synthetic sweep readings so the GUI can be tried without hardware.

    Mimics real sensor data: a near-max-range "open space" baseline, plus a
    handful of simulated objects scattered at random angles *and* random
    distances (near to far), so both close and distant detections - and the
    full range of proximity-warning zones - can be exercised without hardware.
    """

    def __init__(self, step_delay: float = 0.02, max_range: float = 300.0) -> None:
        self._step_delay = step_delay
        self._max_range = max_range
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._scanning_event = threading.Event()  # unset -> starts stopped, like the sketch

    def start(self, queue: "Queue[Reading]") -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, args=(queue,), name="radar-demo-source", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._scanning_event.set()  # wake the thread if it's idling, so it can exit
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def send_command(self, command: str) -> None:
        """Mirrors SerialSource.send_command so the GUI's Start/Stop button works in --demo too."""
        if command == "START":
            self._scanning_event.set()
        elif command == "STOP":
            self._scanning_event.clear()

    def _spawn_objects(self) -> list[_Object]:
        return [
            _Object(
                angle=random.uniform(5, 175),
                distance=random.uniform(self._max_range * 0.05, self._max_range * 0.9),
                width=random.uniform(6, 16),
            )
            for _ in range(random.randint(2, 4))
        ]

    def _run(self, queue: "Queue[Reading]") -> None:
        angles = sweep_angles()
        objects = self._spawn_objects()
        baseline = self._max_range * 0.95

        while not self._stop_event.is_set():
            if not self._scanning_event.wait(timeout=0.1):
                continue
            angle = next(angles)
            distance = baseline

            nearest: float | None = None
            for obj in objects:
                delta = abs(angle - obj.angle)
                if delta >= obj.width:
                    continue
                closeness = 1 - delta / obj.width
                # blends from the object's true distance at the centre of its
                # footprint out to the open-space baseline at its edges
                candidate = obj.distance + (baseline - obj.distance) * (1 - closeness)
                if nearest is None or candidate < nearest:
                    nearest = candidate
            if nearest is not None:
                distance = nearest

            distance += random.uniform(-2, 2)
            queue.put(
                Reading(angle=angle, distance=max(2.0, distance), timestamp=time.monotonic())
            )

            if random.random() < _RESHUFFLE_PROBABILITY:
                objects = self._spawn_objects()

            time.sleep(self._step_delay)
