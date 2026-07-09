from __future__ import annotations

import logging
import re
import threading
import time
from queue import Queue
from typing import Literal

import serial

from .models import Reading

logger = logging.getLogger(__name__)

# The sketch prints two lines per sweep step, e.g. "90 degrees" then "23 cm".
_ANGLE_RE = re.compile(rb"(-?\d+)\s*degrees", re.IGNORECASE)
_DISTANCE_RE = re.compile(rb"(-?\d+)\s*cm", re.IGNORECASE)


def _parse_line(line: bytes) -> tuple[Literal["angle", "distance"], int] | None:
    """Parses one line of the sketch's serial output into a (kind, value) pair."""
    match = _ANGLE_RE.search(line)
    if match is not None:
        return "angle", int(match.group(1))
    match = _DISTANCE_RE.search(line)
    if match is not None:
        return "distance", int(match.group(1))
    return None


class SerialSource:
    """Reads angle/distance samples from my_custom_radar.ino over a serial port.

    The sketch prints its angle and distance as two separate lines per sweep
    step. This class pairs each distance reading with the angle line that
    preceded it to build a complete :class:`~radar_gui.models.Reading`.
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

    def send_command(self, command: str) -> None:
        """Sends a "START" or "STOP" command, matching handleSerialCommand() in the sketch."""
        if self._serial is not None and self._serial.is_open:
            self._serial.write(f"{command}\n".encode("ascii"))

    def _run(self, queue: "Queue[Reading]") -> None:
        assert self._serial is not None
        pending_angle: int | None = None
        while not self._stop_event.is_set():
            try:
                line = self._serial.readline()
            except serial.SerialException:
                logger.exception("Serial connection to %s lost", self._port)
                return
            if not line:
                continue  # read timed out with no data - keep polling

            parsed = _parse_line(line)
            if parsed is None:
                continue
            kind, value = parsed

            if kind == "angle":
                pending_angle = value
                continue

            # kind == "distance": only emit a Reading once we know the angle
            # it belongs to. If the two ever get out of sync (e.g. the
            # connection dropped mid-line), drop the orphaned distance and
            # wait for the next angle line to resynchronise.
            if pending_angle is None:
                continue
            queue.put(
                Reading(angle=pending_angle, distance=float(value), timestamp=time.monotonic())
            )
            pending_angle = None
