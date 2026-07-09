from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class Reading:
    """A single sweep sample: the servo angle and the distance measured there."""

    angle: int
    distance: float
    timestamp: float


def sweep_angles() -> Iterator[int]:
    """Reproduces the servo angle sequence from ``my_custom_radar.ino``.

    The sketch never transmits the servo angle, only the distance reading, so
    the angle has to be reconstructed on the Python side. The sketch sweeps
    with two ``for`` loops: 0 up to 180, then 180 down to 0, forever - one
    reading per degree, in that exact order (including the repeated reading
    at each end where the sweep reverses). This generator replays that same
    sequence so each distance sample received over serial can be paired with
    the angle the servo was actually at when it was taken.
    """
    sweep_up = range(0, 181)
    sweep_down = range(180, -1, -1)
    yield from itertools.cycle(itertools.chain(sweep_up, sweep_down))
