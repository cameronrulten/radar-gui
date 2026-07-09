from __future__ import annotations

import logging
import re
import threading
import time
from queue import Queue

import serial

from .models import Reading, sweep_angles

logger = logging.getLogger(__name__)

# Matches the sketch's `Serial.print(distance); Serial.println("cm");`
# output, e.g. b"23cm\r\n". Tolerant of stray whitespace/case.
_DISTANCE_RE = re.compile(rb"(-?\d+)\s*cm", re.IGNORECASE)


class SerialSource:
    """Reads distance samples from my_custom_radar.ino over a serial port.

    The Arduino sketch only ever prints the distance (e.g. "23cm"), one line
    per servo step - it does not send the angle. This class reconstructs the
    angle locally by walking the same sweep sequence the sketch's servo loop
    follows (see :func:`radar_gui.models.sweep_angles`), so every line read
    is paired with the angle the sensor was actually pointing at.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self, queue: "Queue[Reading]") -> None:
        self._serial = serial.Serial(self._port, self._baudrate, timeout=self._timeout)
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, args=(queue,), name="radar-serial-reader", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._serial is not None and self._serial.is_open:
            self._serial.close()

    def _run(self, queue: "Queue[Reading]") -> None:
        assert self._serial is not None
        angles = sweep_angles()
        while not self._stop_event.is_set():
            try:
                line = self._serial.readline()
            except serial.SerialException:
                logger.exception("Serial connection to %s lost", self._port)
                return
            if not line:
                continue  # read timed out with no data - keep polling
            match = _DISTANCE_RE.search(line)
            if match is None:
                continue
            distance = float(match.group(1))
            angle = next(angles)
            queue.put(Reading(angle=angle, distance=distance, timestamp=time.monotonic()))
