from __future__ import annotations

import array
import math
import time

import pygame

_SAMPLE_RATE = 44100

# (upper bound as a fraction of warn_range, beep interval seconds, frequency Hz)
# Ordered tightest-zone-first so _zone_for_distance finds the closest match.
_ZONE_FRACTIONS = (
    (0.1, 0.08, 1400),
    (0.3, 0.18, 1100),
    (0.6, 0.35, 900),
    (1.0, 0.6, 700),
)


def _zone_for_distance(distance: float, warn_range: float) -> int | None:
    """Picks the warning zone for a distance, or None if no warning is needed."""
    if distance < 0 or distance >= warn_range:
        return None
    for index, (fraction, _interval, _frequency) in enumerate(_ZONE_FRACTIONS):
        if distance < fraction * warn_range:
            return index
    return len(_ZONE_FRACTIONS) - 1


def _make_beep(frequency: float, duration: float) -> pygame.mixer.Sound:
    """Synthesizes a short sine-wave beep with a fast fade in/out to avoid clicks."""
    n_samples = max(1, int(_SAMPLE_RATE * duration))
    fade_samples = max(1, int(_SAMPLE_RATE * 0.005))
    amplitude = int(32767 * 0.8)
    samples = array.array("h")
    for i in range(n_samples):
        value = math.sin(2 * math.pi * frequency * i / _SAMPLE_RATE)
        if i < fade_samples:
            value *= i / fade_samples
        elif i > n_samples - fade_samples:
            value *= (n_samples - i) / fade_samples
        sample = int(value * amplitude)
        samples.append(sample)
        samples.append(sample)  # stereo
    return pygame.mixer.Sound(buffer=samples.tobytes())


class ProximityWarning:
    """Plays a parking-sensor-style warning beep through the computer's speakers.

    Tempo and pitch step up as an object gets closer, replacing the
    instrument's own active buzzer (which could only vary beep rate via a
    blocking delay(), and so tended to sound like it was beeping constantly).
    Sounds are synthesized lazily on first use and cached per zone.
    """

    def __init__(self, warn_range: float, volume: float = 0.5) -> None:
        self._warn_range = warn_range
        self._volume = volume
        self._sounds: list[pygame.mixer.Sound | None] = [None] * len(_ZONE_FRACTIONS)
        self._last_beep_at = 0.0

    def _sound_for_zone(self, index: int) -> pygame.mixer.Sound:
        sound = self._sounds[index]
        if sound is None:
            _, interval, frequency = _ZONE_FRACTIONS[index]
            sound = _make_beep(frequency, min(interval * 0.6, 0.12))
            sound.set_volume(self._volume)
            self._sounds[index] = sound
        return sound

    def update(self, distance: float, scanning: bool) -> None:
        if not scanning:
            return
        zone = _zone_for_distance(distance, self._warn_range)
        if zone is None:
            return
        now = time.monotonic()
        _, interval, _ = _ZONE_FRACTIONS[zone]
        if now - self._last_beep_at >= interval:
            self._sound_for_zone(zone).play()
            self._last_beep_at = now
